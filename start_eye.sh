#!/bin/sh

SCR_DIR=$(cd $(dirname $0); pwd)
cd $SCR_DIR

python3 src/donmasu_eye_server.py &
sleep 3s
python3 src/scenario_2_client.py $1 $2