# 作者: Ning
# 文件名: main.py
# 描述: 平台页面服务。
# 版本: 1.0.0
# 最后修改日期: 2024-01-24

import os,subprocess,random,string,sqlite3,json,re,toml,threading,logging
from flask import Flask, request, jsonify,render_template,redirect, url_for,session
from flask_cors import CORS
from flask_socketio import SocketIO, send
from datetime import datetime
# 解决与google requests的冲突
import requests as normal_requests

# google登录接口
from google.oauth2 import id_token
from google.auth.transport import requests
from flask import send_file

GOOGLE_OAUTH2_CLIENT_ID = 'xxxx'
GOOGLE_OAUTH2_TOKEN = 'xxx'

app = Flask(__name__, static_folder='templates', static_url_path='')
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = '890831'  # 用于加密 SocketIO 通信，替换为一个安全的密钥
socketio = SocketIO(app)

# 读取 TOML 文件
with open('config.toml', 'r') as file:
    toml_data = toml.load(file)

# 获取 TOML 字段值
CloudStorage = toml_data.get('servers', {}).get('upload_folder', {}).get('http')
updata_url = toml_data.get('servers', {}).get('updata_url', {}).get('http')
edit_url = toml_data.get('servers', {}).get('edit_url', {}).get('http')
task_serve_url = toml_data.get('servers', {}).get('task_serve', {}).get('http')
server_port = toml_data.get('servers', {}).get('home_port', {}).get('port')
database_path = toml_data.get('servers', {}).get('database', {}).get('path')

ALLOWED_EXTENSIONS = {'mp4', 'mov'}

# 在文件开头配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 生成带日期和随机数字的文件夹名
def generate_folder_name():
    current_date = datetime.now().strftime("%Y%m%d")
    random_digits = ''.join(random.choices(string.digits, k=4))
    folder_name = f"{current_date}_{random_digits}"
    return folder_name

# 检查文件扩展名是否合法
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 上传事件增加多线程处理与等待回调
@app.route('/upload', methods=['POST'])
def upload_file():

    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                raise Exception({'error': '未选择文件'})

            file = request.files['file']

            if file.filename == '':
                raise Exception({'error': '文件名为空'})

            if not allowed_file(file.filename):
                raise Exception({'error': '不支持的文件格式'})

            # 这里修改为分布式云储存路径
            upload_folder = CloudStorage
            folder_name = generate_folder_name()
            folder_path = os.path.join(upload_folder, folder_name)

            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            file_path = os.path.join(folder_path, file.filename)
            file.save(file_path)

            file_path = os.path.normpath(file_path)
            
            # 获取用户自定义名称
            name = request.form.get('name')
            # 获取用户信息
            privacy = request.form.get('input_privacy')
            # 获取用户信息
            user_name = request.form.get('user_name')
            # 获取用户信息
            user_id = request.form.get('user_id')
             # 获取是否计算mesh
            export_mesh = request.form.get('export_mesh')

            if name:
                # 调用保存到数据库的函数
                save_to_database(folder_name, name ,privacy,user_name,user_id,export_mesh)
            else:
                # 调用保存到数据库的函数
                save_to_database(folder_name,'default',privacy,user_name,user_id,export_mesh)

            # 使用回调从线程获取状态
            # status_callback = StatusCallback()
            # thread = FFMpegThread(target=run_ffmpeg, args=(folder_path, file_path, folder_name, status_callback))
            # thread.start()

            # 等待线程完成
            # thread.join()

            # 从回调中获取状态
            # status = status_callback.get_status()
            
            # 请求GPU_Manager��务器进行运算
            send_task_to_GPU_Manager(file_path, folder_name, export_mesh)

            # 继续执行回调
            return jsonify({"folder_path": folder_path, "file_path": file_path, "folder_name": folder_name, "status": True})

    except Exception as e:
        return jsonify({'error': str(e)})

# 请求GPU_Manager服务器进行运算
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

