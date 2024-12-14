import os,toml

environment = os.getenv('env', '')

class Config:
    # 读取配置文件
    config_url = 'config.toml'

    if environment == 'dev': # 开发环境
        config_url = 'config_dev.toml'
    elif environment == 'test': # 测试环境
        config_url = 'config_test.toml'
    else: # 生产环境
        config_url = 'config.toml'

    with open(config_url, 'r') as file:
        toml_data = toml.load(file)

    CLOUD_STORAGE = toml_data.get('servers', {}).get('upload_folder', {}).get('http')
    UPDATA_URL = toml_data.get('servers', {}).get('updata_url', {}).get('http')
    EDIT_URL = toml_data.get('servers', {}).get('edit_url', {}).get('http')
    TASK_SERVE_URL = toml_data.get('servers', {}).get('task_serve', {}).get('http')
    SERVER_PORT = toml_data.get('servers', {}).get('home_port', {}).get('port')
    DATABASE_PATH = toml_data.get('servers', {}).get('database', {}).get('path')
    ClientIP = toml_data.get('servers', {}).get('clientIP', {}).get('http')
    MediaSDK = toml_data.get('cmd', {}).get('convert', {}).get('MediaSDK')
    ALLOWED_EXTENSIONS = {'mp4', 'mov'}