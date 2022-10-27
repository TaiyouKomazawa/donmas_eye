'''
眼のアニメーションテスト

黒目の動作、まぶたの瞬きの動作デモ。
通信はしないけどアニメーションの動作は見たいという場合に使う。

author  : Taiyou Komazawa
date    : 2022/4/22
'''

import cv2
import numpy as np

#ライブラリからEyeとEyeLibクラスを読み込む
from libs.lib_donmasu_eye import Eye, EyeLid

#アスペクト比 16:9 (表示したいディスプレイの比率に合わせて設定する) 
HEIGHT = 270
#左右の眼の画像は1つの連結された画像であるので横幅のみ2倍で定義
HALF_WIDTH = 480
WIDTH = HALF_WIDTH*2

#gif映像のどちらを使うか(True:遅いバージョン, False:速いバージョン)
EYELID_SLOW_MODE = True

#瞳の画像のファイルパス
PUPIL_R_FILE_PATHS =[
    'img/pupil_fire.gif',
    'img/pupil_normal.png',
    'img/pupil_smile_right.png'
]
PUPIL_L_FILE_PATHS =[
    'img/pupil_fire.gif',
    'img/pupil_normal.png',
    'img/pupil_smile_left.png'
]

#まぶたの映像とそれに対応するマスク映像のファイルパス
if EYELID_SLOW_MODE == True:
    EYLID_FILE_PATH = 'video/eyelid_slow.gif'
    EYLID_MASK_FILE_PATH = 'video/bin/eyelid_slow.gif'
else:
    EYLID_FILE_PATH = 'video/eyelid_fast.gif'
    EYLID_MASK_FILE_PATH = 'video/bin/eyelid_fast.gif'

#瞬きの間隔 [秒]
BLINK_INTERVAL = 2.0
#瞬きの数 [回数](映像の再生回数。瞬き1回分の映像なので2回が一番自然かと。)
BLINK_NUM = 2

#背景(白目)を宣言
bg = np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8)

#まぶたの映像を読み込み
eyelid_img = cv2.VideoCapture(EYLID_FILE_PATH)
#まぶたのマスク映像を読み込み
eyelid_m_img = cv2.VideoCapture(EYLID_MASK_FILE_PATH)

#左右の眼のクラスオブジェクトを宣言
right = Eye(bg, PUPIL_R_FILE_PATHS, min_range=[0, 0],          max_range=[HEIGHT, HALF_WIDTH])
left = Eye(bg, PUPIL_L_FILE_PATHS,  min_range=[0, HALF_WIDTH], max_range=[HEIGHT, WIDTH])

#まぶたのクラスオブジェクトを宣言
eyelid = EyeLid(eyelid_img, eyelid_m_img)

#出力ウィンドウを定義(フルスクリーンで表示)
cv2.namedWindow("eyes_test", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("eyes_test", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

#瞳の位置を原点にする(画像において左上が原点)
right.set_pos(0, 0)
left.set_pos(0, 0)

#瞬きの間隔と1回の瞬きにおいてまぶたを閉じる回数を指定する。
eyelid.set_interval(BLINK_INTERVAL, BLINK_NUM)

right.change_mode(0)
left.change_mode(0)

x = y = 0
while True:
    #右目を描画
    eye = right.get_image(bg)
    #左目を描画
    eyes = left.get_image(eye)
    #瞬きを描画
    eyes = eyelid.spin_once(eyes)
    #ウィンドウの画像を更新
    cv2.imshow("eyes_test", eyes)

    #横方向に動く
    x += 0.01
    if x >= 1.0:
        x = 0
        #横方向に最大まで動くと縦方向に動く
        y += 0.1
        if y >= 1.0:
            y = 0

    #瞳の位置を設定する
    right.set_pos(y, x)
    left.set_pos(y, x)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

eyelid_img.release()
eyelid_m_img.release()
cv2.destroyAllWindows()

