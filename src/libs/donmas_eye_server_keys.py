'''
ドンマス-アイ サーバー キーリスト

ドンマス-アイとの通信に使用する辞書キー一覧

author  : Taiyou Komazawa
date    : 2022/11/21
'''

class HeaderKey:

    def __init__(self):
        #送信されたデータ数
        self.data_id        = 'data-id'

        self.x_pos          = 'xpos'
        self.y_pos          = 'ypos'
        self.blink_period   = 'period'
        self.blink_num      = 'bnum'
        self.right_mode     = 'rmode'
        self.left_mode      = 'lmode'

        self.right_mode_img = 'rmodeimg'
        self.left_mode_img  = 'lmodeimg'
        self.rl_mode_img    = 'rlmodeimg'
        self.mode_id        = 'mode-id'

        self.mode_num       = 'mode-num'

        self.mode_fname     = 'fname'
        self.mode_bin       = 'bin'

