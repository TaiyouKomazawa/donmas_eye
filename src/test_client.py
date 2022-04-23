'''
クライアントの通信テスト

黒目の動作、まぶたの瞬きの動作をクライアントから制御するプログラムの例。
ローカルループバックアドレス(127.0.0.1)として実行するため、
同じデバイス内実行されているdonmasu_eye_server.pyがあると
それにデータを送信する。

author  : Taiyou Komazawa
date    : 2022/4/23
'''

import time

#ライブラリからEyesControlClientクラスを読み込む
from libs.lib_donmasu_eye import EyesControlClient

#127.0.0.1はローカルループバック用のIPアドレス。
#(LANを挟んだサーバーと通信する場合はサーバーのあるデバイスのIPアドレスを指定する。)
IP = '127.0.0.1'
#使用するネットワーク上のポート番号(donmasu_eye_server.pyで指定したポート番号と同じものを指定する。)
PORT = 35000

#コントロールクライアントのクラスオブジェクトを宣言(ここでアドレスとポートを引数として渡す。)
client = EyesControlClient(IP, PORT)

def main():
    #瞬きの間隔を3.5秒間隔にする。
    client.set_blink_interval(3.5)
    #瞳の位置を原点にセット
    client.set_pos(0, 0)

    x = y = 0
    while True:
        #横方向に動く
        x += 0.01
        if x >= 1.0:
            x = 0
            #横方向に最大まで動くと縦方向に動く
            y += 0.1
        if y >= 1.0:
            y = 0
        
        #瞳の位置を更新(デバッグ用に返り値を表示)
        print('written :', client.set_pos(x, y), ' [bytes]')
        #無遅延だと速すぎるので50ms待つ
        time.sleep(0.05)

if __name__ == '__main__':
    main()