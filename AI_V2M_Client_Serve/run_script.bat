@echo off
REM 激活 Conda 环境
call activate FLASK

title Client_Serve

REM 运行 Python 脚本
python main.py
