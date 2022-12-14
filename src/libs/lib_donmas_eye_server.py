'''
ドンマス-アイ サーバー ライブラリ

ドンマス-アイのサーバー動作に必要なクラスを定義してある。

author  : Taiyou Komazawa
date    : 2022/11/21
'''

import os.path, os

import cv2

import socket

import threading

from .lib_donmas_eye_base import *
from .lib_tcp_protocol import *
from .donmas_eye_server_keys import HeaderKey as Key

#眼の動作を制御するサーバーの動作を定義するクラス
class EyesControlServer:

    def __init__(self, bg, obj_right : Eye, obj_left : Eye, obj_eyelid : EyeLid, port, timeout=10):
        '''
        クラスコンストラクタ

        Parameters
        ----------
        bg          : ndarray
            バックグラウンド画像

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

        self.bg_ = bg
        self.obj_right_ = obj_right
        self.obj_left_ = obj_left
        self.obj_eyelid_ = obj_eyelid

        self.packets = {
            Key().data_id : 0,
            Key().x_pos : 0.5,
            Key().y_pos : 0.5,
            Key().blink_period : 3,
            Key().blink_num : 2,
            Key().right_mode : 0,
            Key().left_mode : 0,

            Key().right_mode_img : '',
            Key().left_mode_img : '',
            Key().rl_mode_img : '',
            Key().mode_id     : -1
        }

        self.resp_packets_ = {
            Key().data_id : 0,
            Key().mode_num : self.obj_right_.numof_mode()
        }

        self.mutex_ = threading.Lock()

        try:
            os.makedirs('tmp_img/')
        except FileExistsError:
            pass

        self.set_pos_()
        self.set_interval_()

        self._is_alive_ = True
        self.init_socket_('', port, timeout)

    def __del__(self):
        '''
        クラスデストラクタ
        '''

        self.close()

    def get_image(self):
        '''
        現在の眼の画像を出力します。

        Parameters
        ----------
        None

        Returns
        -------
        dst     : ndarray
            眼が描画された画像
        '''

        self.mutex_.acquire()
        r = self.obj_right_.spin_once(self.bg_)
        rl = self.obj_left_.spin_once(r)
        dst = self.obj_eyelid_.spin_once(rl)
        self.mutex_.release()

        return dst

    def close(self):
        '''
        通信プロセスを終了します。

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

    def add_mode_(self, is_single_img):

        result = False

        if is_single_img:
            f_bin = self.packets[Key().rl_mode_img]
            mode_id = self.packets[Key().mode_id]

            fpath = 'tmp_img/'+f_bin[Key().mode_fname]

            f = open(fpath, 'wb')
            f.write(f_bin[Key().mode_bin])
            f.close()

            _, ext = os.path.splitext(fpath)
            if ext == '.gif':
                result |= self.obj_right_.add_mode(cv2.VideoCapture(fpath), mode_id)
                result |= self.obj_left_.add_mode(cv2.VideoCapture(fpath), mode_id)
            else:
                result |= self.obj_right_.add_mode(cv2.imread(fpath, cv2.IMREAD_COLOR), mode_id)
                result |= self.obj_left_.add_mode(cv2.imread(fpath, cv2.IMREAD_COLOR), mode_id)
        else:
            rf_bin = self.packets[Key().right_mode_img]
            lf_bin = self.packets[Key().left_mode_img]
            mode_id = self.packets[Key().mode_id]

            rfpath = 'tmp_img/'+rf_bin[Key().mode_fname]
            lfpath = 'tmp_img/'+lf_bin[Key().mode_fname]

            rf = open(rfpath, 'wb')
            lf = open(lfpath, 'wb')
            rf.write(rf_bin[Key().mode_bin])
            lf.write(lf_bin[Key().mode_bin])
            rf.close()
            lf.close()

            _, ext = os.path.splitext(rfpath)
            if ext == '.gif':
                result |= self.obj_right_.add_mode(cv2.VideoCapture(rfpath), mode_id)
            else:
                result |= self.obj_right_.add_mode(cv2.imread(rfpath, cv2.IMREAD_COLOR), mode_id)

            _, ext = os.path.splitext(lfpath)
            if ext == '.gif':
                result |= self.obj_left_.add_mode(cv2.VideoCapture(lfpath), mode_id)
            else:
                result |= self.obj_left_.add_mode(cv2.imread(lfpath, cv2.IMREAD_COLOR), mode_id)
        if result:
            print('Add mode done!')

    def set_pos_(self):
        y = self.packets[Key().y_pos]
        x = self.packets[Key().x_pos]
        self.obj_right_.set_pos(y, x)
        self.obj_left_.set_pos(y, x)

    def set_interval_(self):
        interval = self.packets[Key().blink_period]
        num = self.packets[Key().blink_num]
        self.obj_eyelid_.set_interval(interval, num)

    def set_mode_(self):
        rmode = self.packets[Key().right_mode]
        lmode = self.packets[Key().left_mode]
        self.obj_right_.change_mode(rmode)
        self.obj_left_.change_mode(lmode)

    def init_socket_(self, ip, port, timeout=10):
        self.server_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_.bind((ip, port))
        self.server_.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_.settimeout(timeout)
        self.server_.listen(3)

        self.th_ = threading.Thread(target=self.on_host_waiting_)
        self.th_.setDaemon(True)
        self.th_.start()

    def on_host_waiting_(self):
        while self._is_alive_ != False:
            try:
                conn, addr = self.server_.accept()
                print('[des]Connected from {0}.'.format(addr))
                th = threading.Thread(target=self.on_process_, args=[conn, addr])
                th.setDaemon(True)
                th.start()

            except socket.timeout:
                print('[des]Waiting a host...')
            except KeyboardInterrupt:
                break

    def on_process_(self, conn, addr):
        self.obj_left_.change_mode(0)
        self.obj_right_.change_mode(0)

        while True:
            try:
                r_dict = receive(conn)

                if len(r_dict.keys()) != 0:
                    self.mutex_.acquire()

                    if Key().data_id in r_dict:
                        self.resp_packets_[Key().data_id] = r_dict[Key().data_id]
                        self.resp_packets_[Key().mode_num] = self.obj_right_.numof_mode()

                    if Key().y_pos in r_dict and Key().x_pos in r_dict:
                        self.packets[Key().y_pos] = r_dict[Key().y_pos]
                        self.packets[Key().x_pos] = r_dict[Key().x_pos]
                        self.set_pos_()

                    if Key().blink_period in r_dict and Key().blink_num in r_dict:
                        self.packets[Key().blink_period] = r_dict[Key().blink_period]
                        self.packets[Key().blink_num] = r_dict[Key().blink_num]
                        self.set_interval_()

                    if Key().right_mode in r_dict and Key().left_mode in r_dict:
                        self.packets[Key().right_mode] = r_dict[Key().right_mode]
                        self.packets[Key().left_mode] = r_dict[Key().left_mode]
                        self.set_mode_()

                    if Key().right_mode_img in r_dict and Key().left_mode_img in r_dict:
                        self.packets[Key().right_mode_img] = r_dict[Key().right_mode_img]
                        self.packets[Key().left_mode_img] = r_dict[Key().left_mode_img]
                        self.packets[Key().mode_id] = r_dict[Key().mode_id]
                        self.add_mode_(False)

                    if Key().rl_mode_img in r_dict:
                        self.packets[Key().rl_mode_img] = r_dict[Key().rl_mode_img]
                        self.packets[Key().mode_id] = r_dict[Key().mode_id]
                        self.add_mode_(True)

                    self.mutex_.release()
                    send(conn, self.resp_packets_)
                    print('Data received from {0}.\n  keys: {1}\n'.format(addr, r_dict.keys()))
            except ConnectionResetError:
                print('[des]Disconnected from client({0}).'.format(addr))
                break

            if self._is_alive_ == False:
                break

        print('Close connection.')
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()