# 响应页面获发送nerf计算事件到分发路由
@app.route('/send_nerftask_ByID', methods=['POST'])
def send_nerftask_to_GPU_Manager():
    base_url = task_serve_url
    data = request.get_json()
    id_parameter = data.get('id')

    logging.info(f"收到任务请求，ID: {id_parameter}")
    
    data = {"folder_name": id_parameter}
    endpoint = '/add_nerfact'

    try:
        logging.info(f"正在发送请求到GPU服务器: {base_url}")
        response = normal_requests.post(f'{base_url}{endpoint}', json=data, timeout=5)
        response.raise_for_status()
        logging.info("请求发送成功")
        return response.json()
    except normal_requests.exceptions.ConnectionError:
        error_msg = f"无法连接到GPU服务器 {base_url}"
        logging.error(error_msg)
        return jsonify({"error": "GPU服务器未启动或无法访问"}), 503
    except normal_requests.exceptions.RequestException as e:
        error_msg = f"请求错误: {e}"
        logging.error(error_msg)
        return jsonify({"error": f"请求失败: {str(e)}"}), 500
    
# 从ID获取file_path
def Get_configPath_By_ID(ID):
    # 连接到数据库
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 查询语句
    query = "SELECT nerfacto_config_path FROM project WHERE project_name = ?"

    # 执行查询
    cursor.execute(query, (ID,))
    result = cursor.fetchone()

    # 关闭数据库连接
    conn.close()

    # 如果查询结果为空,则返回None,否则返回type值
    if result:
        return result[0]
    else:
        return None

# 从ID获取CROPinfo
def Get_Crop_Info_By_ID(ID):
    # 连接到数据库
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 查询语句
    query = "SELECT CropPosition, CropScale, CropRotation FROM project WHERE project_name = ?"

    # 执行查询
    cursor.execute(query, (ID,))
    result = cursor.fetchone()

    # 关闭数据库连接
    conn.close()

    # 如果查询结果为空,则返回None,否则返回CropPosition和CropScale的值
    if result:
        crop_position, crop_scale, crop_rotation = result
        return crop_position, crop_scale, crop_rotation
    else:
        return None, None, None

# 发送ExportTask事件请求事件分发路由
@app.route('/ExportTask', methods=['POST'])
def send_ExportTask_to_GPU_Manager():

    # 获取前端传递的JSON数据
    data = request.get_json()

    # 提取ID参数
    folder_name = data.get('id')

    # 获取CROPinfo
    crop_position, crop_scale, CropRotation= Get_Crop_Info_By_ID(folder_name)

    # 获取ConfigPath值
    configPath = Get_configPath_By_ID(folder_name)

    # 从配置表获取GPU_Manager服务器地址
    base_url = task_serve_url

    # Test case with project_id and video_path parameters
    data = {"folder_name": folder_name, "configPath": configPath,"CropPosition": crop_position, "CropScale": crop_scale, "CropRotation": CropRotation}
    endpoint = '/add_ExportTask'

    try:
        response = normal_requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()
        return response.json()
    except normal_requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None

# 发送ExportFormat转换事件请求事件分发路由
@app.route('/ExportFormatTask', methods=['POST'])
def send_ExportFormatTask_to_GPU_Manager():

    # 获取前端传递的JSON数据
    data = request.get_json()

    # 提取ID参数
    folder_name = data.get('id')
    Format_type = data.get('type')

    # 获取ConfigPath值
    configPath = Get_configPath_By_ID(folder_name)

    # 从配置表获取GPU_Manager服务器地址
    base_url = task_serve_url

    # Test case with project_id and video_path parameters
    data = {"folder_name": folder_name, "configPath": configPath, "Format_type": Format_type}
    endpoint = '/add_ExportFormatTask'

    try:
        response = normal_requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()
        return response.json()
    except normal_requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None

# 连接数据库储存上传的数据初始化
def save_to_database(filename,projcet_name,privacy,user_name,user_id,export_mesh):
    conn = sqlite3.connect(database_path)
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

# 更新指定ID进度数据
def updataProgress(project_name,new_progress):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # SQL语句更新数据
    update_query = '''
        UPDATE project
        SET project_progress = ?
        WHERE project_name = ?
    '''

    # 执行SQL语句更新数据
    cursor.execute(update_query, (new_progress, project_name))
    conn.commit()
    conn.close()

