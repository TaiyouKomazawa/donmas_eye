'''
ドンマス-アイ サーバー ライブラリ

ドンマス-アイのサーバー動作に必要なクラスを定義してある。

author  : Taiyou Komazawa
date    : 2022/11/21
'''
import typing

import os.path, os

import cv2

import socket
import struct
import pickle

import threading

from .lib_donmas_eye_base import *

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

        self.data_id_key_ = 'id'

        self.x_pos_key_         = 'xpos'
        self.y_pos_key_         = 'ypos'
        self.blink_period_key_  = 'period'
        self.blink_num_key_     = 'bnum'
        self.right_mode_key_    = 'rmode'
        self.left_mode_key_     = 'lmode'

        self.right_mode_img_key_    = 'rmodeimg'
        self.left_mode_img_key_     = 'lmodeimg'
        self.rl_mode_img_key_       = 'rlmodeimg'
        self.mode_id_key_           = 'mode-id'

        self.mode_num_key_      = 'mode-num'

        self.mode_fname_key_    = 'fname'
        self.mode_bin_key_      = 'bin'

        self.packets = {
            self.data_id_key_ : 0,
            self.x_pos_key_ : 0.5,
            self.y_pos_key_ : 0.5,
            self.blink_period_key_ : 3,
            self.blink_num_key_ : 2,
            self.right_mode_key_ : 0,
            self.left_mode_key_ : 0,

            self.right_mode_img_key_ : '',
            self.left_mode_img_key_ : '',
            self.rl_mode_img_key_ : '',
            self.mode_id_key_     : -1
        }

        self.resp_packet_ = {
            self.data_id_key_ : 0,
            self.mode_num_key_ : self.obj_right_.numof_mode(),
            'len' : 0
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

        self.kill_process()

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

    def add_mode_(self, is_single_img):

        result = False

        if is_single_img:
            f_bin = self.packets[self.rl_mode_img_key_]
            mode_id = self.packets[self.mode_id_key_]

            fpath = 'tmp_img/'+f_bin[self.mode_fname_key_]

            f = open(fpath, 'wb')
            f.write(f_bin[self.mode_bin_key_])
            f.close()

            _, ext = os.path.splitext(fpath)
            if ext == '.gif':
                result |= self.obj_right_.add_mode(cv2.VideoCapture(fpath), mode_id)
                result |= self.obj_left_.add_mode(cv2.VideoCapture(fpath), mode_id)
            else:
                result |= self.obj_right_.add_mode(cv2.imread(fpath, cv2.IMREAD_COLOR), mode_id)
                result |= self.obj_left_.add_mode(cv2.imread(fpath, cv2.IMREAD_COLOR), mode_id)
        else:
            rf_bin = self.packets[self.right_mode_img_key_]
            lf_bin = self.packets[self.left_mode_img_key_]
            mode_id = self.packets[self.mode_id_key_]

            rfpath = 'tmp_img/'+rf_bin[self.mode_fname_key_]
            lfpath = 'tmp_img/'+lf_bin[self.mode_fname_key_]

            rf = open(rfpath, 'wb')
            lf = open(lfpath, 'wb')
            rf.write(rf_bin[self.mode_bin_key_])
            lf.write(lf_bin[self.mode_bin_key_])
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
            print('Add mode!!')

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

        self.payload_sz_ = struct.calcsize('>L')
        self.data_ = b''

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

                self.obj_left_.change_mode(0)
                self.obj_right_.change_mode(0)
                self.obj_eyelid_.set_interval(3, 2)
            except socket.timeout:
                print('Connection timed out.')

            if self._is_alive_ == False:
                break

    def send_(self, conn, packets):
        serial_packets = pickle.dumps(packets, 0)
        data = struct.pack('>L', len(serial_packets)) + serial_packets
        result = conn.send(data)
        return result

    def receive_(self, conn):
        while len(self.data_) <= self.payload_sz_:
            self.data_ += conn.recv(127)
        packed_msg_sz = self.data_[:self.payload_sz_]
        self.data_ = self.data_[self.payload_sz_:]
        msg_sz = struct.unpack('>L', packed_msg_sz)[0]

        while len(self.data_) <= msg_sz:
            self.data_ += conn.recv(127)

        r_dict = pickle.loads(self.data_[:msg_sz], fix_imports=True, encoding='bytes')
        self.data_ = self.data_[msg_sz:]

        return r_dict

    def on_process_(self, conn):
        while True:
            r_dict = self.receive_(conn)

            if len(r_dict.keys()) != 0:
                self.mutex_.acquire()

                if self.data_id_key_ in r_dict:
                    self.resp_packet_[self.data_id_key_] = r_dict[self.data_id_key_]
                    self.resp_packet_[self.mode_num_key_] = self.obj_right_.numof_mode()
                    self.resp_packet_['len'] = len(self.data_)

                if self.y_pos_key_ in r_dict and self.x_pos_key_ in r_dict:
                    self.packets[self.y_pos_key_] = r_dict[self.y_pos_key_]
                    self.packets[self.x_pos_key_] = r_dict[self.x_pos_key_]
                    self.set_pos_()

                if self.blink_period_key_ in r_dict and self.blink_num_key_ in r_dict:
                    self.packets[self.blink_period_key_] = r_dict[self.blink_period_key_]
                    self.packets[self.blink_num_key_] = r_dict[self.blink_num_key_]
                    self.set_interval_()

                if self.right_mode_key_ in r_dict and self.left_mode_key_ in r_dict:
                    self.packets[self.right_mode_key_] = r_dict[self.right_mode_key_]
                    self.packets[self.left_mode_key_] = r_dict[self.left_mode_key_]
                    self.set_mode_()

                if self.right_mode_img_key_ in r_dict and self.left_mode_img_key_ in r_dict:
                    self.packets[self.right_mode_img_key_] = r_dict[self.right_mode_img_key_]
                    self.packets[self.left_mode_img_key_] = r_dict[self.left_mode_img_key_]
                    self.packets[self.mode_id_key_] = r_dict[self.mode_id_key_]
                    self.add_mode_(False)

                elif self.rl_mode_img_key_ in r_dict:
                    self.packets[self.rl_mode_img_key_] = r_dict[self.rl_mode_img_key_]
                    self.packets[self.mode_id_key_] = r_dict[self.mode_id_key_]
                    self.add_mode_(True)

                self.mutex_.release()
                self.send_(conn, self.resp_packet_)
                print('Data received!\n  keys: {0}\n'.format(r_dict.keys()))

            if self._is_alive_ == False:
                break

        print('Close connection.')
        conn.close()
