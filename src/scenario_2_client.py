'''
シナリオサーバーからEyesControlClientへ変換するスクリプト

シナリオサーバーからTCPで送られてくる文字列形式のコマンドを解析してドンマス-アイサーバーを制御します。

author  : Taiyou Komazawa
date    : 2022/4/27
'''

import sys
import time
import random
import re
import socket
import threading


args = sys.argv

TARGET_IP = args[1]
TARGET_PORT = int(args[2])
print("Server IP:", TARGET_IP)
print("Server PORT:", TARGET_PORT)

#ライブラリからEyesControlClientクラスを読み込む
from libs.lib_donmas_eye import EyesControlClient

from libs.lib_curves import Proportion

#127.0.0.1はデバイス内のシナリオサーバからデータを受け取るためのローカルループバック用のIPアドレス。
#SCENARIO_SERVER_IP = '192.168.0.34'
SCENARIO_SERVER_IP = TARGET_IP
#接続先(EyesControlServer)のIPアドレス
CTRL_SERVER_IP = '127.0.0.1'

#シナリオサーバのポート番号
#SCENARIO_SERVER_PORT = 35001
SCENARIO_SERVER_PORT = TARGET_PORT
#接続先のポート番号(donmas_eye_server.pyで指定したポート番号と同じものを指定する。)
CTRL_SERVER_PORT = 35000

#瞳の左右の画像のファイルパス
PUPIL_R_FILE_PATHS =[
    'img/pupil_smile_right.png',
    'img/pupil_fire_fast.gif',
    'img/pupil_dame_right.png',
    'img/pupil_akire_right.png'
]
PUPIL_L_FILE_PATHS =[
    'img/pupil_smile_left.png',
    'img/pupil_fire_fast.gif',
    'img/pupil_dame_left.png',
    'img/pupil_akire_left.png'
]

