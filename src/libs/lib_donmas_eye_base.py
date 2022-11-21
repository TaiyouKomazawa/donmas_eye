'''
ドンマス-アイ ベース　ライブラリ

ドンマス-アイの基本動作に必要なクラスを定義してある。

author  : Taiyou Komazawa
date    : 2022/11/21
'''

import os.path, os
import time

import cv2
import numpy as np

import random
import copy

#眼(瞳)のアニメーションを定義するクラス
class Eye:

    def __init__(self, bg, pupil_paths, min_range=[0,0], max_range=[0,0], th=0.0):
        '''
        クラスコンストラクタ

        Parameters
        ----------
        bg          : ndarray
            使用する背景(白目)画像

        pupil_paths       : [string, ...]
            瞳の画像(またはgif)のパスのリスト(モード順のリスト)

        min_range   : [float, float]
            原点(y,x)=(0.0, 0.0)のオフセット画素値[pixel]

        max_range   : [float, float]
            最大値(y,x)=(1.0, 1.0)のオフセット画素値[pixel]

        th  : float
            眼の固定角度(度)
        '''

        self.bg_ = bg

        self.pupils_ = []
        self.pupils_gif_mode_ = []
        for pupil_path in pupil_paths:
            _, ext = os.path.splitext(pupil_path)
            if ext == '.gif':
                self.add_mode(cv2.VideoCapture(pupil_path))
            else:
                self.add_mode(cv2.imread(pupil_path, cv2.IMREAD_COLOR))

        self.bg_r_ = self.bg_.shape[:2]

        self.min_r_ = min_range
        self.max_r_ = max_range

        self.p_pos_ = (0.0, 0.0)
        self.p_noise_ = (0, 0)

        self.cos_th = np.cos(th/180*np.pi)
        self.sin_th = np.sin(th/180*np.pi)

        self.change_mode(0)
        self.last_n_tim_ = time.time()

    def add_mode(self, img, mode_id=-1):
        '''
        瞳のタイプを追加(すでにある場合は上書き)する関数

        Parameters
        ----------
        img     :   ndarray or cv2.VideoCapture
            瞳の画像(またはgif映像)
        mode_id :   int
            追加する瞳の表情モード(負値で最後尾に追加)

        Returns
        -------
        rlt     :   int
            追加・上書きされたモードID, 失敗した場合-1を返す
        '''

        rlt = 0

        if mode_id >= self.numof_mode() or mode_id < 0:
            if type(img) is cv2.VideoCapture:
                self.pupils_.append(img)
                self.pupils_gif_mode_.append(True)
                rlt = self.numof_mode() - 1
            elif type(img) is np.ndarray:
                self.pupils_.append(img)
                self.pupils_gif_mode_.append(False)
                rlt = self.numof_mode() - 1
            else:
                rlt = -1
        elif mode_id < self.numof_mode():
            if type(img) is cv2.VideoCapture:
                self.pupils_[mode_id] = img
                self.pupils_gif_mode_[mode_id] = True
                rlt = mode_id
            elif type(img) is np.ndarray:
                self.pupils_[mode_id] = img
                self.pupils_gif_mode_[mode_id] = False
                rlt = mode_id
            else:
                rlt = -1

        return rlt

    def change_mode(self, mode_id):
        '''
        瞳のタイプを変更する関数

        Parameters
        ----------
        mode_id    : int
            瞳の表情モード

        Returns
        -------
        None
        '''

        if mode_id < len(self.pupils_):
            self.pupil_ = self.pupils_[mode_id]
            self.pupil_gif_mode = self.pupils_gif_mode_[mode_id]

            if self.pupil_gif_mode:
                self.pupil_r_ = [int(self.pupil_.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                                int(self.pupil_.get(cv2.CAP_PROP_FRAME_WIDTH))]
                self.pupil_.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.last_f_tim_ = time.time()
            else:
                self.pupil_r_ = self.pupil_.shape[:2]

            self.min_mr_ = [self.min_r_[0], self.min_r_[1]]
            self.min_mr_[0] += self.pupil_r_[0] / 2
            self.min_mr_[1] += self.pupil_r_[1] / 2
            self.max_mr_ = [self.max_r_[0], self.max_r_[1]]
            self.max_mr_[0] -= self.pupil_r_[0] / 2
            self.max_mr_[1] -= self.pupil_r_[1] / 2
            self.set_pos(0.5, 0.5)

    def numof_mode(self):
        '''
        瞳のタイプの数を返す関数

        Parameters
        ----------
        None

        Returns
        -------
        len     : int
            瞳の表情モードの数
        '''

        return len(self.pupils_)

    def set_pos(self, y, x):
        '''
        瞳の位置を指定する関数

        Parameters
        ----------
        y   : float
            眼のy座標((縦方向のpixel数)*0.0-1.0)

        x   : float
            眼のx座標((横方向のpixel数)*0.0-1.0)
        Returns
        -------
        None
        '''

        rot_x = (x-0.5)*self.cos_th - (y-0.5)*self.sin_th + 0.5
        rot_y = (x-0.5)*self.sin_th + (y-0.5)*self.cos_th + 0.5

        self.p_pos_ = (rot_x, rot_y)

    def spin_once(self, src, noise_range=0.001, noise_sec=1.0):
        '''
        瞳を描写する関数

        Parameters
        ----------
        src     : ndarray
            入力する画像
        noise_range : float
            眼の振れ幅
        noise_sec : float
            瞳の座標振れ間隔

        Returns
        -------
        dst     : ndarray
            出力画像
        '''

        dst = copy.copy(src)

        if((time.time()-self.last_n_tim_) > noise_sec):
            self.p_noise_ = [
                random.uniform(-noise_range, noise_range),
                random.uniform(-noise_range, noise_range)
            ]
            self.last_n_tim_ = time.time()

        p_pos_h = np.clip(self.p_pos_[1]+self.p_noise_[1], 0.0, 1.0)
        p_pos_w = np.clip(self.p_pos_[0]+self.p_noise_[0], 0.0, 1.0)

        px_org = (
            (self.max_mr_[0]-self.min_mr_[0])*p_pos_h+self.min_mr_[0]-self.pupil_r_[0]/2,
            (self.max_mr_[1]-self.min_mr_[1])*p_pos_w+self.min_mr_[1]-self.pupil_r_[1]/2
        )

        p_pxh = [
            int(px_org[0]),
            int(px_org[0])+self.pupil_r_[0]
        ]
        p_pxw = [
            int(px_org[1]),
            int(px_org[1])+self.pupil_r_[1]
        ]

        if self.pupil_gif_mode:

            T = 1.0/self.pupil_.get(cv2.CAP_PROP_FPS)
            img = 0

            if (time.time() - self.last_f_tim_) >= T:
                if self.pupil_.get(cv2.CAP_PROP_POS_FRAMES) >= self.pupil_.get(cv2.CAP_PROP_FRAME_COUNT):
                    self.pupil_.set(cv2.CAP_PROP_POS_FRAMES, 0)

                ret, img = self.pupil_.read()
                self.last_f_tim_ = time.time()
            else:
                ret, img = self.pupil_.retrieve()

            if ret:
                dst[p_pxh[0]:p_pxh[1], p_pxw[0]:p_pxw[1]] = img
        else:
            dst[p_pxh[0]:p_pxh[1], p_pxw[0]:p_pxw[1]] = self.pupil_

        return dst

#まぶた(瞬き)のアニメーションを定義するクラス
class EyeLid:

    def __init__(self, eyelid_cap, eyelid_mask):
        '''
        クラスコンストラクタ

        Parameters
        ----------
        eyelid_cap  : cv2.VideoCapture class object
            まぶたのgif映像

        eyelid_mask : cv2.VideoCapture class object
            まぶたのgif映像のマスク
        '''

        self.eyelid_ = eyelid_cap
        self.eyelid_mask_ = eyelid_mask
        self.last_lid_time = time.time()

        self.lid_sec_ = 3.0
        self.lid_loop_ = 2
        self.lid_scat_ = 7.0

        self.lid_ex_sec_ = random.uniform(0, self.lid_scat_)

    def set_interval(self, sec, loop=2, scat_sec=6.0):
        '''
        瞬きの間隔を指定する関数

        Parameters
        ----------
        sec     : float
            瞬きの間隔(画像を再生する周期)[sec]

        loop    : int
            1回の瞬きにおけるまぶたを閉じる回数[回]

        scat_sec: float
            瞬きの間隔の散乱具合[sec]

        Returns
        -------
        None
        '''

        self.lid_sec_ = sec
        self.lid_loop_ = loop
        self.lid_scat_ = scat_sec
        self.loop_cnt = 1
        self.last_lid_time = time.time()
        self.lid_ex_sec_ = random.uniform(0, self.lid_scat_)

    def spin_once(self, src):
        '''
        周期を測り瞬きを描写する関数

        Parameters
        ----------
        src     : ndarray
            入力する画像

        Returns
        -------
        dst     : ndarray
            出力画像。瞬きの待ち時間であれば入力画像がそのまま返却される
        '''

        if self.lid_loop_ <= 0:
            self.last_lid_time = time.time()
            return src

        if (time.time() - self.last_lid_time) > (self.lid_sec_+self.lid_ex_sec_):
            ret_m, mask = self.eyelid_mask_.read()
            ret, frame = self.eyelid_.read()

            if ret_m and ret:
                masked_src = cv2.bitwise_and(src, mask)
                return cv2.addWeighted(masked_src, 1, frame, 1, 0)
            else:
                self.eyelid_mask_.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.eyelid_.set(cv2.CAP_PROP_POS_FRAMES, 0)
                if self.loop_cnt < self.lid_loop_:
                    self.loop_cnt += 1
                else:
                    self.last_lid_time = time.time()
                    self.loop_cnt = random.randint(1, self.lid_loop_)
                    self.lid_ex_sec_ = random.uniform(0, self.lid_scat_)
                return src
        else:
            return src

