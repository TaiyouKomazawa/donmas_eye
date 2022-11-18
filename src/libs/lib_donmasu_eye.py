'''
ドンマス-アイ ライブラリ

ドンマス-アイの動作に必要なクラスを定義してある。
使いたいときは本スクリプトをimportする。

'''

import os.path
import time

import cv2
import numpy as np

import random
import time
import copy

import socket
import pickle

import threading

#眼(瞳)のアニメーションを定義するクラス
class Eye:

    def __init__(self, bg, pupil_paths, min_range=[0,0], max_range=[0,0], th=0.0):
        '''
        クラスコンストラクタ

        Parameters
        ----------
        bg          : ndarray
            使用する背景(白目)画像

        pupil_paths       : [string, ...]
            瞳の画像(またはgif)のパスのリスト(モード順のリスト)

        min_range   : [float, float]
            原点(y,x)=(0.0, 0.0)のオフセット画素値[pixel]

        max_range   : [float, float]
            最大値(y,x)=(1.0, 1.0)のオフセット画素値[pixel]

        th  : float
            眼の固定角度(度)
        '''
        self.bg_ = bg
        
        self.pupils_ = []
        self.pupils_gif_mode = []
        for pupil_path in pupil_paths:
            root, ext = os.path.splitext(pupil_path)
            if ext == '.gif':
                self.pupils_.append(cv2.VideoCapture(pupil_path))
                self.pupils_gif_mode.append(True)
            else:
                self.pupils_.append(cv2.imread(pupil_path, cv2.IMREAD_COLOR))
                self.pupils_gif_mode.append(False)

        self.bg_r_ = self.bg_.shape[:2]

        self.min_r_ = min_range
        self.max_r_ = max_range

        self.p_org_px = (0.5, 0.5)

        self.cos_th = np.cos(th/180*np.pi)
        self.sin_th = np.sin(th/180*np.pi)

        self.change_mode(0)

    def change_mode(self, mode):
        '''
        瞳のタイプを変更する関数

        Parameters
        ----------
        mode    : int
            瞳の画像の種類(0から読み込んだ画像順で指定可能)

        Returns
        -------
        None
        '''
        if mode < len(self.pupils_):
            self.pupil_ = self.pupils_[mode]
            self.pupil_gif_mode = self.pupils_gif_mode[mode]

            if self.pupil_gif_mode:
                self.pupil_r_ = [int(self.pupil_.get(cv2.CAP_PROP_FRAME_HEIGHT)), 
                                int(self.pupil_.get(cv2.CAP_PROP_FRAME_WIDTH))]
                self.pupil_.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.last_f_tim_ = time.time()
            else:
                self.pupil_r_ = self.pupil_.shape[:2]

            self.min_mr_ = [self.min_r_[0], self.min_r_[1]]
            self.min_mr_[0] += self.pupil_r_[0] / 2
            self.min_mr_[1] += self.pupil_r_[1] / 2
            self.max_mr_ = [self.max_r_[0], self.max_r_[1]]
            self.max_mr_[0] -= self.pupil_r_[0] / 2
            self.max_mr_[1] -= self.pupil_r_[1] / 2
            self.set_pos(0.5, 0.5)

    def set_pos(self, y, x):
        '''
        瞳の位置を指定する関数

        Parameters
        ----------
        y   : float 
            眼のy座標((縦方向のpixel数)*0.0-1.0)

        x   : float 
            眼のx座標((横方向のpixel数)*0.0-1.0)
        Returns
        -------
        None
        '''

        rot_x = (x-0.5)*self.cos_th - (y-0.5)*self.sin_th + 0.5
        rot_y = (x-0.5)*self.sin_th + (y-0.5)*self.cos_th + 0.5

        np.clip(rot_y, 0.0, 1.0)
        np.clip(rot_x, 0.0, 1.0)

        px_pos = (  (self.max_mr_[0] - self.min_mr_[0]) * rot_y + self.min_mr_[0],
                    (self.max_mr_[1] - self.min_mr_[1]) * rot_x + self.min_mr_[1])
        self.p_org_px = (int(px_pos[0]-self.pupil_r_[0]/2), int(px_pos[1]-self.pupil_r_[1]/2))

    def get_image(self, src):
        '''
        瞳を描写する関数

        Parameters
        ----------
        src     : ndarray
            入力する画像

        Returns
        -------
        dst     : ndarray
            出力画像
        '''

        dst = copy.copy(src)

        if self.pupil_gif_mode:

            T = 1.0/self.pupil_.get(cv2.CAP_PROP_FPS)
            img = 0

            if (time.time() - self.last_f_tim_) >= T:
                if self.pupil_.get(cv2.CAP_PROP_POS_FRAMES) >= self.pupil_.get(cv2.CAP_PROP_FRAME_COUNT):
                    self.pupil_.set(cv2.CAP_PROP_POS_FRAMES, 0)

                ret, img = self.pupil_.read()
                self.last_f_tim_ = time.time()
            else:
                ret, img = self.pupil_.retrieve()

            if ret:
                dst[self.p_org_px[0]:self.p_org_px[0]+self.pupil_r_[0], 
                    self.p_org_px[1]:self.p_org_px[1]+self.pupil_r_[1]] = img

        else:
            dst[self.p_org_px[0]:self.p_org_px[0]+self.pupil_r_[0], 
                self.p_org_px[1]:self.p_org_px[1]+self.pupil_r_[1]] = self.pupil_
 
        return dst

