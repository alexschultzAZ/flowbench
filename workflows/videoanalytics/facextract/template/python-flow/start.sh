#!/bin/bash

mosquitto -d
python3 warm_gpu.py &
fwatchdog
