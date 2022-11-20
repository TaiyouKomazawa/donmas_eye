#!/bin/sh

# ドンマス-アイサーバーと、シナリオサーバとのインターフェイスを同時に起動するshellスクリプト
#
# 次のように、"自動起動するアプリケーションの設定"に登録しておくと、コンピュータ起動時に自動実行される。
# sh /(ドンマスアイの保存場所のパス)/donmas_eye/start_scenario_eye.sh (固定したIPアドレス) (使用するポート)
#
# 例 : sh /home/ubuntu/ドキュメント/donmas_eye/start_scenario_eye.sh 192.168.0.34 35001

SCR_DIR=$(cd $(dirname $0); pwd)
cd $SCR_DIR

#exec 1>>stdout.log
#exec 2>>stderr.log

python3 src/donmas_eye_server.py &
sleep 10s
python3 src/scenario_2_client.py $1 $2
