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

from .lib_tcp_protocol import *
from .donmas_eye_server_keys import HeaderKey as Key

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

        self.data_id_ = 0

        self.data_ = b''
        self.payload_sz_ = struct.calcsize('>L')

        self.resp_packets_ = {
            Key().data_id : 0,
            Key().mode_num : 0
        }

        self.set_pos(0.5, 0.5)

    def __del__(self):
        '''
        クラスデストラクタ
        '''
        self.client.shutdown(socket.SHUT_RDWR)
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
            Key().x_pos : x,
            Key().y_pos : y
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
            Key().blink_period  : period,
            Key().blink_num     : loop_num
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
            Key().right_mode    : r_mode_id,
            Key().left_mode     : l_mode_id
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
                Key().mode_fname    : f_name,
                Key().mode_bin      : f.read(),
            }
            packets = {
                Key().rl_mode_img   : f_data,
                Key().mode_id       : mode_id
            }

            f.close()
        else:
            _, rf_name = os.path.split(right_path)
            _, lf_name = os.path.split(left_path)

            rf = open(right_path, 'rb')
            lf = open(left_path, 'rb')

            rf_data = {
                Key().mode_fname    : rf_name,
                Key().mode_bin      : rf.read(),
            }
            lf_data = {
                Key().mode_fname    : lf_name,
                Key().mode_bin      : lf.read(),
            }
            packets = {
                Key().right_mode_img: rf_data,
                Key().left_mode_img : lf_data,
                Key().mode_id       : mode_id
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
        return self.resp_packets_[Key().mode_num]

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

        r_dict = receive(self.client)

        if len(r_dict.keys()) > 0:
            self.resp_packets_[Key().data_id] = r_dict[Key().data_id]
            self.resp_packets_[Key().mode_num] = r_dict[Key().mode_num]
            return r_dict
        else:
            return None

    def send_(self, packets):
        packets[Key().data_id] = self.data_id_
        result = send(self.client, packets)
        time.sleep(0.01)
        self.data_id_ += 1
        return result
