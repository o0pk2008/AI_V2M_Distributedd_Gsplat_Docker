# 作者: Ning
# 文件名: gpu_manager.py
# 描述: 平台计算的服务。
# 版本: 1.0.0
# 最后修改日期: 2024-03-26
# GPU可选状态：idle、busy、offline
# 任务可选状态：Waiting、Run、End

import os,sqlite3,toml,random,string,requests,asyncio,json,logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send
from flask_cors import CORS
from datetime import datetime
from threading import Thread

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='web', static_url_path='')
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = '890831'  # 用于加密 SocketIO 通信，替换为一个安全的密钥
socketio = SocketIO(app)

# 读取 TOML 文件
with open('config_modeling_serve.toml', 'r') as file:
    toml_data = toml.load(file)

# 获取 TOML 字段值
updata_url = toml_data.get('servers', {}).get('updata_url', {}).get('http')
edit_url = toml_data.get('servers', {}).get('edit_url', {}).get('http')
server_port = toml_data.get('servers', {}).get('GPU_Manager_Port', {}).get('port')
database_path = toml_data.get('servers', {}).get('database', {}).get('path')

command_Str_1 = toml_data.get('cmd', {}).get('convert', {}).get('command_Str_1')
command_Str_2 = toml_data.get('cmd', {}).get('convert', {}).get('command_Str_2')

# 查询可用的并且空闲的GPU
def get_available_gpu():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute('SELECT id, name, port FROM GpuServer WHERE status = "idle"')
    available_gpu = cursor.fetchone()

    conn.close()

    return available_gpu

# 查询所有GPU状态
@app.route('/get_gpu_servers', methods=['GET'])
def get_gpu_servers():
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 执行查询语句
        cursor.execute('SELECT * FROM GpuServer')

        # 获取查询结果
        data = cursor.fetchall()

        # 将结果转换为字典列表
        result = [{'id': row[0], 'name': row[1], 'port': row[2], 'status': row[3]} for row in data]

        conn.close()

        # 返回JSON格式的数据
        return jsonify({'gpu_servers': result})

    except Exception as e:
        return jsonify({'error': str(e)})

# 从任务列表中搜索有多少待计算任务
@app.route('/get_task_num', methods=['GET'])
def get_task_num():
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 查询数据库中status值为'Waiting'的数���总数量
        query = '''
            SELECT COUNT(*)
            FROM taskProject
            WHERE status = 'Waiting'
        '''
        cursor.execute(query)
        result = cursor.fetchone()[0]  # 获取第一列的值，即总数量

        conn.close()

        # 返回JSON格式的数据
        return jsonify({'task_num': result})

    except Exception as e:
        return jsonify({'error': str(e)})

# 从任务列表中搜索有多少已完成任务
@app.route('/get_taskEnd_num', methods=['GET'])
def get_taskEnd_num():
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 查询数据库中status值为'Waiting'的数据总数量
        query = '''
            SELECT COUNT(*)
            FROM taskProject
            WHERE status = 'End'
        '''
        cursor.execute(query)
        result = cursor.fetchone()[0]  # 获取第一列的值，即总数量

        conn.close()

        # 返回JSON格式的数据
        return jsonify({'taskEnd_num': result})

    except Exception as e:
        return jsonify({'error': str(e)})
    
