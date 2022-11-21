'''
ドンマス-アイ サーバー キーリスト

ドンマス-アイとの通信に使用する辞書キー一覧

author  : Taiyou Komazawa
date    : 2022/11/21
'''

class HeaderKey:

    def __init__(self):
    # クライアント -> サーバー ----
        #サーバーに送信されたコマンドのID
        self.data_id        = 'data-id'
        #瞳のx座標
        self.x_pos          = 'xpos'
        #瞳のy座標
        self.y_pos          = 'ypos'
        #瞳のまばたき間隔
        self.blink_period   = 'period'
        #瞳の瞬き数
        self.blink_num      = 'bnum'
        #右瞳表情モード
        self.right_mode     = 'rmode'
        #左瞳表情モード
        self.left_mode      = 'lmode'
        #右瞳表情モードの画像パケット
        self.right_mode_img = 'rmodeimg'
        #左瞳表情モードの画像パケット
        self.left_mode_img  = 'lmodeimg'
        #左右共通瞳表情モードの画像パケット
        self.rl_mode_img    = 'rlmodeimg'
        #画像パケット->画像ファイル名
        self.mode_fname     = 'fname'
        #画像パケット->画像バイナリデータ
        self.mode_bin       = 'bin'
        #追加する表情モードのID
        self.mode_id        = 'mode-id'
    #----

    # サーバー -> クライアント ----
        #サーバーに送信されたコマンドのID
        #self.data_id        = 'data-id'
        #使用できる瞳表情モードの数
        self.mode_num       = 'mode-num'