# 更新指定ID splatfacto训练状态为完成
@app.route('/updataProjectState', methods=['POST'])
def updataProjectState():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')

        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句更新数据
        update_query = '''
            UPDATE project
            SET project_state = ?
            WHERE project_name = ?
        '''

        # 执行SQL语句更新数据
        cursor.execute(update_query, (1, id_parameter))
        conn.commit()
        conn.close()

        response_data = {'message': '数据训练完成', 'id': id_parameter}
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})

# 更新指定ID nerfacto训练状态为完成
@app.route('/updataNerfactoState', methods=['POST'])
def updataNerfactoState():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')

        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句更新数据
        update_query = '''
            UPDATE project
            SET nerfacto_status = ?
            WHERE project_name = ?
        '''

        # 执行SQL语句更新数据
        cursor.execute(update_query, (1, id_parameter))
        conn.commit()
        conn.close()

        response_data = {'message': '数据训练完成', 'id': id_parameter}
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})

# 更新指定ID OBJ状态为完成
@app.route('/updataExportObjState', methods=['POST'])
def updataExportObjState():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')

        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句更新数据
        update_query = '''
            UPDATE project
            SET export_obj_state = ?
            WHERE project_name = ?
        '''

        # 执行SQL语句更新数据
        cursor.execute(update_query, (1, id_parameter))
        conn.commit()
        conn.close()

        response_data = {'message': '数据训练完成', 'id': id_parameter}
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})

# 更新指定ID Format状态为完成
@app.route('/updataExportFormatState', methods=['POST'])
def updataExportFormatState():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')
        format = data.get('format')

        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 定义需要更新的字段
        update_fields = {
            'gltf': 'export_gltf_state',
            'obj': 'export_obj_state',
            'fbx': 'export_fbx_state',
            '3ds': 'export_3ds_state',
            'x': 'export_x_state',
            'stl': 'export_stl_state',
            # 继续添加其他格式和对应字段
        }

        # 确保传入的格式是在定义的字段中
        if format not in update_fields:
            raise ValueError("Unsupported format")

        # 构建更新的字段名
        update_field = update_fields[format]

        # 构建更新的SQL语句
        update_query = f'''
            UPDATE project
            SET {update_field} = ?
            WHERE project_name = ?
        '''

        # 执行更新SQL语句
        cursor.execute(update_query, (1, id_parameter))
        conn.commit()

        conn.close()

        response_data = {'message': '数据转换完成', 'id': id_parameter}
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})

# 重置指定ID Format状态
@app.route('/resetExportFormatState', methods=['POST'])
def resetExportFormatState():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')
        format = 'obj'

        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 定义需要更新的字段
        update_fields = {
            'gltf': 'export_gltf_state',
            'obj': 'export_obj_state',
            'fbx': 'export_fbx_state',
            '3ds': 'export_3ds_state',
            'x': 'export_x_state',
            'stl': 'export_stl_state',
            # 继续添加其他格式和对应字段
        }

        # 确保传入的格式是在定义的字段中
        if format not in update_fields:
            raise ValueError("Unsupported format")

        # 构建更新的字段名
        update_field = update_fields[format]

        # 构建更新的SQL语句
        update_query = f'''
            UPDATE project
            SET {update_field} = ?
            WHERE project_name = ?
        '''

        # 执行更新SQL语句
        cursor.execute(update_query, (0, id_parameter))
        conn.commit()

        conn.close()

        response_data = {'message': '数据转换完成', 'id': id_parameter}
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})


# 添加指定ID NerfactoConfig_Path
@app.route('/NerfactoConfig_Path', methods=['POST'])
def NerfactoConfig_Path():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')
        Config_Path = data.get('path')

        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句更新数据
        update_query = '''
            UPDATE project
            SET nerfacto_config_path = ?
            WHERE project_name = ?
        '''

        # 执行SQL语句更新数据
        cursor.execute(update_query, (Config_Path, id_parameter))
        conn.commit()
        conn.close()

        response_data = {'message': 'config_path', 'id': id_parameter}
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})

