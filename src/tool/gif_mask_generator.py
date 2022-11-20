'''
gif映像のマスク生成器

gif映像を2値化して画像合成用のマスクに使える画像に変換して出力する
マスク画像はまぶたの切り出し処理に使用される。

まぶたの映像(gif形式のみを想定しています)を変えた際に必ず実行すること。

author  : Taiyou Komazawa
date    : 2022/4/22
'''

import cv2
#openCVとは別の画像処理ライブラリ(Pillow)を使用する。
from PIL import Image

#読み込むファイルパス
file_in = 'video/eyelid_fast.gif'
#出力先のファイルパス
file_out = 'video/bin/eyelid_fast.gif'

#file_in = 'video/eyelid_slow.gif'
#file_out = 'video/bin/eyelid_slow.gif'

#映像(gifファイル)を読み込み
vid = cv2.VideoCapture(file_in)

imgs = []

while True:
    ret, frame = vid.read()
    
    if ret:
        print('f:', vid.get(cv2.CAP_PROP_POS_FRAMES))
        print('  ', frame.shape)

        #1フレームをグレイスケールに変換
        frame_g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #グレイスケールを2値(0 or 255)画像に変換(明るさが0の位置を0、それ以外の画素を255にする。明るさが0の画素がまぶたとして表示される。)
        frame_bin = cv2.threshold(frame_g, 1, 255, cv2.THRESH_BINARY)[1]
        #画像のビットを反転。
        frame_bin = cv2.bitwise_not(frame_bin)
        #画像をPillowの画像形式で時系列で重ねていく。
        imgs.append(Image.fromarray(frame_bin).convert('P'))
    else:
        break

#画像の再生時間を算出
dur = 1.0/vid.get(cv2.CAP_PROP_FPS) * len(imgs)
#gif形式でファイルにエンコード
imgs[0].save(file_out, save_all=True, append_images=imgs[1:], optimize=False, duration=dur, loop=0)

vid.release()
