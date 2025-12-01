#!/bin/bash

value=$(sysctl -n net.ipv4.tcp_meta_enable)
[ "$value" -eq 0 ] && echo "NO ALGO SWITCHING"
value=$(sysctl -n net.ipv4.tcp_deepcc)
[ "$value" -eq 0 ] && echo "NO ORCA"
grep -E '^[[:space:]]*use_lstm' rl-module/agent.py
grep -E '^[[:space:]]*use_log' rl-module/envwrapper.py
grep -E '^[[:space:]]*bool use_dynamic' src/orca-server-mahimahi.cc
grep -E '^[[:space:]]*bool use_orca' src/orca-server-mahimahi.cc
