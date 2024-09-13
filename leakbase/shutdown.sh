#!/bin/bash

PROCESS=$(ps -ef|grep run_lb.py |grep -v grep|grep -v PPID|awk '{ print $2}')

for pid in $PROCESS
do
    kill -15 $pid
    echo "Killed process with PID: $pid"
done