# 更新指定ID splatfacto进度状态
@app.route('/updataProjectProgress', methods=['POST'])
def updataProjectProgress():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')
        progressVal = data.get('progressVal')

        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句更新数据
        update_query = '''
            UPDATE project
            SET project_progress = ?
            WHERE project_name = ?
        '''

        # 执行SQL语句更新数据
        cursor.execute(update_query, (progressVal, id_parameter))
        conn.commit()
        conn.close()

        response_data = {'message': '数据训练100%', 'id': id_parameter}
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})

# 更新指定ID nerfacto进度状态
@app.route('/updataNerfactoProgress', methods=['POST'])
def updataNerfactoProgress():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')
        progressVal = data.get('progressVal')

        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句更新数据
        update_query = '''
            UPDATE project
            SET nerfacto_progress = ?
            WHERE project_name = ?
        '''

        # 执行SQL语句更新数据
        cursor.execute(update_query, (progressVal, id_parameter))
        conn.commit()
        conn.close()

        response_data = {'message': '数据训练100%', 'id': id_parameter}
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})
   
# 更新指定ID ExportObj进度状态
@app.route('/updataExportObjProgress', methods=['POST'])
def updataExportObjProgress():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')
        progressVal = data.get('progressVal')

        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句更新数据
        update_query = '''
            UPDATE project
            SET export_obj_progress = ?
            WHERE project_name = ?
        '''

        # 执行SQL语句更新数据
        cursor.execute(update_query, (progressVal, id_parameter))
        conn.commit()
        conn.close()

        response_data = {'message': '数据训练100%', 'id': id_parameter}
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})

# 更新CROP矩阵数据
@app.route('/updataCropPositionAndScale', methods=['POST'])
def updataCropPositionAndScale():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')

        # 提取CropPosition和CropScale参数
        crop_position = data.get('CropPosition')
        crop_scale = data.get('CropScale')
        crop_rotation = data.get('CropRotation')

        print(crop_position)
        print(crop_scale)
        print(crop_rotation)

        # 连接数据库
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句更新项目表中的CropPosition和CropScale字段数据
        update_query = '''
            UPDATE project
            SET CropPosition = ?,
                CropScale = ?,
                CropRotation = ?
            WHERE project_name = ?
        '''

        # 执行SQL语句更新数据
        cursor.execute(update_query, (crop_position, crop_scale, crop_rotation, id_parameter))

        conn.commit()
        conn.close()

        # 返回成功消息
        response_data = {'message': 'Crop矩阵写入成功', 'id': id_parameter}
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})

# 查询CROP矩阵接口
@app.route('/get_crop_position_and_scale', methods=['POST'])
def get_crop_position_and_scale():
    try:
        # 连接到数据库
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取项目名称参数
        project_name = data.get('id')

        # SQL语句查询指定project_name的CropPosition和CropScale
        select_query = '''
            SELECT CropPosition, CropScale, CropRotation
            FROM project
            WHERE project_name = ?
        '''

        # 执行SQL语句查询数据
        cursor.execute(select_query, (project_name,))
        result = cursor.fetchone()  # 获取一行结果

        crop_position, crop_scale, crop_rotation = result

        # 关闭数据库连接
        conn.close()

        # 返回查询到的CropPosition和CropScale值
        return jsonify({'status': 'success', 'message': json.dumps({"CropPosition": crop_position, "CropScale": crop_scale, "CropRotation": crop_rotation})})

    except Exception as e:
        return jsonify({'error': str(e)})

# 更新指定ID编辑状态
def updataProjectEditorState(project_name,new_State):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # SQL语句更新数据
    update_query = '''
        UPDATE project
        SET project_edit = ?
        WHERE project_name = ?
    '''

    # 执行SQL语句更新数据
    cursor.execute(update_query, (new_State, project_name))
    conn.commit()
    conn.close()

