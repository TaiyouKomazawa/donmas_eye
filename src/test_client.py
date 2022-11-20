'''
クライアントの通信テスト

黒目の動作、まぶたの瞬きの動作をクライアントから制御するプログラムの例。
ローカルループバックアドレス(127.0.0.1)として実行するため、
同じデバイス内実行されているdonmas_eye_server.pyがあると
それにデータを送信する。

author  : Taiyou Komazawa
date    : 2022/4/23
'''

import time

#ライブラリからEyesControlClientクラスを読み込む
from libs.lib_donmas_eye import EyesControlClient

#127.0.0.1はローカルループバック用のIPアドレス。
#(LANを挟んだサーバーと通信する場合はサーバーのあるデバイスのIPアドレスを指定する。)
IP = '127.0.0.1'
#使用するネットワーク上のポート番号(donmas_eye_server.pyで指定したポート番号と同じものを指定する。)
PORT = 35000

#コントロールクライアントのクラスオブジェクトを宣言(ここでアドレスとポートを引数として渡す。)
client = EyesControlClient(IP, PORT)


#瞳の画像のファイルパス
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

def main():
    client.add_modes(PUPIL_R_FILE_PATHS, PUPIL_L_FILE_PATHS, 1)
    time.sleep(0.1)

    #瞬きの間隔を3.5秒間隔にする。
    client.set_blink_interval(3.5)
    #瞳の位置を原点にセット
    client.set_pos(0, 0)
    #瞳のモードをセット(右:通常の瞳(0), 左:通常の瞳(0))
    client.set_mode(0, 0)

    x = y = 0.5
    while True:
        #まばたき停止
        client.set_blink_interval(3.5, 0)

        #表情を変更
        client.set_mode(1, 1)
        print('Result : ', client.get_response())
        time.sleep(3)
        client.set_mode(2, 2)
        print('Result : ', client.get_response())
        time.sleep(3)
        client.set_mode(3, 3)
        print('Result : ', client.get_response())
        time.sleep(3)
        client.set_mode(4, 4)
        print('Result : ', client.get_response())
        time.sleep(3)
        client.set_mode(0, 0)
        print('Result : ', client.get_response())
        
        #まばたき再開
        client.set_blink_interval(3.5)
        
        #黒眼を動かす
        while y <= 1.0:
            while x <= 1.0:#横方向に動く
                client.set_pos(x, y)
                print('Result : ', client.get_response())
                #無遅延だと速すぎるので50ms待つ
                time.sleep(0.05)
                x += 0.01
            x = 0
            #横方向に最大まで動くと縦方向に動く
            y += 0.1
        y = 0
        

if __name__ == '__main__':
    main()