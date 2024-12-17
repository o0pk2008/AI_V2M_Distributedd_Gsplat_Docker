#
# client 端 api 实现
#


import sqlite3, os, threading,subprocess
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
# 导入配置数据
from app.config import Config
# 导入工具函数
from app.utils import (
    # extract_username_from_email,
    get_db_connection,
    execute_with_retry,
    generate_folder_name, # 生成带日期和随机数字的文件夹名
    allowed_file,  # 检查文件扩展名是否合法
    save_to_database, # 连接数据库储存上传的数据初始化
    send_task_to_GPU_Manager, # 上传事件请求事件分发路由
    is_valid_email, # 邮箱校验
)


# 创建蓝图对象
client_api_bp = Blueprint('client_api_bp', __name__)

# 获取配置数据
database_path = Config.DATABASE_PATH
updata_url = Config.UPDATA_URL
edit_url = Config.EDIT_URL
CloudStorage = Config.CLOUD_STORAGE
ClientIP = Config.ClientIP
TaskServer = Config.TASK_SERVE_URL


# 返回配置数据
@client_api_bp.route('/client_api/v1/config', methods=['POST'])
def get_config():
    try:
        return jsonify({
            'status': 'success',
            'data': {
                'client_ip': ClientIP,
                'task_server': TaskServer
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred.',
            'details': str(e)
        })