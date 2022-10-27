'''
ドンマス-アイ サーバー

ドンマス-アイのアニメーションを制御するサーバー
TCP経由で同じネットワーク上にあるクライアントから、
データを受信することでドンマス-アイの視線の移動と瞬きの頻度を変更する。

author  : Taiyou Komazawa
date    : 2022/4/22
'''

import cv2
import numpy as np

#ライブラリからEyeとEyeLibとEyesControlServerクラスを読み込む
from libs.lib_donmasu_eye import Eye, EyeLid, EyesControlServer

#使用するネットワーク上のポート番号
PORT = 35000

#表示する画像の大きさ。現在の設定値はアスペクト比 16:9の画面に合わせている。
SCREEN_HEIGHT   = 720
SCREEN_WIDTH    = 2*1290


#処理に用いる画像の大きさ。瞳の画質に合わせて設定する。
HEIGHT = 270
#左右の眼の画像は1つの連結された画像であるので横幅のみ2倍で定義
HALF_WIDTH = 480
WIDTH = HALF_WIDTH*2

#gif映像のどちらを使うか(True:遅い, False:速い)
EYELID_SLOW_MODE = True

#瞳の画像のファイルパス
PUPIL_R_FILE_PATHS =[
    'img/pupil_normal.png',
    'img/pupil_smile_right.png',
    'img/pupil_fire_fast.gif',
    'img/pupil_dame_right.png',
    'img/pupil_akire_right.png'
]
PUPIL_L_FILE_PATHS =[
    'img/pupil_normal.png',
    'img/pupil_smile_left.png',
    'img/pupil_fire_fast.gif',
    'img/pupil_dame_left.png',
    'img/pupil_akire_left.png'
]

#まぶたの映像とそれに対応するマスク映像のファイルパス
if EYELID_SLOW_MODE == True:
    EYLID_FILE_PATH = 'video/eyelid_slow.gif'
    EYLID_MASK_FILE_PATH = 'video/bin/eyelid_slow.gif'
else:
    EYLID_FILE_PATH = 'video/eyelid_fast.gif'
    EYLID_MASK_FILE_PATH = 'video/bin/eyelid_fast.gif'

#背景(白目)を宣言
bg = 255*np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8)

#まぶたの映像を読み込み
eyelid_img = cv2.VideoCapture(EYLID_FILE_PATH)
#まぶたのマスク映像を読み込み
eyelid_m_img = cv2.VideoCapture(EYLID_MASK_FILE_PATH)

#左右の眼のクラスオブジェクトを宣言
right = Eye(bg, PUPIL_R_FILE_PATHS, min_range=[0, 0],          max_range=[HEIGHT, HALF_WIDTH])
left = Eye(bg, PUPIL_L_FILE_PATHS,  min_range=[0, HALF_WIDTH], max_range=[HEIGHT, WIDTH])


#まぶたのクラスオブジェクトを宣言
eyelid = EyeLid(eyelid_img, eyelid_m_img)
#コントロールサーバーのクラスオブジェクトを宣言(左右の眼のオブジェクト、まぶたのオブジェクト、使用するポートを引数に渡す)
eyes_ctrl_server = EyesControlServer(right, left, eyelid, PORT)

#出力ウィンドウを定義(フルスクリーンで表示)
cv2.namedWindow("eyes_test", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("eyes_test", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

def main():
    while True:
        #右目を描画
        eye = right.get_image(bg)
        #左目を描画
        eyes = left.get_image(eye)
        #瞬きを描画
        eyes = eyelid.spin_once(eyes)
        #ウィンドウの画像を更新
        cv2.imshow("eyes_test", cv2.resize(eyes, dsize=(SCREEN_WIDTH, SCREEN_HEIGHT)))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            eyelid_img.release()
            eyelid_m_img.release()
            cv2.destroyAllWindows()
            print("The 'q' key has been pressed and the main loop has ended.")
            break

    eyes_ctrl_server.kill_process()

if __name__ == '__main__':
    main()

