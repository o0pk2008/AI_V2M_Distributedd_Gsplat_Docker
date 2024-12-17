# 
# 工具函数模块
#

import sqlite3, random, re, string,logging
from datetime import datetime
# 解决与google requests的冲突
import requests as normal_requests
# 配置项
from app.config import Config


# 获取配置数据
CloudStorage = Config.CLOUD_STORAGE
updata_url = Config.UPDATA_URL
edit_url = Config.EDIT_URL
task_serve_url = Config.TASK_SERVE_URL
server_port = Config.SERVER_PORT
database_path = Config.DATABASE_PATH
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
ClientIP = Config.ClientIP


# 数据库连接重试机制
def get_db_connection(database):
    conn = sqlite3.connect(database, timeout=10)
    # 将行工厂设为 sqlite3.row
    # note:
    # 以便查询结果返回类似字典的对象，可以通过字段名访问列
    conn.row_factory = sqlite3.Row
    return conn



def execute_with_retry(cursor, sql, params=(), retries=5, delay=0.5):
    for i in range(retries):
        try:
            cursor.execute(sql, params)
            return
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                time.sleep(delay)
            else:
                raise



# 邮箱校验
def is_valid_email(email):
    # 正则表达式校验邮箱格式
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None



# 获取当前当前时间日期（格式化后的）
# 其他参考： now = datetime.utcnow().isoformat()
def get_datetime(format = '%Y-%m-%d %H:%M:%S'):
    now = datetime.now()
    # 格式化为字符串
    formatted_now = now.strftime(format)
    return formatted_now



# 生成带日期和随机数字的文件夹名
def generate_folder_name():
    current_date = datetime.now().strftime("%Y%m%d")
    random_digits = ''.join(random.choices(string.digits, k=4))
    folder_name = f"{current_date}_{random_digits}"
    return folder_name



# 检查文件扩展名是否合法
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS



# 请求GPU_Manager服务器进行运算
# def send_task_to_GPU_Manager(file_path, folder_name, export_mesh):
#     # 从配置表获取GPU_Manager服务器地址
#     base_url = task_serve_url

#     # Test case with project_id and video_path parameters
#     data = {"file_path": file_path, "folder_name": folder_name, "export_mesh": export_mesh}
#     endpoint = '/add_task'

#     try:
#         response = normal_requests.post(f'{base_url}{endpoint}', json=data)
#         response.raise_for_status()
#         return response.json()
#     except normal_requests.exceptions.RequestException as e:
#         print(f"Error sending request: {e}")
#         return None

def send_task_to_GPU_Manager(file_path, folder_name, export_mesh):
    # 从配置表获取GPU_Manager服务器地址
    base_url = task_serve_url

    # Test case with project_id and video_path parameters
    data = {"file_path": file_path, "folder_name": folder_name, "export_mesh": export_mesh}
    endpoint = '/add_task'

    try:
        logging.info(f"正在连接GPU服务器: {base_url}")
        response = normal_requests.post(f'{base_url}{endpoint}', json=data, timeout=5)
        response.raise_for_status()
        logging.info("GPU服务器连接成功")
        return response.json()
    except normal_requests.exceptions.ConnectionError:
        error_msg = f"无法连接到GPU服务器 {base_url}"
        logging.error(error_msg)
        return {"error": "GPU服务器未启动或无法访问"}
    except normal_requests.exceptions.RequestException as e:
        error_msg = f"请求错误: {e}"
        logging.error(error_msg)
        return {"error": f"请求失败: {str(e)}"}


# 连接数据库储存上传的数据初始化
def save_to_database(filename,projcet_name,privacy,user_name,user_id,export_mesh):
    conn = get_db_connection(database_path)
    cursor = conn.cursor()

    # 获取服务器时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 定义要插入的数据，注意"Queue"这个值在前端页面有引用
    color = "0.0,0.0,0.0,1.0"
    project_data = (filename, current_time, user_name, projcet_name, privacy, 0, "Queue", 0, 0, 0, user_id, color, "", "0", 0, "0", 0, 0, 0, 0, 0, 0, 0, "0.0, 0.0, 0.0", "1.0, 1.0, 1.0", "0.0, 0.0, 0.0", export_mesh)
    # SQL语句向项目表中插入数据
    insert_query = '''
        INSERT INTO project (
            project_name, 
            project_date, 
            project_user, 
            project_title, 
            project_public, 
            project_state, 
            project_progress,
            project_edit,
            project_down_num,
            project_like_num,
            project_user_id,
            project_color,
            nerfacto_config_path,
            nerfacto_progress,
            nerfacto_status,
            export_obj_progress,
            export_obj_state,
            export_gltf_state,
            export_fbx_state,
            export_ply_state,
            export_3ds_state,
            export_x_state,
            export_stl_state,
            CropPosition,
            CropScale,
            CropRotation,
            export_mesh
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    # 执行SQL语句插入数据
    cursor.execute(insert_query, project_data)

    conn.commit()
    conn.close()