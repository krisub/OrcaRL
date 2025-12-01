#!/bin/bash

echo "$1"

cp -r "./rl-module/backup_tds/$1" "./rl-module/train_dir"
./orca-standalone-emulation.sh 44444
cd rl-module
rm -rf log
rm -rf train_dir
mkdir log