# 更新指定ID背景色数值
def updataProjectBgColor(project_name,new_color):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # SQL语句更新数据
    update_query = '''
        UPDATE project
        SET project_color = ?
        WHERE project_name = ?
    '''

    # 执行SQL语句更新数据
    cursor.execute(update_query, (new_color, project_name))
    conn.commit()
    conn.close()

# 更新指定ID点赞数量
def incrementProjectLikeNum(project_name):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 从数据库中获取当前 project_like 的值
    select_query = '''
        SELECT project_like_num
        FROM project
        WHERE project_name = ?
    '''
    cursor.execute(select_query, (project_name,))
    current_like_num = cursor.fetchone()

    if current_like_num is not None:
        current_like_num = current_like_num[0]
        # 将 project_like 加1
        new_like_num = current_like_num + 1

        # 更新数据库中的 project_like 值
        update_query = '''
            UPDATE project
            SET project_like_num = ?
            WHERE project_name = ?
        '''
        cursor.execute(update_query, (new_like_num, project_name))
        conn.commit()
    else:
        # 处理未找到项目的情况，例如抛出异常或返回错误信息
        print(f"项目 '{project_name}' 不存在")

    conn.close()

# 正则表达式过滤命令行进度字符
def extract_percentage(progress_string):
    # 使用正则表达式匹配百分比
    match = re.search(r'(\d+)%', progress_string)
    
    if match:
        percentage = int(match.group(1))
        return f"{percentage}%"  # 将百分比转换为字符串
    else:
        return None
    
# 定义页面路由-首页
@app.route('/')
def index():
    # user_id = request.args.get('user_id', None)
    # username = request.args.get('username', None)
    # return render_template('home.html', user_id=user_id, username=username)
    # return app.send_static_file('Home.html')

    # 检查用户是否已登录
    if 'user_id' in session and 'username' in session:
        user_id = session['user_id']
        return render_template('home.html', user_id=user_id, username=session['username'])

    else:
        # 用户未登录，重定向到登录页面
        # return render_template('Login.html')
        # 用户未登录，不显示用户名但正常查看
        return render_template('home.html')

# 提取邮箱的 @ 之前的部分作为用户名
def extract_username_from_email(email):
    return email.split('@')[0]

# 登录页面-（修改字段时记得同步修改google接口）
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 从数据库中检查用户信息
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password, review FROM user WHERE username=?', (username,))
        user = cursor.fetchone()
        
        if user:
            user_id, username, stored_password, review = user
            # 检查审核状态
            if review == 0:
                return render_template('Login.html', error = '内测账号审核中，请耐心等待')
                return jsonify({'error': '账号待审核，请耐心等待'}), 400
            elif review == 1:
                # 检查密码是否匹配
                if password == stored_password:
                    # 登录成功，将用户信息存储到Session中
                    session['user_id'] = user_id
                    session['username'] = username
                    # 重定向到首页
                    user_id = session['user_id']
                    return redirect(url_for('index'))
                    return jsonify({'success': True}), 200
                else:
                    return render_template('Login.html', error = '密码错误，请检查后重试')
                    return jsonify({'error': '密码错误，请检查'}), 400
            else:
                return render_template('Login.html', error = '审核状态异常，请联系管理员')
                return jsonify({'error': '审核状态异常，请联系管理员'}), 400
        else:
            return render_template('Login.html', error = '用户名不存在，请检查后重试')
            return jsonify({'error': '用户不存在'}), 400

# 登录页面路由
@app.route('/loginPage')
def loginPage():
    return render_template('Login.html')