# 标记GPU为忙碌状态
def mark_gpu_busy(gpu_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute('UPDATE GpuServer SET status = "busy" WHERE id = ?', (gpu_id,))
    conn.commit()

    conn.close()

# 标记GPU为空闲状态
def mark_gpu_available(gpu_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute('UPDATE GpuServer SET status = "idle" WHERE id = ?', (gpu_id,))
    conn.commit()

    conn.close()

# 连接数据库储存上传的数据初始化
def save_to_database(filename,project_id,export_mesh):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 获取服务器时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 定义要插入的数据
    project_data = (project_id, filename, current_time, '', 'Queue', 'Waiting', 0, 'train', '', '', '', '', export_mesh)
    # SQL语句向项目表中插入数据
    insert_query = '''
        INSERT INTO taskProject (
            project_id, 
            video_path, 
            start_time,
            finish_time,
            progress,
            status,
            finish,
            type,
            configPath,
            CropPosition,
            CropScale,
            CropRotation,
            export_mesh
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    # 执行SQL语句插入数据
    cursor.execute(insert_query, project_data)

    conn.commit()
    conn.close()

# 连接数据库储存上传的数据初始化Export
def save_to_Export_database(project_id,configPath,export_format,CropPosition,CropScale,CropRotation):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    #随机数字
    random_digits = ''.join(random.choices(string.digits, k=4))

    # 获取服务器时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 定义要插入的数据
    project_data = (f"{project_id}_{random_digits}", project_id, current_time, '', '', 'Waiting', 0, export_format, configPath, CropPosition, CropScale,CropRotation, '0')
    # SQL语句向项目表中插入数据
    insert_query = '''
        INSERT INTO taskProject (
            project_id, 
            video_path, 
            start_time,
            finish_time,
            progress,
            status,
            finish,
            type,
            configPath,
            CropPosition,
            CropScale,
            CropRotation,
            export_mesh
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    # 执行SQL语句插入数据
    cursor.execute(insert_query, project_data)

    conn.commit()
    conn.close()

# 接口:添加任务数据并开始执行
# 1.将请求加入队列数据库
# 2.任务列表中查找队列任务
# 3.向空闲GPU发起任务请求
@app.route('/add_task', methods=['POST'])
def add_task():

    # 获取请求中的参数 project_id 和 video_path
    # folder_path = request.json.get('folder_path')
    file_path = request.json.get('file_path')
    folder_name = request.json.get('folder_name')
    export_mesh = request.json.get('export_mesh')

    # 将请求加入队列数据库
    save_to_database(file_path, folder_name, export_mesh)

    # 在后台执行 run_task()，不等待其完成
    thread = Thread(target=run_task, args=())
    thread.start()

    # 请求加入数据库则返回成功
    return jsonify({'status': 'success'})

# 测试接口:添加一个export任务
@app.route('/add_ExportTask', methods=['POST'])
def add_ExportTask():

    # 获取请求中的参数 project_id 和 video_path
    folder_name = request.json.get('folder_name')
    configPath = request.json.get('configPath')
    CropPosition = request.json.get('CropPosition')
    CropScale = request.json.get('CropScale')
    CropRotation = request.json.get('CropRotation')

    # 将请求加入队列数据库
    save_to_Export_database(folder_name,configPath,"export",CropPosition,CropScale,CropRotation)

    # 在后台执行 run_task()，不等待其完成
    thread = Thread(target=run_task, args=())
    thread.start()

    # 请求加入数据库则返回成功
    return jsonify({'status': 'success'})

# 接口:添���一个CropTask任务
@app.route('/add_CropTask', methods=['POST'])
def add_CropTask():

    # 获取请求中的参数 project_id 和 video_path
    folder_name = request.json.get('folder_name')
    configPath = request.json.get('configPath')

    # 将请求加入队列数据库
    save_to_Export_database(folder_name,configPath,"crop",'','','')

    # 在后台执行 run_task()，不等待其完成
    thread = Thread(target=run_task, args=())
    thread.start()

    # 请求加入数据库则返回成功
    return jsonify({'status': 'success'})

# 接口:添加一个nerfact任务
@app.route('/add_nerfact', methods=['POST'])
def add_nerfact():

    # 获取请求中的参数 project_id 和 video_path
    folder_name = request.json.get('folder_name')

    # 将请求加入队列数据库
    save_to_Export_database(folder_name,'',"nerfact",'','','')

    # 在后台执行 run_task()，不等待其完成
    thread = Thread(target=run_task, args=())
    thread.start()

    # 请求加入数据库则返回成功
    return jsonify({'status': 'success'})

# 接口:添加一个exportFormat任务
@app.route('/add_ExportFormatTask', methods=['POST'])
def add_ExportFormatTask():

    # 获取请求中的参数 project_id 和 video_path
    folder_name = request.json.get('folder_name')
    configPath = request.json.get('configPath')
    format_type = request.json.get('Format_type')

    # 将请求加入队列数据库
    save_to_Export_database(folder_name,configPath,format_type,'','','')

    # 在后台执行 run_task()，不等待其完成
    thread = Thread(target=run_task, args=())
    thread.start()

    # 请求加入数据库则返回成功
    return jsonify({'status': 'success'})

# 从任务队列中获取任务并执行
@app.route('/run_task', methods=['POST'])
def run_task():
    logger.info("开始执行任务")

    # 从任务列表中查找队列任务
    earliest_waiting_task = get_earliest_waiting_task()

    # 如果存在未完成的任务则开始分配任务
    if earliest_waiting_task and len(earliest_waiting_task) > 0:
        logger.info("存在待计算任务")
        project_id, video_path, export_mesh = earliest_waiting_task
        logger.info(f"Earliest waiting task: Project ID - {project_id}, Video Path - {video_path}, export mesh - {export_mesh}")

         # 获取空闲的GPU
        available_gpu = get_available_gpu()
        
        if available_gpu is None:
            logger.info("没有可用GPU")
            # 如果没有可用GPU，直接返回状态信息，不使用jsonify
            return {'status': 'queue'}
        
        # 存在空闲GPU
        if available_gpu:
            gpu_id, gpu_name, gpu_port = available_gpu
            logger.info(gpu_id)
            # mark_gpu_busy(gpu_id)

            # 定义向空闲GPU发起任务请求
            send_task(gpu_port, project_id, video_path, export_mesh)
            logger.info("有空闲GPU进行计算.")
            return jsonify({'status': 'success'})

        # 没有空闲GPU
        else:
            logger.info("没有空闲GPU进行计算继续排队.")
            return jsonify({'status': 'queue'})

    # 任务均已完成
    else:
        logger.info("不存在待计算任务.")
        return jsonify({'status': 'null'})

# 定义向空闲GPU发起任务请求
def send_task(gpu_port,project_id,video_path, export_mesh):

    # 更新任务状态为Run
    updata_task_state('Run',project_id)

    # 向指定IP端口发送post请求
    base_url = f"http://127.0.0.1:{gpu_port}"

    # Test case with project_id and video_path parameters
    data = {'project_id': project_id, 'video_path': video_path, 'export_mesh': export_mesh}
    endpoint = '/start_GPU_task'

    try:
        response = requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending request: {e}", exc_info=True)
        return None

# GPU Work事件完成后回调数据
@app.route('/return_task', methods=['POST'])
def return_task():

    # 获取请求中的参数 project_id 和 video_path
    project_id = request.json.get('project_id')

    logger.info(f"计算完成{project_id}")
    # 继续查找队列任务,查看空闲GPU服务
    idle_GPU = run_task()

    # 返回当前项目状态 进行中 或 队列
    if idle_GPU:
        logger.info("继续计算下一个任务")
        return jsonify({'status': 'success'})
    else:
        logger.info("没有任务了")
        return jsonify({'status': 'queue'})

# 更新任务为状态
def updata_task_state(status,project_id):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute(f'UPDATE taskProject SET status = "{status}" WHERE project_id = ?', (project_id,))
    conn.commit()

    conn.close()

# 从任务列表中查找队列任务
def get_earliest_waiting_task():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 查询数据库中status值为'Waiting'的start_time最早的一条数据
    query = '''
        SELECT project_id, video_path, export_mesh
        FROM taskProject
        WHERE status = 'Waiting'
        ORDER BY start_time
        LIMIT 1
    '''
    cursor.execute(query)
    result = cursor.fetchone()

    conn.close()

    return result

# 定义页面路由-首页
@app.route('/')
def index():
    return app.send_static_file('index.html')

# 响应页面请求获取指定ID的训练进度
@app.route('/Get_ProgressByID', methods=['POST'])
def Get_ProgressByID():
    try:
        # 连接到数据库
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 获取前端传递的JSON数据
        data = request.get_json()

        # 提取ID参数
        project_id_to_query = data.get('id')

        # 执行查询
        cursor.execute("SELECT progress, status, finish FROM taskProject WHERE project_id = ?;", (project_id_to_query,))

        # 获取查询结果
        result = cursor.fetchone()
        
        # 处理查询结果
        progress, status, finish = result

        # 关闭数据库连接
        conn.close()

        # 返回查询到的project_progress值
        return jsonify({'status': 'success', 'message': json.dumps({"Progress": progress, "Status": status, "Finish": finish})})

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get_video_path', methods=['GET'])
def get_video_path():
    """
    根据项目 ID 获取视频路径
    """
    try:
        # 从查询参数中获取 project_id
        project_id = request.args.get('project_id')

        # 检查必要参数
        if not project_id:
            return jsonify({"error": "Missing required parameter 'project_id'"}), 400

        # 查询数据库获取视频路径
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 查询语句
        query = "SELECT video_path FROM taskProject WHERE project_id = ?"
        cursor.execute(query, (project_id,))
        result = cursor.fetchone()

        # 关闭数据库连接
        conn.close()

        # 返回查询结果
        if result:
            return jsonify({"video_path": result[0]}), 200
        else:
            return jsonify({"error": "No video path found for the given project_id"}), 404

    except sqlite3.Error as db_error:
        return jsonify({"error": f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_project_type', methods=['GET'])
def get_project_type():
    """
    根据项目 ID 获取任务类型
    """
    try:
        # 从查询参数中获取 project_id
        project_id = request.args.get('project_id')

        # 检查必要参数
        if not project_id:
            return jsonify({"error": "Missing required parameter 'project_id'"}), 400

        # 查询数据库获取任务类型
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 查询语句
        query = "SELECT type FROM taskProject WHERE project_id = ?"
        cursor.execute(query, (project_id,))
        result = cursor.fetchone()

        # 关闭数据库连接
        conn.close()

        # 返回查询结果
        if result:
            return jsonify({"type": result[0]}), 200
        else:
            return jsonify({"error": "No task type found for the given project_id"}), 404

    except sqlite3.Error as db_error:
        return jsonify({"error": f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_config_path', methods=['GET'])
def get_config_path():
    """
    根据项目 ID 获取 configPath
    """
    try:
        # 从查询参数中获取 project_id
        project_id = request.args.get('project_id')

        # 检查必要参数
        if not project_id:
            return jsonify({"error": "Missing required parameter 'project_id'"}), 400

        # 查询数据库获取 configPath
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 查询语句
        query = "SELECT configPath FROM taskProject WHERE project_id = ?"
        cursor.execute(query, (project_id,))
        result = cursor.fetchone()

        # 关闭数据库连接
        conn.close()

        # 返回查询结果
        if result:
            return jsonify({"configPath": result[0]}), 200
        else:
            return jsonify({"error": "No configPath found for the given project_id"}), 404

    except sqlite3.Error as db_error:
        return jsonify({"error": f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_crop_info', methods=['GET'])
def get_crop_info():
    """
    根据项目 ID 获取 Crop 信息（CropPosition, CropScale, CropRotation）
    """
    try:
        # 从查询参数中获取 ID
        project_id = request.args.get('project_id')

        # 检查必要参数
        if not project_id:
            return jsonify({"error": "Missing required parameter 'project_id'"}), 400

        # 查询数据库获取 Crop 信息
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 查询语句
        query = "SELECT CropPosition, CropScale, CropRotation FROM taskProject WHERE project_id = ?"
        cursor.execute(query, (project_id,))
        result = cursor.fetchone()

        # 关闭数据库连接
        conn.close()

        # 返回查询结果
        if result:
            crop_position, crop_scale, crop_rotation = result
            return jsonify({
                "CropPosition": crop_position,
                "CropScale": crop_scale,
                "CropRotation": crop_rotation
            }), 200
        else:
            return jsonify({"error": "No crop info found for the given project_id"}), 404

    except sqlite3.Error as db_error:
        return jsonify({"error": f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_task_state', methods=['POST'])
def update_task_state():
    """
    更新任务状态（例如 'completed'，'in_progress'，'pending'）根据项目 ID
    """
    try:
        # 从请求中解析 JSON 数据
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON payload"}), 400

        # 获取传入的 project_id 和 status
        project_id = data.get('project_id')
        status = data.get('status')

        # 检查必要参数
        if not project_id or not status:
            return jsonify({"error": "Missing required fields 'project_id' or 'status'"}), 400

        # 更新任务状态
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 更新数据库中的任务状态
        cursor.execute('UPDATE taskProject SET status = ? WHERE project_id = ?', (status, project_id))
        conn.commit()

        # 关闭数据库连接
        conn.close()

        return jsonify({"message": "Task state updated successfully"}), 200

    except sqlite3.Error as db_error:
        return jsonify({"error": f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_task_finish', methods=['POST'])
def update_task_finish():
    """
    更新任务的 finish 状态（例如 'True' 或 'False'）根据项目 ID
    """
    try:
        # 从请求中解析 JSON 数据
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON payload"}), 400

        # 获取传入的 project_id 和 finish
        project_id = data.get('project_id')
        finish = data.get('finish')

        # 检查必要参数
        if not project_id or finish is None:
            return jsonify({"error": "Missing required fields 'project_id' or 'finish'"}), 400

        # 更新任务状态
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 更新数据库中的任务状态
        cursor.execute('UPDATE taskProject SET finish = ? WHERE project_id = ?', (finish, project_id))
        conn.commit()

        # 关闭数据库连接
        conn.close()

        return jsonify({"message": "Task finish state updated successfully"}), 200

    except sqlite3.Error as db_error:
        return jsonify({"error": f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_gpu_status', methods=['POST'])
def update_gpu_status():
    """
    更新指定 GPU 的状态（例如 'busy'、'idle' 或 'offline'）
    """
    try:
        # 从请求中解析 JSON 数据
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON payload"}), 400

        port = data.get('port')
        status = data.get('status')

        # 检查必要参数
        if port is None or status is None:
            return jsonify({"error": "Missing required fields 'port' or 'status'"}), 400

        # 验证状态值
        valid_statuses = ['busy', 'idle', 'offline']
        if status not in valid_statuses:
            return jsonify({"error": f"Invalid status value, must be one of {valid_statuses}"}), 400

        # 更新数据库中 GPU 的状态
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Enable WAL mode
        cursor.execute('PRAGMA journal_mode=WAL')

        # 执行更新操作
        update_query = '''
            UPDATE GpuServer
            SET status = ?
            WHERE port = ?
        '''
        cursor.execute(update_query, (status, port))
        conn.commit()
        conn.close()

        return jsonify({"message": f"GPU status updated to '{status}' successfully"}), 200

    except sqlite3.Error as db_error:
        return jsonify({"error": f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_progress', methods=['POST'])
def update_progress():
    """
    更新任务进度（progress）根据项目 ID
    """
    try:
        # 从请求中解析 JSON 数据
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON payload"}), 400

        # 获取传入的 project_id 和 progress
        project_id = data.get('project_id')
        progress = data.get('progress')

        # 检查必要参数
        if not project_id or progress is None:
            return jsonify({"error": "Missing required fields 'project_id' or 'progress'"}), 400

        # 更新任务进度
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 执行更新操作
        update_query = '''
            UPDATE taskProject
            SET progress = ?
            WHERE project_id = ?
        '''
        cursor.execute(update_query, (progress, project_id))
        conn.commit()

        # 关闭数据库连接
        conn.close()

        return jsonify({"message": "Task progress updated successfully"}), 200

    except sqlite3.Error as db_error:
        return jsonify({"error": f"Database error: {db_error}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=server_port)
