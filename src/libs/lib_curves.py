'''
曲線 ライブラリ

眼を線形的に動かしたいときに便利な関数を提供するライブラリ。
使い方はtest_smooth_perspective.pyを参照。
現在、比例関数(Proportion)、3次関数(Pow3)が使用できる。

'''

import time

class Proportion:
    def __init__(self, y0=0):
        self.T = 0
        self.A = 0
        self.B = y0
        self.t0 = time.time()

    def reset(self, y1, dt):
        t = time.time() - self.t0
        if t > self.T:
            y0 = self.get_out()[0]
            if dt == 0:
                raise ValueError("Must be specified by dt>0.")
            self.T = dt
            self.A = (y1 - y0) / dt
            self.B = y0
            self.t0 = time.time()
            return True
        else:
            return False

    def get_out(self):
        t = time.time() - self.t0
        if self.T >= t:
            return (self.A * t + self.B, False)
        else:
            return (self.A * self.T + self.B, True)

class Pow3:
    def __init__(self, y0=0):
        self.T = 0
        self.A = 0
        self.B = y0
        self.t0 = time.time()

    def reset(self, y1, dt):
        t = time.time() - self.t0
        if t > self.T:
            y0 = self.get_out()[0]
            if dt == 0:
                raise ValueError("Must be specified by dt>0.")
            self.T = dt
            self.A = (y1 - y0) / (dt*dt*dt)
            self.B = y0
            self.t0 = time.time()
            return True
        else:
            return False

    def get_out(self):
        t = time.time() - self.t0
        if self.T >= t:
            return (self.A * t*t*t + self.B, False)
        else:
            return (self.A * self.T*self.T*self.T + self.B, True)