# 注册账号
@app.route('/Register', methods=['GET', 'POST'])
def Register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            return render_template('Register.html', error = '用户名或密码不能为空')
            return jsonify({'error': '用户名或密码不能为空'}), 400
        
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 检查用户是否存在
        cursor.execute('SELECT id FROM user WHERE username=?', (username,))
        user = cursor.fetchone()

        if user:
            # 用户已存在
            return render_template('Register.html', error = '用户已存在')
            return jsonify({'error': '用户已存在'}), 400
        else:
            # 注册用户
            cursor.execute('INSERT INTO user (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            # 注册成功
            return jsonify({'success': True}), 200

    return render_template('Register.html')

# 注册账号页面路由
@app.route('/RegisterPage')
def RegisterPage():
    return render_template('Register.html')

# google接口
@app.route('/google', methods=['GET', 'POST'])
def handle_id_token():
    # 尝试使用Google登录
    csrf_token_cookie = request.form.get('credential')
    try:
        idinfo = id_token.verify_oauth2_token(csrf_token_cookie, requests.Request(), GOOGLE_OAUTH2_CLIENT_ID)
        google_id = idinfo['sub']
        email = idinfo['email']

        # 检查本地数据库是否已存在与当前Google邮箱相匹配的用户
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user WHERE email=?', (email,))
        local_user = cursor.fetchone()

        if local_user:
            # 本地数据库中已存在与当前Google邮箱相匹配的用户，直接进行本地登录
            user_id, username = local_user[0], local_user[1]

            # 登录成功，将用户信息存储到Session中
            session['user_id'] = user_id
            session['username'] = username

            return redirect(url_for('index'))

        else:
            # Google用户在数据库中未注册，将其信息插入数据库
            username_from_email = extract_username_from_email(email)
            cursor.execute('INSERT INTO user (username, google_id, email) VALUES (?, ?, ?)', (username_from_email, google_id, email))
            conn.commit()

            # 获取插入后的用户信息
            cursor.execute('SELECT id, username FROM user WHERE email=?', (email,))
            new_user = cursor.fetchone()
            user_id, username = new_user[0], new_user[1]

            # 登录成功，将用户信息存储到Session中
            session['user_id'] = user_id
            session['username'] = username
            
            return redirect(url_for('index'))

    except ValueError as e:
        # ID Token verification failed
        error = 'Invalid credentials. Please try again.'
        return render_template('login.html', error=error)
    finally:
        conn.close()

# 用户退出
@app.route('/logout', methods=['GET'])
def logout():
    # 清除会话信息
    session.clear()
    return render_template('Login.html')

# 测试事件-前端激活打印路径
@app.route('/test', methods=['POST'])
def handle_frontend_event():
    data = request.get_json()
    event_name = data.get('event', 'default_event')

    # 在这里处理接收到的事件
    print(f'Received event from frontend: {event_name}')

    # 获取当前脚本所在的目录路径
    current_directory = os.getcwd()
    convert_path = os.path.join(current_directory,'3DTools')

    # 返回响应给前端
    return jsonify({'status': 'success', 'message': convert_path})

# SocketIO 连接事件
@socketio.on('connect', namespace='/test')
def test_connect():
    send('Connected')

# 全局刷新页面与数据
@socketio.on('Refresh_global_data', namespace='/test')
def Refresh_global_data():
    # 连接到数据库
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 执行查询
    cursor.execute('SELECT * FROM project')
    projects = cursor.fetchall()

    # 关闭数据库连接
    conn.close()

    # 发送数据到前端，包括数据服务器地址
    socketio.emit('update_data', json.dumps({"projects": projects, "updata_http": updata_url, "edit_http": edit_url}), namespace='/test')


@app.route('/get_data', methods=['POST'])
def GetData_request():
    try:
        # 从请求体中获取参数
        data = request.get_json()
        page = int(data.get('page', 1))  # 默认为 1 并转换为整数
        search = data.get('search', '')  # 获取搜索关键词，默认为空字符串

        MyCaptures_per_page = 18  # 每页个人项目显示的项目数量
        Explore_per_page = 20  # 每页探索项目显示的项目数量
        start = (page - 1) * MyCaptures_per_page
        user_id = session.get('user_id')

        # 连接到数据库
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 构建 SQL 查询语句，根据搜索关键词过滤项目数据，同时根据当前用户 id 过滤项目数据，按更新时间降序排列
        user_query = '''
            SELECT * FROM project 
            WHERE project_user_id = ? 
            AND project_title LIKE ? 
            ORDER BY project_id DESC 
            LIMIT ? OFFSET ?'''
        other_query = '''
            SELECT * FROM project 
            WHERE project_user_id != ? 
            AND project_title LIKE ? 
            ORDER BY project_id DESC 
            LIMIT ?'''

        # 执行查询，根据当前用户 id 过滤项目数据，按更新时间降序排列
        cursor.execute(user_query, (user_id, f'%{search}%', MyCaptures_per_page, start))
        user_projects = cursor.fetchall()

        # 获取其他项目数据，不匹配当前用户 id 的项目，按更新时间降序排列
        cursor.execute(other_query, (user_id, f'%{search}%', Explore_per_page))
        other_projects = cursor.fetchall()

        # 获取当前用户的项目总数
        cursor.execute('SELECT COUNT(*) FROM project WHERE project_user_id = ? AND project_title LIKE ?', (user_id, f'%{search}%'))
        user_project_count = cursor.fetchone()[0]

        # 获取其他项目的总数
        cursor.execute('SELECT COUNT(*) FROM project WHERE project_user_id != ? AND project_title LIKE ?', (user_id, f'%{search}%'))
        other_project_count = cursor.fetchone()[0]

        # 计算总页数
        total_user_pages = (user_project_count + MyCaptures_per_page - 1) // MyCaptures_per_page
        total_other_pages = (other_project_count + Explore_per_page - 1) // Explore_per_page
        totalPages = max(total_user_pages, total_other_pages)

        # 关闭数据库连接
        conn.close()

        # 返回响应给前端
        return jsonify({'status': 'success', 'message': json.dumps({"projects": user_projects, "otherProjects": other_projects, 'totalPages': totalPages, "updata_http": updata_url, "edit_http": edit_url})})

    except Exception as e:
        return jsonify({'error': str(e)})


# 响应页面获取指定ID进度的请求
@app.route('/get_dataByID', methods=['POST'])
def Get_project_progress():
    try:
        # 连接到数据库
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句查询指定project_name的project_progress
        select_query = '''
            SELECT project_progress, project_state
            FROM project
            WHERE project_name = ?
        '''

        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')

        # 执行SQL语句查询数据
        cursor.execute(select_query, (id_parameter,))
        result = cursor.fetchone()  # 获取一行结果

        project_progress, project_state = result

        # 关闭数据库连接
        conn.close()

        # 返回查询到的project_progress值
        return jsonify({'status': 'success', 'message': json.dumps({"project_progress": project_progress, "project_state": project_state})})

    except Exception as e:
        return jsonify({'error': str(e)})

# 响应页面获取指定ID Nerf进度的请求
@app.route('/get_NerfByID', methods=['POST'])
def Get_Nerf_progress():
    try:
        # 连接到数据库
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句查询指定project_name的nerfacto_progress
        select_query = '''
            SELECT nerfacto_progress, nerfacto_status
            FROM project
            WHERE project_name = ?
        '''

        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')

        # 执行SQL语句查询数据
        cursor.execute(select_query, (id_parameter,))
        result = cursor.fetchone()  # 获取一行结果

        nerfacto_progress, nerfacto_status = result

        # 关闭数据库连接
        conn.close()

        # 返回查询到的nerfacto_progress值
        return jsonify({'status': 'success', 'message': json.dumps({"nerfacto_progress": nerfacto_progress, "nerfacto_status": nerfacto_status})})

    except Exception as e:
        return jsonify({'error': str(e)})

# 响应页面获取指定ID ExportOBJ进度的请求
@app.route('/get_ExportOBJByID', methods=['POST'])
def Get_ExportOBJ_progress():
    try:
        # 连接到数据库
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句查询指定project_name的export_obj_progress
        select_query = '''
            SELECT export_obj_progress, export_obj_state
            FROM project
            WHERE project_name = ?
        '''

        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')

        # 执行SQL语句查询数据
        cursor.execute(select_query, (id_parameter,))
        result = cursor.fetchone()  # 获取一行结果

        export_obj_progress, export_obj_state = result

        # 关闭数据库连接
        conn.close()

        # 返回查询到的export_obj_progress值
        return jsonify({'status': 'success', 'message': json.dumps({"export_obj_progress": export_obj_progress, "export_obj_state": export_obj_state})})

    except Exception as e:
        return jsonify({'error': str(e)})

# 响应页面获取指定ID Export格式状态请求
@app.route('/get_ExportClassByID', methods=['POST'])
def get_ExportClassByID():
    try:
        # 连接到数据库
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 获取前端传递的 JSON 数据
        data = request.get_json()

        # 提取项目名称和导出类型参数
        project_name = data.get('project_name')
        export_type = data.get('export_type')

        export_state_column = {
            'obj': 'export_obj_state',
            'gltf': 'export_gltf_state',
            'fbx': 'export_fbx_state',
            'ply': 'export_ply_state',
            '3ds': 'export_3ds_state',
            'x': 'export_x_state',
            'stl': 'export_stl_state'
        }

        if export_type not in export_state_column:
            return jsonify({'status': 'error', 'message': f"Invalid export type: {export_type}"}), 400

        state_column = export_state_column[export_type]

        # SQL语句查询指定project_name的export
        select_query = f"SELECT {state_column} FROM project WHERE project_name = ?"

        # 执行SQL语句查询数据
        cursor.execute(select_query, (project_name,))
        result = cursor.fetchone()

        export_state = result[0]

        # 关闭数据库连接
        conn.close()

        # 返回查询到的export值
        return jsonify({'status': 'success', 'message': json.dumps({"export_Class_state": export_state})})

    except Exception as e:
        return jsonify({'error': str(e)})

# 响应页面获取指定ID的所有数据
@app.route('/get_dataviewByID', methods=['POST'])
def Get_projectByID():
    try:
        # 连接到数据库
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')

        # 如果 ID 参数为空,则返回或提供默认值
        if id_parameter is None:
            print('没有提供有效的 ID 参数')

        # 将 ID 参数转换为整数类型
        id_parameter = int(id_parameter)

        # SQL 查询语句
        select_query = '''
            SELECT * FROM project
            WHERE project_id = ?
        '''

        # 执行 SQL 查询语句
        cursor.execute(select_query, (id_parameter,))

        # 获取查询结果
        projects = cursor.fetchall()

        # 关闭数据库连接
        conn.close()

        # 返回查询到的project_progress值
        return jsonify({'status': 'success', 'message': json.dumps({"projects": projects, "updata_http": updata_url, "edit_http": edit_url})})

    except Exception as e:
        return jsonify({'error': str(e)})

# 修改后的文件保存
@app.route('/save', methods=['POST'])
def post_save_file():
    try:
        # 从请求中访问上传的文件和ID
        ply_file = request.files['plyFile']
        id_field = request.form['id']
        color = request.form['color']

        # 指定要保存文件的路径
        save_path = f'{CloudStorage}/{id_field}/edit/'  # Replace with your desired path

        # 检查目录如果不存在则先创建目录
        os.makedirs(save_path, exist_ok=True)

        # 将文件保存到指定路径
        ply_file.save(os.path.join(save_path, 'Editfile.ply'))

        # 修改数据库对应ID编辑状态
        updataProjectEditorState(id_field,1)

        # 修改数据库对应ID背景色
        updataProjectBgColor(id_field,color)

        return 'File saved successfully.'
    except Exception as e:
        return 'Error: ' + str(e)

# 根据ID删除项目 数据库
@app.route('/delete', methods=['POST'])
def post_delete_id_request():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')

        # 在这里处理你的业务逻辑，然后返回响应
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL语句删除项目表中指定project_name的数据
        delete_query = '''
            DELETE FROM project
            WHERE project_name = ?
        '''

        # 执行SQL语句删除数据
        cursor.execute(delete_query, (id_parameter,))

        conn.commit()
        conn.close()

        response_data = {'message': '删除数据成功', 'id': id_parameter}

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})

# 根据ID添加点赞 数据库
@app.route('/AddLike', methods=['POST'])
def post_add_like_request():
    try:
        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        id_parameter = data.get('id')

        # 在这里处理你的业务逻辑，然后返回响应
        incrementProjectLikeNum(id_parameter)
        response_data = {'message': '成功处理请求', 'id': id_parameter}

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)})
    
if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, debug=True,host='0.0.0.0', port=server_port)
