'''
ドンマス-アイ クライアント ライブラリ

ドンマス-アイのクライアント動作に必要なクラスを定義してある。

author  : Taiyou Komazawa
date    : 2022/11/21
'''

import os.path, os
import time

import numpy as np

import socket
import struct
import pickle


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

        self.data_id_key_       = 'id'

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

        self.data_id_ = 0

        self.data_ = b''
        self.payload_sz_ = struct.calcsize('>L')

        self.resp_packet_ = {
            self.data_id_key_ : 0,
            self.mode_num_key_ : 0,
            'len' : 0
        }

        self.set_pos(0.5, 0.5)

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

    def set_mode(self, r_mode_id, l_mode_id):
        '''
        瞳のモードをサーバーに送信する関数

        Parameters
        ----------
        r_mode_id   : int
            右の瞳のモード

        l_mode_id   : int
            左の瞳のモード

        Returns
        -------
        result  : int
            書き込んだバイト数 [bytes]
        '''

        packets = {
            self.right_mode_key_    : r_mode_id,
            self.left_mode_key_     : l_mode_id
        }

        return self.send_(packets)

    def add_mode(self, right_path, left_path=None, mode_id=-1):
        '''
        瞳の画像(またはgif画像)をサーバーに送信する関数

        Parameters
        ----------
        right_path  : str
            右目の画像ファイルパス

        left_path   : str
            左目の画像ファイルパス(未指定なら両目とも同じ画像で登録)

        mode_id     : int
            追加する瞳の表情モード位置(負値で最後尾に追加)

        Returns
        -------
        result  : int
            書き込んだバイト数 [bytes]
        '''

        if left_path is None or (right_path == left_path):
            _, f_name = os.path.split(right_path)

            f = open(right_path, 'rb')

            f_data = {
                self.mode_fname_key_    : f_name,
                self.mode_bin_key_      : f.read(),
            }
            packets = {
                self.rl_mode_img_key_   : f_data,
                self.mode_id_key_       : mode_id
            }

            f.close()
        else:
            _, rf_name = os.path.split(right_path)
            _, lf_name = os.path.split(left_path)

            rf = open(right_path, 'rb')
            lf = open(left_path, 'rb')

            rf_data = {
                self.mode_fname_key_    : rf_name,
                self.mode_bin_key_      : rf.read(),
            }
            lf_data = {
                self.mode_fname_key_    : lf_name,
                self.mode_bin_key_      : lf.read(),
            }
            packets = {
                self.right_mode_img_key_: rf_data,
                self.left_mode_img_key_ : lf_data,
                self.mode_id_key_       : mode_id
            }

            rf.close()
            lf.close()

        return self.send_(packets)

    def add_modes(self, right_paths, left_paths, head_m_id=-1):
        '''
        瞳の画像(またはgif画像)リストをサーバーに送信する関数

        Parameters
        ----------
        right_paths : [str,...]
            右目の画像ファイルパスのリスト

        left_paths  : [str,...]
            左目の画像ファイルパスのリスト

        head_m_id   : int
            追加する瞳の表情モードの先頭位置(負値で最後尾から追加)

        Returns
        -------
        None
        '''

        if head_m_id <= -1:
            for (r, l) in zip(right_paths, left_paths):
                self.add_mode(r, l)
        else:
            i = head_m_id
            for (r, l) in zip(right_paths, left_paths):
                self.add_mode(r, l, i)
                i += 1


    def numof_mode(self, sync=True):
        '''
        サーバーから現在使用できる瞳モードの数を取得する関数

        Parameters
        ----------
        sync    : bool
            サーバーからのレスポンスを更新するかどうか

        Returns
        -------
        mode_num    : int
            サーバーに登録されている瞳モードの数
        '''

        if sync:
            self.get_response()
        return self.resp_packet_[self.mode_num_key_]

    def get_response(self):
        '''
        サーバーからレスポンスを取得する関数

        Parameters
        ----------
        None

        Returns
        -------
        data : r_dict
            サーバーからのレスポンス
        '''

        r_dict = self.receive_()

        if len(r_dict.keys()) >= 3:
            self.resp_packet_[self.data_id_key_] = r_dict[self.data_id_key_]
            self.resp_packet_[self.mode_num_key_] = r_dict[self.mode_num_key_]
            self.resp_packet_['len'] = r_dict['len']
            return r_dict
        else:
            return None

    def send_(self, packets):
        packets[self.data_id_key_] = self.data_id_
        serial_packets = pickle.dumps(packets, 0)
        data = struct.pack('>L', len(serial_packets)) + serial_packets
        result = self.client.send(data)
        time.sleep(0.01)
        self.data_id_ += 1
        return result

    def receive_(self):
        while len(self.data_) <= self.payload_sz_:
            self.data_ += self.client.recv(127)
        packed_msg_sz = self.data_[:self.payload_sz_]
        self.data_ = self.data_[self.payload_sz_:]
        msg_sz = struct.unpack('>L', packed_msg_sz)[0]

        while len(self.data_) <= msg_sz:
            self.data_ += self.client.recv(127)

        r_dict = pickle.loads(self.data_[:msg_sz], fix_imports=True, encoding='bytes')
        self.data_ = self.data_[msg_sz:]

        return r_dict