#まぶた(瞬き)のアニメーションを定義するクラス
class EyeLid:

    def __init__(self, eyelid_cap, eyelid_mask):
        '''
        クラスコンストラクタ

        Parameters
        ----------
        eyelid_cap  : cv2.VideoCapture class object
            まぶたのgif映像

        eyelid_mask : cv2.VideoCapture class object
            まぶたのgif映像のマスク
        '''
        self.eyelid_ = eyelid_cap
        self.eyelid_mask_ = eyelid_mask
        self.last_lid_time = time.time()

        self.lid_sec_ = 3.0
        self.lid_loop_ = 2
        self.lid_scat_ = 7.0

        self.lid_ex_sec_ = random.uniform(0, self.lid_scat_)

    def set_interval(self, sec, loop=2, scat_sec=6.0):
        '''
        瞬きの間隔を指定する関数

        Parameters
        ----------
        sec     : float
            瞬きの間隔(画像を再生する周期)[sec]

        loop    : int
            1回の瞬きにおけるまぶたを閉じる回数[回]
        
        scat_sec: float
            瞬きの間隔の散乱具合[sec]
        
        Returns
        -------
        None
        '''
        self.lid_sec_ = sec
        self.lid_loop_ = loop
        self.lid_scat_ = scat_sec
        self.loop_cnt = 1
        self.last_lid_time = time.time()
        self.lid_ex_sec_ = random.uniform(0, self.lid_scat_)

    def spin_once(self, src):
        '''
        周期を測り瞬きを描写する関数

        Parameters
        ----------
        src     : ndarray
            入力する画像

        Returns
        -------
        dst     : ndarray
            出力画像。瞬きの待ち時間であれば入力画像がそのまま返却される
        '''
        if (time.time() - self.last_lid_time) > (self.lid_sec_+self.lid_ex_sec_): 
            ret_m, mask = self.eyelid_mask_.read()
            ret, frame = self.eyelid_.read()

            if ret_m and ret:
                masked_src = cv2.bitwise_and(src, mask)
                return cv2.addWeighted(masked_src, 1, frame, 1, 0)
            else:
                self.eyelid_mask_.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.eyelid_.set(cv2.CAP_PROP_POS_FRAMES, 0)
                if self.loop_cnt < self.lid_loop_:
                    self.loop_cnt += 1
                else:
                    self.last_lid_time = time.time()
                    self.loop_cnt = random.randint(1, self.lid_loop_)
                    self.lid_ex_sec_ = random.uniform(0, self.lid_scat_)
                return src
        else:
            return src

