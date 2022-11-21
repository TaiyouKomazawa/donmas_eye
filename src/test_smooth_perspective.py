'''
なめらかな視線移動のテスト

test_client.pyの瞳の動きをより自然な動作にした例。

author  : Taiyou Komazawa
date    : 2022/4/23
'''

import time

#ライブラリからEyesControlClientクラスとPow3クラスを読み込む
from libs.lib_donmas_eye import EyesControlClient, Pow3

#127.0.0.1はローカルループバック用のIPアドレス。
#(LANを挟んだサーバーと通信する場合はサーバーのあるデバイスのIPアドレスを指定する。)
IP = '127.0.0.1'
#使用するネットワーク上のポート番号(donmas_eye_server.pyで指定したポート番号と同じものを指定する。)
PORT = 35000

#コントロールクライアントのクラスオブジェクトを宣言(ここでアドレスとポートを引数として渡す。)
client = EyesControlClient(IP, PORT)

#x軸方向の動作関数のオブジェクトクラスを宣言(ここで眼を中心から動かしていきたいので0.5を初期値に指定)
fx = Pow3(0.5)
#y軸方向の動作関数のオブジェクトクラスを宣言(ここで眼を中心から動かしていきたいので0.5を初期値に指定)
fy = Pow3(0.5)

def main():
    #瞬きの間隔を4秒間隔にする。
    client.set_blink_interval(4)

    #増加モードからスタート
    x_adding = True
    y_adding = True
    x = y = 0

    #初期の移動先を指定(目標値、移動にかける時間[秒])
    fx.reset(1.0, 4)
    fy.reset(1.0, 20)
    while True:
        #現在の座標と指定した時間が経過したかを取得
        x, x_rlt = fx.get_out()
        y, y_rlt = fy.get_out()

        #x軸側の指定していた時間が経過した場合
        if x_rlt == True:
            #モードを反転
            x_adding = not x_adding

            #増加モード(現在値から1.0まで増やす)
            if x_adding == True:
                fx.reset(1.0, 4)
            #減少モード(現在値から0.0まで減らす)
            else:
                fx.reset(0.0, 4)

        #y軸側の指定していた時間が経過した場合
        if y_rlt == True:
            #モードを反転
            y_adding = not y_adding

            #増加モード(現在値から1.0まで増やす)
            if y_adding == True:
                fy.reset(1.0, 20)
            #減少モード(現在値から0.0まで減らす)
            else:
                fy.reset(0.0, 20)

        #瞳の位置を更新(デバッグ用に返り値を表示)
        print('written :', client.set_pos(x, y), ' [bytes]')
        #無遅延だと速すぎるので50ms待つ
        time.sleep(0.05)

if __name__ == '__main__':
    main()