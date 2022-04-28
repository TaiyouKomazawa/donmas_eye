'''
シナリオサーバーからEyesControlClientへ変換するスクリプト

author  : Taiyou Komazawa
date    : 2022/4/27
'''

import time
import random
import re
import socket
import threading


#ライブラリからEyesControlClientクラスを読み込む
from libs.lib_donmasu_eye import EyesControlClient

from libs.lib_curves import Proportion

#127.0.0.1はデバイス内のシナリオサーバからデータを受け取るためのローカルループバック用のIPアドレス。
SCENARIO_SERVER_IP = '127.0.0.1'
#接続先(EyesControlServer)のIPアドレス
CTRL_SERVER_IP = '127.0.0.1'


SCENARIO_SERVER_PORT = 35001
#使用するネットワーク上のポート番号(donmasu_eye_server.pyで指定したポート番号と同じものを指定する。)
CTRL_SERVER_PORT = 35000

class Scenario2Server:
    def __init__(self, ctrl_server_addr, scenario_addr=['127.0.0.1', 22], timeout=10):

        self.all_pattern = re.compile('EYDMRP(C\d+)(.*)')
        self.sub_pattern = re.compile('(\D\d+)?(\D\d+)?(\D\d+)?(\D\d+)?.*')

        self.linear_x = Proportion(0.5)
        self.linear_y = Proportion(0.5)

        self._is_alive_ = True
        self.init_socket_(scenario_addr[0], scenario_addr[1], timeout)
        self.client_ = EyesControlClient(ctrl_server_addr[0], ctrl_server_addr[1])

    def __del__(self):
        self.kill_process()

    def spin_once(self, noise_range=0.003):
        x, xrlt = self.linear_x.get_out()
        y, yrlt = self.linear_y.get_out()

        x += random.uniform(-noise_range, noise_range)
        y += random.uniform(-noise_range, noise_range)

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
                cmds = self.all_pattern.match(data.decode('utf-8'))

                if cmds is None:
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

ss = Scenario2Server([CTRL_SERVER_IP, CTRL_SERVER_PORT], [SCENARIO_SERVER_IP, SCENARIO_SERVER_PORT])

def main():

    x = y = 0
    while True:
        ss.spin_once()
        time.sleep(0.05)

if __name__ == '__main__':
    main()