#眼の動作を制御するサーバーの動作を定義するクラス
class EyesControlServer:

    def __init__(self, obj_right, obj_left, obj_eyelid, port, timeout=10):
        '''
        クラスコンストラクタ

        Parameters
        ----------
        obj_right   : Eye class object
            右目のクラスオブジェクト

        obj_left    : Eye class object
            左目のクラスオブジェクト

        obj_eyelid  : Eyelid class object
            まぶたのクラスオブジェクト

        port        : int
            リッスンするポート

        timeout     : int
            受付の待ち時間
        '''
        self.obj_right_ = obj_right
        self.obj_left_ = obj_left
        self.obj_eyelid_ = obj_eyelid

        self.x_pos_key_         = 'xpos'
        self.y_pos_key_         = 'ypos'
        self.blink_period_key_  = 'period'
        self.blink_num_key_     = 'bnum'
        self.right_mode_key_    = 'rmode'
        self.left_mode_key_     = 'lmode'        

        self.packets = {
            self.x_pos_key_ : 0.5,
            self.y_pos_key_ : 0.5,
            self.blink_period_key_ : 3,
            self.blink_num_key_ : 2,
            self.right_mode_key_: 0,
            self.left_mode_key_: 0
        }

        self.set_pos_()
        self.set_interval_()

        self._is_alive_ = True
        self.init_socket_('', port, timeout)

    def __del__(self):
        '''
        クラスデストラクタ
        '''
        self.kill_process()

    def kill_process(self):
        '''
        通信プロセスをキルします。

        Parameters
        ----------
        None

        Returns
        -------
        None
        '''

        self._is_alive_ = False
        self.server_.close()
        self.th_.join()
        

    def set_pos_(self):
        y = self.packets[self.y_pos_key_]
        x = self.packets[self.x_pos_key_]
        self.obj_right_.set_pos(y, x)
        self.obj_left_.set_pos(y, x)

    def set_interval_(self):
        interval = self.packets[self.blink_period_key_]
        num = self.packets[self.blink_num_key_]
        self.obj_eyelid_.set_interval(interval, num)

    def set_mode_(self):
        rmode = self.packets[self.right_mode_key_]
        lmode = self.packets[self.left_mode_key_]
        self.obj_right_.change_mode(rmode)
        self.obj_left_.change_mode(lmode)

    def init_socket_(self, ip, port, timeout=10):
        self.server_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_.bind((ip, port))
        self.server_.settimeout(timeout)
        self.server_.listen(2)

        self.th_ = threading.Thread(target=self.on_host_waiting_)
        self.th_.start()

    def on_host_waiting_(self):
        while True:
            print('Waiting a host...')
            try:
                conn, addr = self.server_.accept()
                print('Connected from {0}.'.format(addr))
                th = threading.Thread(target=self.on_process_, args=[conn])
                th.start()
                th.join()
            except socket.timeout:
                print('Connection timed out.')

            if self._is_alive_ == False:
                break

    def on_process_(self, conn):
        while True:
            try:
                data = conn.recv(512)
            except InterruptedError:
                break

            if len(data) != 0:
                dict = pickle.loads(data)
                if self.y_pos_key_ in dict and self.x_pos_key_ in dict:
                    self.packets[self.y_pos_key_] = dict[self.y_pos_key_]
                    self.packets[self.x_pos_key_] = dict[self.x_pos_key_]
                    self.set_pos_()

                if self.blink_period_key_ in dict and self.blink_num_key_ in dict:
                    self.packets[self.blink_period_key_] = dict[self.blink_period_key_]
                    self.packets[self.blink_num_key_] = dict[self.blink_num_key_]
                    self.set_interval_()
                
                if self.right_mode_key_ in dict and self.left_mode_key_ in dict:
                    self.packets[self.right_mode_key_] = dict[self.right_mode_key_]
                    self.packets[self.left_mode_key_] = dict[self.left_mode_key_]
                    self.set_mode_()

                print('Data received!\n  data: {0}\n'.format(dict))
                conn.send(data)
            else:
                break
            
            if self._is_alive_ == False:
                break

        print('Close connection.')
        conn.close()

#眼の動作を制御するサーバーのクライアント側で実行できる動作を定義するクラス
class EyesControlClient:

    def __init__(self, ip, port):
        '''
        クラスコンストラクタ

        Parameters
        ----------
        ip      : string
            接続先のIPアドレス

        port    : int
            接続するポート
        '''
        
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((ip, port))

        self.x_pos_key_         = 'xpos'
        self.y_pos_key_         = 'ypos'
        self.blink_period_key_  = 'period'
        self.blink_num_key_     = 'bnum'
        self.right_mode_key_    = 'rmode'
        self.left_mode_key_     = 'lmode'

    def __del__(self):
        '''
        クラスデストラクタ
        '''
        self.client.close()

    def set_pos(self, x, y):
        '''
        瞳の位置をサーバーに送信する関数

        Parameters
        ----------
        x   : float 
            眼のx座標((横方向のpixel数)*0.0-1.0)

        y   : float 
            眼のy座標((縦方向のpixel数)*0.0-1.0)
        
        Returns
        -------
        result  : int
            書き込んだバイト数 [bytes]
        '''
        packets = {
            self.x_pos_key_ : x,
            self.y_pos_key_ : y
        }

        return self.send_(packets)

    def set_blink_interval(self, period, loop_num=2):
        '''
        瞬きの間隔をサーバーに送信する関数

        Parameters
        ----------
        period      : float
            瞬きの間隔(画像を再生する周期)[sec]

        loop_num    : int
            1回の瞬きにおけるまぶたを閉じる回数[回]
        
        Returns
        -------
        result  : int
            書き込んだバイト数 [bytes]
        '''
        packets = {
            self.blink_period_key_  : period,
            self.blink_num_key_     : loop_num
        }

        return self.send_(packets)

    def set_mode(self, right, left):
        '''
        瞳のモードをサーバーに送信する関数

        Parameters
        ----------
        right   : int
            右の瞳のモード  

        left    : int
            左の瞳のモード
        
        Returns
        -------
        result  : int
            書き込んだバイト数 [bytes]
        '''
        packets = {
            self.right_mode_key_    : right,
            self.left_mode_key_     : left
        }

        return self.send_(packets)

    def send_(self, packets):
        serial_packets = pickle.dumps(packets)
        result = self.client.send(serial_packets)
        time.sleep(0.01)
        return result
