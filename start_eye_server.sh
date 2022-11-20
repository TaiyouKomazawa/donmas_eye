#!/bin/sh

# ドンマス-アイサーバーのみを起動するshellスクリプト
#
# 次のように、"自動起動するアプリケーションの設定"に登録しておくと、コンピュータ起動時に自動実行される。
# sh /(ドンマスアイの保存場所のパス)/donmas_eye/start_eye_server.sh
#
# 例 : sh /home/ubuntu/ドキュメント/donmas_eye/start_eye_server.sh

SCR_DIR=$(cd $(dirname $0); pwd)
cd $SCR_DIR

#exec 1>>stdout.log
#exec 2>>stderr.log

python3 src/donmas_eye_server.py
