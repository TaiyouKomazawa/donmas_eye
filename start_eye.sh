#!/bin/sh

# サーバーとシナリオサーバとのインターフェイスを同時に起動するshellスクリプト
#
# 次のように、"自動起動するアプリケーションの設定"に登録しておくと、コンピュータ起動時に自動実行される。
# sh /(ドンマスアイの保存場所のパス)/donmasu_eye/start_eye.sh (固定したIPアドレス) (使用するポート)
#
# 例 : sh /home/ubuntu/ドキュメント/donmasu_eye/start_eye.sh 192.168.0.34 35001

SCR_DIR=$(cd $(dirname $0); pwd)
cd $SCR_DIR

python3 src/donmasu_eye_server.py &
sleep 3s
python3 src/scenario_2_client.py $1 $2