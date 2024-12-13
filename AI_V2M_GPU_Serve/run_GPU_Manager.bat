@echo off
REM 激活 Conda 环境
call activate FLASK
title GPU_Manager
REM 运行 Python 脚本
python gpu_manager.py
