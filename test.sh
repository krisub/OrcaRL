#!/bin/bash

echo "$0"
echo "$1"   # new logdir name and new traindir name

run_interruptible() {
    "$@" &
    cmd_pid=$!

    # trap Ctrl+C only while this command is running
    trap "echo 'Ctrl+C pressed — killing command...'; kill $cmd_pid 2>/dev/null" INT

    wait $cmd_pid     # wait for child to exit
    trap - INT        # restore default trap
}


run_interruptible ./orca-standalone-emulation.sh 44444

cd rl-module || exit 1

mv log "${1}_log"
mv train_dir "${1}_train_dir"

mkdir log