# シナリオサーバーとEyeCntrolServerの間をつなぐクラス
'''
コマンドの例

瞳を(16,255)の位置に10秒をかけて動かす場合
EYDMRPC0X16Y255T100
瞬きの周期を3.5秒にする場合
EYDMRPC1T35
瞳のモードを通常(右:0, 左:0)から笑顔(右:1, 左:1)変更する
EYDMRPC2M11
'''
class Scenario2Server:
    def __init__(self, ctrl_server_addr, r_paths, l_paths, scenario_addr=['127.0.0.1', 22], timeout=10):

        self.all_pattern = re.compile('EYDMRP(C\d+)(.*)')
        self.all_pattern_ex = re.compile('EYDMRP([^0-9\t\n\r\f\v]+)')
        self.sub_pattern = re.compile('(\D\d+)?(\D\d+)?(\D\d+)?(\D\d+)?.*')

        self.linear_x = Proportion(0.5)
        self.linear_y = Proportion(0.5)

        self._is_alive_ = True
        self.init_socket_(scenario_addr[0], scenario_addr[1], timeout)
        self.client_ = EyesControlClient(ctrl_server_addr[0], ctrl_server_addr[1])

        self.client_.add_modes(r_paths, l_paths, 1)

    def __del__(self):
        self.kill_process()

    def spin_once(self):
        x, xrlt = self.linear_x.get_out()
        y, yrlt = self.linear_y.get_out()
        if not (xrlt and yrlt):
            self.client_.set_pos(x, y)

        return (xrlt and yrlt)

    def kill_process(self):
        self._is_alive_ = False
        self.server_.close()
        self.th_.join()

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

            if self._is_alive_ == False:
                break

            if len(data) != 0:
                dec_data = data.decode('utf-8')

                cmds = self.all_pattern.match(dec_data)

                if cmds is None:
                    #追加のコマンド系、簡易的なコマンドの判定
                    cmds_ex = self.all_pattern_ex.match(dec_data)
                    if cmds_ex is not None:
                        group = cmds_ex.groups()
                        cmd_type = group[0]
                        print(cmd_type)
                        if cmd_type == 'C': #C : 瞳を中心に戻す
                            x = 0.5
                            y = 0.5
                            dt = 0.7
                            print('Got command moving pupil. x:{0}, y:{1}, t:{2}'.format(x, y, dt))
                            self.linear_x.reset(x, dt)
                            self.linear_y.reset(y, dt)
                        elif cmd_type == 'U': #U : 瞳を上に動かす
                            x = 0.5
                            y = 0.05
                            dt = 0.7
                            print('Got command moving pupil. x:{0}, y:{1}, t:{2}'.format(x, y, dt))
                            self.linear_x.reset(x, dt)
                            self.linear_y.reset(y, dt)
                        elif cmd_type == 'D': #D : 瞳を下に動かす
                            x = 0.5
                            y = 0.8
                            dt = 0.7
                            print('Got command moving pupil. x:{0}, y:{1}, t:{2}'.format(x, y, dt))
                            self.linear_x.reset(x, dt)
                            self.linear_y.reset(y, dt)
                        elif cmd_type == 'L': #L : 瞳を左に動かす
                            x = 0.2
                            y = 0.5
                            dt = 0.7
                            print('Got command moving pupil. x:{0}, y:{1}, t:{2}'.format(x, y, dt))
                            self.linear_x.reset(x, dt)
                            self.linear_y.reset(y, dt)
                        elif cmd_type == 'R': #R : 瞳を右に動かす
                            x = 0.8
                            y = 0.5
                            dt = 0.7
                            print('Got command moving pupil. x:{0}, y:{1}, t:{2}'.format(x, y, dt))
                            self.linear_x.reset(x, dt)
                            self.linear_y.reset(y, dt)
                        elif cmd_type == 'RU' or cmd_type == 'UR': #RU : 瞳を右上に動かす
                            x = 0.8
                            y = 0.05
                            dt = 0.7
                            print('Got command moving pupil. x:{0}, y:{1}, t:{2}'.format(x, y, dt))
                            self.linear_x.reset(x, dt)
                            self.linear_y.reset(y, dt)
                        elif cmd_type == 'RD' or cmd_type == 'DR': #RD : 瞳を右下に動かす
                            x = 0.8
                            y = 0.8
                            dt = 0.7
                            print('Got command moving pupil. x:{0}, y:{1}, t:{2}'.format(x, y, dt))
                            self.linear_x.reset(x, dt)
                            self.linear_y.reset(y, dt)
                        elif cmd_type == 'LU' or cmd_type == 'UL': #LU : 瞳を左上に動かす
                            x = 0.2
                            y = 0.05
                            dt = 0.7
                            print('Got command moving pupil. x:{0}, y:{1}, t:{2}'.format(x, y, dt))
                            self.linear_x.reset(x, dt)
                            self.linear_y.reset(y, dt)
                        elif cmd_type == 'LD' or cmd_type == 'DL': #LD : 瞳を左下に動かす
                            x = 0.2
                            y = 0.8
                            dt = 0.7
                            print('Got command moving pupil. x:{0}, y:{1}, t:{2}'.format(x, y, dt))
                            self.linear_x.reset(x, dt)
                            self.linear_y.reset(y, dt)
                        elif cmd_type == 'NORMAL': #NORMAL : 通常
                            self.client_.set_mode(0, 0)
                            self.client_.set_blink_interval(3)
                        elif cmd_type == 'SMILE': #SMILE : 笑顔
                            self.client_.set_blink_interval(3, 0) #瞬き回数を0に
                            self.client_.set_mode(1, 1)
                        elif cmd_type == 'FIRE': #FIRE : 熱血(炎の瞳)
                            self.client_.set_blink_interval(3, 0) #瞬き回数を0に
                            self.client_.set_mode(2, 2)
                        elif cmd_type == 'RCLOSE': #RCLOSE : 右目を瞑る
                            self.client_.set_blink_interval(3, 0) #瞬き回数を0に
                            self.client_.set_mode(1, 0)
                        elif cmd_type == 'LCLOSE': #LCLOSE : 左目を瞑る
                            self.client_.set_blink_interval(3, 0) #瞬き回数を0に
                            self.client_.set_mode(0, 1)
                        elif cmd_type == 'DAME': #DAME : ダメ~な目
                            self.client_.set_blink_interval(3, 0) #瞬き回数を0に
                            self.client_.set_mode(3, 3)
                        elif cmd_type == 'AKIRE': #AKIRE : 呆れた目
                            self.client_.set_blink_interval(3, 0) #瞬き回数を0に
                            self.client_.set_mode(4, 4)
                        else:
                            print('Unknown ex command.')
                    continue

                group = cmds.groups()
                cmd_type = group[0]
                cmd_data = self.sub_pattern.match(group[1])

                if cmd_data is None:
                    continue

                if   cmd_type == 'C0': #C0 : 瞳を動かすコマンドの場合
                    cmd_list = {
                        'X' : 0, #X座標値(X/255)
                        'Y' : 0, #Y座標値(Y/255)
                        'T' : 0  #動作時間(T/10) [秒]
                    }

                    for cmd in cmd_data.groups():
                        if cmd:
                            cmd_list[cmd[0]] = int(cmd[1:])

                    x = cmd_list['X']/255.0
                    y = cmd_list['Y']/255.0
                    dt = cmd_list['T'] / 10.0
                    print('Got command moving pupil. x:{0}, y:{1}, t:{2}'.format(x, y, dt))
                    self.linear_x.reset(x, dt)
                    self.linear_y.reset(y, dt)

                elif cmd_type == 'C1': #C1 : まぶたの周期を設定するコマンドの場合
                    cmd_list = {
                        'T' : 0  #まぶたの周期(T/10) [秒]
                    }

                    for cmd in cmd_data.groups():
                        if cmd:
                            cmd_list[cmd[0]] = int(cmd[1:])

                    t = cmd_list['T'] / 10.0
                    print('Got command eyelid interval. t:{0}'.format(t))
                    self.client_.set_blink_interval(t)
                    
                elif  cmd_type == 'C2': #C2 : 表情(瞳)のモードを設定するコマンドの場合
                    cmd_list = {
                        'M' : '00' #十の位:左のモード、一の位:右のモード
                    }

                    for cmd in cmd_data.groups():
                        if cmd:
                            cmd_list[cmd[0]] = cmd[1:]

                    mode = cmd_list['M']
                    left = int(mode[0])
                    right = int(mode[1])
                    print('Got command pupil mode. L:{0}, R:{0}'.format(left, right))
                    self.client_.set_mode(right, left)
                else:
                    continue

                print('Data received!\n  data: {0}\n'.format(data))
            else:
                break

        print('Close connection.')
        conn.close()

ss = Scenario2Server(
    [CTRL_SERVER_IP, CTRL_SERVER_PORT],
    PUPIL_R_FILE_PATHS,
    PUPIL_L_FILE_PATHS,
    [SCENARIO_SERVER_IP, SCENARIO_SERVER_PORT])

def main():
    while True:
        ss.spin_once()
        time.sleep(0.05)

if __name__ == '__main__':
    main()