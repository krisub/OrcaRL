#!/bin/bash

echo "$0"
echo "$1"   # new logdir name and new traindir name
echo "$2"   # number of repetitions

run_interruptible() {
    "$@" &
    cmd_pid=$!

    # trap Ctrl+C only while this command is running
    trap "echo 'Ctrl+C pressed — killing command...'; kill $cmd_pid 2>/dev/null" INT

    wait $cmd_pid     # wait for child to exit
    trap - INT        # restore default trap
}


for ((i = 1; i <= $2; i++)); do
    echo "===== Run $i of $2 ====="

    run_interruptible ./orca-standalone-emulation.sh 44444
done

cd rl-module || exit 1

mv log "${1}_log"
mv train_dir "${1}_train_dir"
mv "${1}_log" step_all_data
mv "${1}_train_dir" step_all_data

mkdir log
