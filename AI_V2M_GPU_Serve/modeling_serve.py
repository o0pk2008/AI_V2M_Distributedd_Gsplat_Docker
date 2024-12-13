# 作者: Ning
# 文件名: modeling_serve.py
# 描述: 用于建模计算的服务。
# 版本: 1.0.0
# 最后修改日期: 2024-04-08
# GPU可选状态：idle、busy、offline

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, send
import os,subprocess,random,time,string,sqlite3,json,re,base64,toml,threading,socket,atexit,argparse,requests
# 硬件信息
import psutil,platform,datetime

# 导出文件
import zipfile

# 自动裁剪点云边框
import open3d as o3d
import numpy as np
import json

# 转fbx库
import os
import shutil
import pyassimp

# global
global_splatfacto_config_path = None

global_nerfacto_config_path = None

app = Flask(__name__, static_folder='web', static_url_path='')
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = '890831'
socketio = SocketIO(app)

# 读取 TOML 文件
with open('config_modeling_serve.toml', 'r') as file:
    toml_data = toml.load(file)

# 获取 TOML 字段值
upload_folder = toml_data.get('servers', {}).get('upload_folder', {}).get('http')
base_path = toml_data.get('servers', {}).get('upload_folder', {}).get('base_path')
updata_url = toml_data.get('servers', {}).get('updata_url', {}).get('http')
edit_url = toml_data.get('servers', {}).get('edit_url', {}).get('http')
GPU_Manager_url = toml_data.get('servers', {}).get('GPU_Manager_url', {}).get('http')
# database_path = toml_data.get('servers', {}).get('database', {}).get('path')

# 客户端服务器地址
Client_Service_url = toml_data.get('Client_Service', {}).get('url', {}).get('http')

command_Str_1 = toml_data.get('cmd', {}).get('convert', {}).get('command_Str_1')
command_Str_2 = toml_data.get('cmd', {}).get('convert', {}).get('command_Str_2')

ALLOWED_EXTENSIONS = {'mp4', 'mov'}
ffmpeg_status = ''  # 用于存储 ffmpeg 执行状态

# 生成带日期和随机数字的文件夹名
def generate_folder_name():
    current_date = datetime.now().strftime("%Y%m%d")
    random_digits = ''.join(random.choices(string.digits, k=4))
    folder_name = f"{current_date}_{random_digits}"
    return folder_name

# 检查文件扩展名是否合法
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# V2算法 run_colmap
def run_colmap(file_path,folder_name):

    global ffmpeg_status

    # 提取文件路径的目录部分
    global_updatadir_path = os.path.dirname(file_path)

    # 判断视频转换完成
    pattern_COLMAP_1 = "Done converting video to images"
    # 其他���骤
    pattern_COLMAP_2 = "Done extracting COLMAP features"
    pattern_COLMAP_3 = "Done matching COLMAP features"
    pattern_COLMAP_4 = "Done COLMAP bundle adjustment"
    pattern_COLMAP_5 = "Done refining intrinsics"

    # command = [
    #     'cmd', '/c', 'ns-process-data video ','--data=' + file_path ,'--output-dir=' + global_updatadir_path + '/sfm'
    # ]

    # 检测操作系统类型并相应调整命令
    if platform.system() == 'Windows':
        command = [
            'cmd', '/c', 
            f'conda activate nerfstudio && ns-process-data video --data={file_path} --output-dir={global_updatadir_path}/sfm'
        ]
    else:
        # Linux环境下的命令
        command = [
            '/bin/bash', '-c',
            f'source ~/miniconda3/etc/profile.d/conda.sh && conda activate nerfstudio && ns-process-data video --data={file_path} --output-dir={global_updatadir_path}/sfm'
        ]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # 读取子进程输出
        for line in iter(process.stdout.readline, ''):
            try:
                if isinstance(line, bytes):
                    string = line.decode('utf-8', errors='ignore').strip()
                else:
                    string = line.strip()
                
                # 调试LOG
                print('[' + datetime.datetime.now().strftime('%H:%M:%S') + '] ' + 'colmapLOG:' + string)

                if pattern_COLMAP_1 in string:
                    # 更新数据到数据库
                    call_update_progress(folder_name , "init 1/5")  
                    # 更新数据到[客户端]数据库
                    update_project_progress(folder_name,"init 1/5",Client_Service_url)
                    print("init 1/5")
                    # ffmpeg_status = 'ffmpeg执行完成'
                
                if pattern_COLMAP_2 in string:
                    # 更新数据到数据库
                    call_update_progress(folder_name , "init 2/5")  
                    # 更新数据到[客户端]数据库
                    update_project_progress(folder_name,"init 2/5",Client_Service_url)
                    print("init 2/5")

                if pattern_COLMAP_3 in string:
                    # 更新数据到数据库
                    call_update_progress(folder_name , "init 3/5")  
                    # 更新数据到[客户端]数据库
                    update_project_progress(folder_name,"init 3/5",Client_Service_url)
                    print("init 3/5")

                if pattern_COLMAP_4 in string:
                    # 更新数据到数据库
                    call_update_progress(folder_name , "init 4/5")  
                    # 更新数据到[客户端]数据库
                    update_project_progress(folder_name,"init 4/5",Client_Service_url)
                    print("init 4/5")

                if pattern_COLMAP_5 in string:
                    # 更新数据到数据库
                    call_update_progress(folder_name , "init 5/5")  
                    # 更新数据到[客户端]数据库
                    update_project_progress(folder_name,"init 5/5",Client_Service_url)
                    print("init 5/5")

                # 前端日志打印
                # socketio.emit('log', {'data': string})
            except UnicodeDecodeError:
                # 忽略无法解码的行
                pass
            except Exception as e:
                print(f"An error occurred: {e}")

        # 等待命令行窗口关闭
        process.wait()
        print(f'Done init')

    except Exception as e:
        # 处理异常
        print(f"An error occurred: {e}")
        ffmpeg_status = f'ffmpeg执行失败：{e}'

# V2算法 splatfacto 训练
def run_splatfacto(global_updatadir_path,folder_name,export_mesh):
    # 获取全局变量
    global global_splatfacto_config_path

    # command = [
    #     'cmd', '/c', 'ns-train', 'splatfacto-big', '--data=' + f'{global_updatadir_path}' + '/sfm'
    # ]

    # 检测操作系统类型并相应调整命令
    if platform.system() == 'Windows':
        command = [
            'cmd', '/c', 
            'call conda activate nerfstudio && ns-train splatfacto-big --data={}/sfm'.format(global_updatadir_path)
        ]
    else:
        command = [
            '/bin/bash', '-c',
            'source ~/miniconda3/etc/profile.d/conda.sh && conda activate nerfstudio && ns-train splatfacto-big --data={}/sfm'.format(global_updatadir_path)
        ]


    print(command)

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # List of encodings to try
        encodings = ['utf-8', 'gbk', 'big5', 'shift_jis', 'latin-1']

        # 初始化为0.0
        max_printed = 0.0

        # 正则表达式模式,匹配形如99.90%的字符串
        pattern = r'(\d+\.\d+%)' 

        # 匹配config.yml路径
        config_pattern = r'Config File \│\s*(outputs\\\\sfm\\\\splatfacto\\\\(\d{4}-\d{2}-\d{2}_\d{6})\\\\config\.yml)'

        for line in iter(process.stdout.readline, ''):
            decoded_line = None
            for encoding in encodings:
                try:
                    decoded_line = line.decode(encoding)
                    break
                except UnicodeDecodeError:
                    pass

            if decoded_line is None:
                # If none of the encodings worked, replace invalid bytes with a placeholder
                decoded_line = line.decode('utf-8', errors='replace')

            string = decoded_line.strip()

            # 调试LOG
            # print('[' + datetime.datetime.now().strftime('%H:%M:%S') + '] ' + 'splatLOG:' + string)

            # 筛选进度
            matches = re.findall(pattern, string)
            for match in matches:
                # 提取百分比数值
                percentage = float(match.strip('%'))
                # 判断数值不回滚
                if percentage > max_printed:
                    print(match)
                    # 更新splatfacto数据到数据库
                    call_update_progress(folder_name , match)  
                    # 更新splatfacto数据到[客户端]数据库
                    update_project_progress(folder_name,match,Client_Service_url)

                    max_printed = percentage

            # 尝试匹配config.yml路径
            if "config.yml" in string:
                start = string.find("outputs")
                end = string.find("│", start)
                global_splatfacto_config_path = string[start:end]
                print(global_splatfacto_config_path)

            # 检测运行完成跳出循环
            if "Use ctrl+c to quit" in string:
                process.terminate()
                break
            # 前端日志打印
            # socketio.emit('log', {'data': string})

        # 等待命令行窗口关闭
        process.wait()
        print(f'run_splatfacto完成')

        # 执行export PLY
        print(f'执行ns_export')

        run_ns_export(global_updatadir_path,folder_name,export_mesh)

    except Exception as e:
        # 处理异常
        print(f"An error occurred: {e}")
        # 您可以在此处添加其他异常处理代码,例如记录错误、发送通知等

# V2算法 ns-export 导出 ply
def run_ns_export(global_updatadir_path,folder_name,export_mesh):
    # 获取全局变量 文件与目录
    global global_splatfacto_config_path

    # 清除字符串两端空格
    global_splatfacto_config_path = global_splatfacto_config_path.strip()
    global_splatfacto_config_path = global_splatfacto_config_path.replace("\\", "/")
    global_updatadir_path = global_updatadir_path.replace("\\", "/")
    # command = [
    #     'cmd', '/c', 'ns-export gaussian-splat','--load-config' , global_splatfacto_config_path ,'--output-dir' , global_updatadir_path + '/'
    # ]
    if platform.system() == 'Windows':
        command = [
            'cmd', '/c', 
            'call conda activate nerfstudio && ns-export gaussian-splat --load-config {} --output-dir {}'.format(global_splatfacto_config_path, global_updatadir_path + '/')
        ]
    else:
        command = [
            '/bin/bash', '-c',
            'source ~/miniconda3/etc/profile.d/conda.sh && conda activate nerfstudio && ns-export gaussian-splat --load-config {} --output-dir {}'.format(global_splatfacto_config_path, global_updatadir_path + '/')
        ]


    print(command)
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # 等待命令行窗口关闭
        return_code = process.wait()

        if return_code == 0:
            print(f'ns-export完成')

            # 更新数据到数据库
            call_update_progress(folder_name , '100%')  
            # 更新数据到[客户端]数据库
            update_project_progress(folder_name,'100%',Client_Service_url)

            # 将当前任务finish状态到[客户端]数据库
            update_project_state(folder_name,Client_Service_url)

            print(f'任务结束')
            # 将当前任务状态
            call_update_task_state('End',folder_name)

            # 将当前任务finish状态到[任务]数据库 
            call_update_task_finish(1,folder_name)

            # 在任务完成后，标记此GPU为空闲
            call_update_gpu_status('idle')

            # 通知GPU Manager任务结束 执行下一个任务
            send_retrun_task(folder_name)

            
        else:
            print(f'train执行失败，返回码: {return_code}')  # 在执行失败时打印消息
            socketio.emit('update_output', {'output': f'train执行失败，返回码: {return_code}'}, namespace='/test')

    except Exception as e:
        # 处理异常
        print(f"An error occurred: {e}")
        # 您可以在此处添加其他异常处理代码,例如记录错误、发送通知等
        socketio.emit('update_output', {'output': f'发生错误：{e}'}, namespace='/test')

# 调用 get_video_path 获取项目视频路径
def call_get_video_path(project_id):
    """
    调用 get_video_path 接口，根据项目 ID 获取视频路径
    :param project_id: 项目 ID
    :return: 视频路径或 None
    """
    endpoint = 'get_video_path'
    base_url = GPU_Manager_url.rstrip('/')

    params = {
        "project_id": project_id
    }

    try:
        response = requests.get(f'{base_url}/{endpoint}', params=params)
        response.raise_for_status()
        
        # 从响应中提取 video_path
        result = response.json()
        if 'video_path' in result:
            return result['video_path']
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error sending request to get_video_path: {e}")
        return None

# 调用 get_project_type 获取任务类型
def call_get_project_type(project_id):
    """
    调用 get_project_type 接口，根据项目 ID 获取任务类型
    :param project_id: 项目 ID
    :return: 接口返回的任务类型或错误信息
    """
    # 拼接完整的 URL
    endpoint = '/get_project_type'
    base_url = GPU_Manager_url

    # 准备查询参数
    params = {
        "project_id": project_id
    }

    try:
        # 发送 GET 请求
        response = requests.get(f'{base_url}{endpoint}', params=params)
        response.raise_for_status()  # 如果发生 HTTP 错误，抛出异常
        return response.json()  # 返回 JSON 响应

    except requests.exceptions.RequestException as e:
        print(f"Error sending request to get_project_type: {e}")
        return None

# V2算法 执行 nerfacto 训练
# 在数据库记录sfm信息，实现异步执行 nerfacto 训练
def run_nerfacto(project_id):

    global global_nerfacto_config_path

    # 获取父任务ID
    parent_task_id = call_get_video_path(project_id)
    if parent_task_id is None:
        print("Error: Could not get parent task ID")
        return

    # 获取父任务视频路径
    video_path = call_get_video_path(parent_task_id)
    if video_path is None:
        print("Error: Could not get video path")
        return


    # 统一路径格式，将所有反斜杠转换为正斜杠
    video_path = video_path.replace('\\', '/')

    # 找到 AI_V2M_CloudStorage\uploads 之前的所有内容并替换
    video_path = video_path.replace(base_path, upload_folder)
    

    # 提取文件路径的目录部分
    folder_path = os.path.dirname(video_path)

    # 使用预测法线的网络设置训练 nerfacto
    # command = [
    #     'cmd', '/c', 'ns-train', 'nerfacto',
    #     '--data', f'{folder_path}\\sfm', '--pipeline.model.predict-normals', 'True'
    # ]

    if platform.system() == 'Windows':
        command = [
            'cmd', '/c', 
            'call conda activate nerfstudio && ns-train nerfacto --data {}\\sfm --pipeline.model.predict-normals True'.format(folder_path)
        ]
    else:
        command = [
            '/bin/bash', '-c',
            'source ~/miniconda3/etc/profile.d/conda.sh && conda activate nerfstudio && ns-train nerfacto --data {}/sfm --pipeline.model.predict-normals True'.format(folder_path)
        ]


    print(command)

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # List of encodings to try
        encodings = ['utf-8', 'gbk', 'big5', 'shift_jis', 'latin-1']

        # 初始化为0.0
        max_printed = 0.0

        # 正则表达式模式,匹配形如99.90%的字符串
        pattern = r'(\d+\.\d+%)' 

        # 匹配config.yml路径
        config_pattern = r'Config File \│\s*(outputs\\\\sfm\\\\nerfacto\\\\(\d{4}-\d{2}-\d{2}_\d{6})\\\\config\.yml)'

        for line in iter(process.stdout.readline, ''):
            decoded_line = None
            for encoding in encodings:
                try:
                    decoded_line = line.decode(encoding)
                    break
                except UnicodeDecodeError:
                    pass

            if decoded_line is None:
                # If none of the encodings worked, replace invalid bytes with a placeholder
                decoded_line = line.decode('utf-8', errors='replace')

            string = decoded_line.strip()

            # 调试LOG
            # print('[' + datetime.datetime.now().strftime('%H:%M:%S') + '] ' + 'splatLOG:' + string)

            # 筛选进度
            matches = re.findall(pattern, string)
            for match in matches:
                # 提取百分比数值
                percentage = float(match.strip('%'))
                # 判断数值不回滚
                if percentage > max_printed:
                    print(match)

                    # 更新Nerf数据到数据库
                    call_update_progress(project_id , match)  
                    # 更新Nerf数据到父任务ID[客户端]数据库
                    update_Nerfacto_progress(parent_task_id,match,Client_Service_url)

                    max_printed = percentage

            # 尝试匹配config.yml路径
            if "config.yml" in string:
                start = string.find("outputs")
                end = string.find("│", start)
                global_nerfacto_config_path = string[start:end]
                print(global_nerfacto_config_path)

                # 更新NerfactoConfig_Path到父任务ID[客户端]数据库
                update_NerfactoConfig_Path(parent_task_id,global_nerfacto_config_path,Client_Service_url)
                

            # 检测运行完成跳出循环
            if "Use ctrl+c to quit" in string:
                process.terminate()
                break
            # 前端日志打印
            # socketio.emit('log', {'data': string})

        # 等待命令行窗口关闭
        process.wait()
        print(f'run_nerfacto完成')

        # 执行pcd导出-提前导出pcd方便Export页面加载点云
        run_pcd_export(global_nerfacto_config_path,parent_task_id)

        # 更新Nerf数据到[客户端]数据库
        update_Nerfacto_progress(parent_task_id,'100%',Client_Service_url)
        
        # 更新Nerf完成状态到[客户端]数据库
        update_Nerfacto_state(parent_task_id,Client_Service_url)

        # 将当前任务状态
        call_update_task_state('End',project_id)

        # 将当前任务finish状态到[任务]数据库 
        call_update_task_finish(1,project_id)

        # 在任务完成后，标记此GPU为空闲
        call_update_gpu_status('idle')

        # 添加ExportOBJ任务 - 改为由客户端执行
        # print(f'执行ns_export')
        # send_ExportTask_to_GPU_Manager(global_nerfacto_config_path,folder_name)

        # 添加Crop边界计算任务
        print(f'执行Crop边界计算')
        send_CropTask_to_GPU_Manager(global_nerfacto_config_path,parent_task_id)

        # 通知GPU Manager任务结束 执行下一个任务
        send_retrun_task(project_id)

    except Exception as e:
        # 处理异常
        print(f"An error occurred: {e}")
        # 您可以在此处添加其他异常处理代码,例如记录错误、发送通知等

# 调用 get_config_path 获取 configPath
def call_get_config_path(project_id):
    """
    调用 get_config_path 接口，根据项目 ID 获取 configPath
    :param project_id: 项目 ID
    :return: 接口返回的 configPath 或错误信息
    """
    # 拼接完整的 URL
    endpoint = '/get_config_path'
    base_url = GPU_Manager_url

    # 准备查询参数
    params = {
        "project_id": project_id
    }

    try:
        # 发送 GET 请求
        response = requests.get(f'{base_url}{endpoint}', params=params)
        response.raise_for_status()  # 如果发生 HTTP 错误，抛出异常
        
        # 获取返回的 JSON 数据
        response_data = response.json()
        
        # 检查是否成功返回 configPath
        if 'configPath' in response_data:
            return response_data['configPath']
        else:
            print(f"Error: {response_data.get('error', 'Unknown error')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error sending request to get_config_path: {e}")
        return None

    
# 调用 get_crop_info 获取 Crop 信息
def call_get_crop_info(project_id):
    """
    调用 get_crop_info 接口，根据项目 ID 获取 Crop 信息
    :param project_id: 项目 ID
    :return: 接口返回的 Crop 信息（CropPosition, CropScale, CropRotation）或错误信息
    """
    # 拼接完整的 URL
    endpoint = '/get_crop_info'
    base_url = GPU_Manager_url

    # 准备查询参数
    params = {
        "project_id": project_id
    }

    try:
        # 发送 GET 请求
        response = requests.get(f'{base_url}{endpoint}', params=params)
        response.raise_for_status()  # 如果发生 HTTP 错误，抛出异常
        return response.json()  # 返回 JSON 响应

    except requests.exceptions.RequestException as e:
        print(f"Error sending request to get_crop_info: {e}")
        return None

# 打包目录到ZIP
def zip_directory(directory, zip_file):
    """
    压缩指定文件夹到一个ZIP文件中。

    参数:
        directory (str): 要压缩的文件夹路径。
        zip_file (str): 输出的ZIP文件路径。

    返回:
        无
    """
    # 创建一个新的ZIP文件对象，'w' 表示写入模式，zipfile.ZIP_DEFLATED 表示使用默认的压缩算法
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 使用 os.walk() 遍历文件夹中的所有文件和子文件夹
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                # 将文件添加到ZIP文件中，os.path.relpath() 用于获取相对路径
                zipf.write(file_path, os.path.relpath(file_path, directory))
            
# V2算法 执行cmd导出 obj
def run_obj_export(config,exportID,proID,bounding_box_center,bounding_box_scale,bounding_box_rotation,faces,use_bounding_box):
    # command = [
    #     'cmd', '/c', 'ns-export', 'poisson',
    #     '--load-config', config,
    #     '--output-dir', upload_folder + '/' + proID + '/mesh/',
    #     '--target-num-faces', faces,
    #     '--num-pixels-per-side', '2048',
    #     '--num-points', '1000000',
    #     '--remove-outliers', 'True',
    #     '--normal-method', 'open3d',
    #     '--use_bounding_box', use_bounding_box,
    #     '--obb_center', bounding_box_center[0], bounding_box_center[1], bounding_box_center[2],
    #     '--obb_rotation',  bounding_box_rotation[0], bounding_box_rotation[1], bounding_box_rotation[2],
    #     '--obb_scale', bounding_box_scale[0], bounding_box_scale[1], bounding_box_scale[2],
    #     # '--texture-method', 'point_cloud'
    # ]

    if platform.system() == 'Windows':
        command = [
            'cmd', '/c',
            'call', 'conda', 'activate', 'nerfstudio', '&&', 'ns-export', 'poisson',
            '--load-config', config,
            '--output-dir', os.path.join(upload_folder, proID, 'mesh'),
            '--target-num-faces', str(faces),
            '--num-pixels-per-side', '2048',
            '--num-points', '1000000',
            '--remove-outliers', 'True',
            '--normal-method', 'open3d',
            '--use_bounding_box', str(use_bounding_box),
            '--obb_center', f"{bounding_box_center[0]} {bounding_box_center[1]} {bounding_box_center[2]}",
            '--obb_rotation', f"{bounding_box_rotation[0]} {bounding_box_rotation[1]} {bounding_box_rotation[2]}",
            '--obb_scale', f"{bounding_box_scale[0]} {bounding_box_scale[1]} {bounding_box_scale[2]}",
        ]
    else:
        command = [
            '/bin/bash', '-c', 
            f'source ~/miniconda3/etc/profile.d/conda.sh && conda activate nerfstudio && ' + 
            f'ns-export poisson ' + 
            f'--load-config {config} ' + 
            f'--output-dir {os.path.join(upload_folder, proID, "mesh")} ' + 
            f'--target-num-faces {faces} ' + 
            '--num-pixels-per-side 2048 ' + 
            '--num-points 1000000 ' + 
            '--remove-outliers True ' + 
            '--normal-method open3d ' + 
            f'--use_bounding_box {use_bounding_box} ' + 
            f'--obb_center {bounding_box_center[0]} {bounding_box_center[1]} {bounding_box_center[2]} ' + 
            f'--obb_rotation {bounding_box_rotation[0]} {bounding_box_rotation[1]} {bounding_box_rotation[2]} ' + 
            f'--obb_scale {bounding_box_scale[0]} {bounding_box_scale[1]} {bounding_box_scale[2]}'
        ]



    print(command)  # 检查命令输出

    # 定义字符串和对应的初始化百分比
    mesh_progress = {
        "Cleaning Point Cloud": "10",
        "Estimating Point Cloud Normals": "20",
        "Generated PointCloud with": "30",
        "Computing Mesh this may take a while": "40",
        "Saving Mesh": "50",
        "Unwrapped mesh with xatlas method": "70",
        "All DONE": "80"
    }
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        # stdout, stderr = process.communicate()

        # print("STDOUT:", stdout.decode('utf-8'))
        # print("STDERR:", stderr.decode('utf-8'))

        # List of encodings to try
        encodings = ['utf-8', 'gbk', 'big5', 'shift_jis', 'latin-1']

        for line in iter(process.stdout.readline, ''):
            decoded_line = None
            for encoding in encodings:
                try:
                    decoded_line = line.decode(encoding)
                    break
                except UnicodeDecodeError:
                    pass

            if decoded_line is None:
                # If none of the encodings worked, replace invalid bytes with a placeholder
                decoded_line = line.decode('utf-8', errors='replace')

            string = decoded_line.strip()

            # 调试LOG
            # print('[' + datetime.datetime.now().strftime('%H:%M:%S') + '] ' + 'splatLOG:' + string)

            # 检查字符串是否存在于字典的键中
            if any(key in string for key in mesh_progress.keys()):
                # 找到匹配的键并打印对应的值
                for key, value in mesh_progress.items():
                    if key in string:
                        print(value)

                        # 更新obj数据到数据库
                        call_update_progress(exportID, value)

                        # 更新obj数据到[客户端]数据库
                        update_ExportObj_progress(proID,value,Client_Service_url)

                        # 退出当前的for循环
                        break

            # 检测运行完成跳出循环
            if "All DONE" in string:
                process.terminate()
                break

        # 等待命令行窗口关闭
        process.wait()
        # 更新obj数据到数据库
        call_update_progress(exportID, 100)
        print(f'ns-export完成')

        # 调用函数，将指定文件夹打包成ZIP文件
        zip_directory(upload_folder + '/' + proID + '/mesh/', upload_folder + '/' + proID + '/OBJ_' + proID + '.zip')
        print(f'Zip压缩完成')

        # 更新当前任务状态
        call_update_task_state('End',exportID)

        # 将当前任务finish状态到[任务]数据库 
        call_update_task_finish(1,exportID)

        # 将当前任务ExportObj finish状态到[客户端]数据库 - 修改到所有格式执行完毕才执行
        # update_ExportFormat_state(proID,Client_Service_url,'obj')

    except Exception as e:
        # 处理异常
        print(f"An error occurred: {e}")
        # 您可以在此处添加其他异常处理代码,例如记录错误、发送通知等

# V2算法 执行cmd导出 pointcloud
def run_pcd_export(config,proID):
    # command = [
    #     'cmd', '/c', 'ns-export', 'pointcloud',
    #     '--load-config', config,
    #     '--output-dir', upload_folder + '/' + proID + '/pcd/',
    #     '--num-points', '1000000',
    #     '--remove-outliers', 'True',
    #     '--normal-method', 'open3d',
    #     '--save-world-frame', 'False'
    # ]

    if platform.system() == 'Windows':
        command = [
            'cmd', '/c', 
            'call conda activate nerfstudio && ns-export pointcloud --load-config {} --output-dir {}/pcd/ --num-points 1000000 --remove-outliers True --normal-method open3d --save-world-frame False'.format(
                config, upload_folder + '/' + proID
            )
        ]
    else:
        command = [
            '/bin/bash', '-c',
            'source ~/miniconda3/etc/profile.d/conda.sh && conda activate nerfstudio && ns-export pointcloud --load-config {} --output-dir {}/pcd/ --num-points 1000000 --remove-outliers True --normal-method open3d --save-world-frame False'.format(
                config, upload_folder + '/' + proID
            )
        ]


    print(command)
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # 等待命令行窗口关闭
        return_code = process.wait()

        if return_code == 0:
            print(f'pcd-export完成')

        else:
            print(f'train执行失败，返回码: {return_code}')  # 在执行失败时打印消息

    except Exception as e:
        # 处理异常
        print(f"An error occurred: {e}")

# V2自动裁剪矩阵转换
def apply_rotation(rot_matrix, axis, theta):
    """
    将旋转矩阵应用到原始矩阵
    
    Parameters:
        rot_matrix (numpy.ndarray): 旋转矩阵
        axis (str): 旋转轴，'x', 'y', 或 'z'
        theta (float): 旋转角度，单位为度
    
    Returns:
        numpy.ndarray: 旋转后的矩阵
    """
    theta_rad = np.radians(theta)
    if axis == 'x':
        rotation_matrix = np.array([
            [1, 0, 0],
            [0, np.cos(theta_rad), -np.sin(theta_rad)],
            [0, np.sin(theta_rad), np.cos(theta_rad)]
        ])
    elif axis == 'y':
        rotation_matrix = np.array([
            [np.cos(theta_rad), 0, np.sin(theta_rad)],
            [0, 1, 0],
            [-np.sin(theta_rad), 0, np.cos(theta_rad)]
        ])
    elif axis == 'z':
        rotation_matrix = np.array([
            [np.cos(theta_rad), -np.sin(theta_rad), 0],
            [np.sin(theta_rad), np.cos(theta_rad), 0],
            [0, 0, 1]
        ])
    else:
        raise ValueError("Invalid rotation axis. Please choose 'x', 'y', or 'z'.")
    
    return np.dot(rotation_matrix, rot_matrix)

# V2自动裁剪算法
def calculate_bounding_box(transforms_data_path, dataparser_data_path, point_cloud_path):
    # 读取JSON文���
    with open(transforms_data_path, 'r') as f:
        transforms_data = json.load(f)

    # 读取JSON文件
    with open(dataparser_data_path, 'r') as f:
        dataparser_data = json.load(f)

    # 获取transform和scale字段的值
    transform_matrix = np.array(dataparser_data['transform'])
    scale = dataparser_data['scale']

    # 创建相机参数
    pinhole_camera_intrinsic = o3d.camera.PinholeCameraIntrinsic(
        transforms_data['w'], transforms_data['h'], transforms_data['fl_x'], transforms_data['fl_y'], transforms_data['cx'], transforms_data['cy']
    )

    # 创建点云
    pcd = o3d.geometry.PointCloud()

    # 选择要应用的旋转轴
    rotation_axis = 'x'  # 选择 'x', 'y', 或 'z'

    # 选择旋转角度
    rotation_angle = 90  # 选择旋转角度，单位为度

    # 添加所有帧的相机姿态
    for frame in transforms_data['frames']:
        # 获取相机位姿
        c2w = np.array(frame['transform_matrix'])

        # 应用转换
        c2w_train = transform_matrix @ c2w
        c2w_train[:3, 3] *= scale

        # 使用 apply_rotation 函数进行旋转
        c2w_train = apply_rotation(c2w_train, rotation_axis, rotation_angle)

        # 将c2w_train转换为4x4矩阵
        c2w_train = np.concatenate([c2w_train, np.array([[0, 0, 0, 1]])], axis=0)
        
        # 创建相机
        cam = o3d.camera.PinholeCameraParameters()
        cam.intrinsic = pinhole_camera_intrinsic
        cam.extrinsic = c2w_train  # 使用转换后的相机位姿矩阵

        # 将相机渲染成锥形
        cam_cone = o3d.geometry.TriangleMesh.create_cone(radius=0.05, height=0.1)
        cam_cone.compute_vertex_normals()
        cam_cone.paint_uniform_color([1, 0, 0])  # 设置锥形的颜色
        cam_cone.rotate(c2w_train[:3, :3], center=np.array([0, 0, 0]))  # 旋转锥形以匹配相机的方向
        cam_cone.translate(c2w_train[:3, 3])  # 移动锥形以匹配相机的位置

        # 将锥形转换为点云并添加到原点云中
        cam_points = np.asarray(cam_cone.vertices)
        cam_pcd = o3d.geometry.PointCloud()
        cam_pcd.points = o3d.utility.Vector3dVector(cam_points)
        pcd += cam_pcd

    # 加载稀疏点云并使用边界框裁剪
    sparse_pcd = o3d.io.read_point_cloud(point_cloud_path)

    # 加载包围盒并设置颜色
    aabb = pcd.get_axis_aligned_bounding_box()
    aabb.color = (1, 0, 0)  # 设置包围盒的颜色

    # 创建新的包围盒对象并修改高度值
    new_min_bound = [aabb.min_bound[0], aabb.min_bound[1], aabb.min_bound[2] - 3]
    new_max_bound = [aabb.max_bound[0], aabb.max_bound[1], aabb.max_bound[2] + 3]
    new_aabb = o3d.geometry.AxisAlignedBoundingBox(min_bound=new_min_bound, max_bound=new_max_bound)
    new_aabb.color = (1, 0, 0)  # 设置包围盒的颜色

    # 对稀疏点云进行裁剪
    sparse_pcd_cropped = sparse_pcd.crop(new_aabb)

    # 统计滤波
    cl, ind = sparse_pcd_cropped.remove_statistical_outlier(nb_neighbors=20,std_ratio=2.0)

    # 根据滤波器结果选择点云中的子集
    filtered_pcd = cl

    # 获取裁剪后稀疏点云的轴对齐边界框
    cropped_aabb = filtered_pcd.get_axis_aligned_bounding_box()

    # 打印包围盒的中心
    center = cropped_aabb.get_center()
    # print("Bounding Box Center: {:.2f}, {:.2f}, {:.2f}".format(center[0], center[1], center[2]))

    # 打印包围盒的缩放
    scale = cropped_aabb.get_max_bound() - cropped_aabb.get_min_bound()
    # print("Bounding Box Scale: {:.2f}, {:.2f}, {:.2f}".format(scale[0], scale[1], scale[2]))
    
    # 返回包围盒的中心和缩放
    return center, scale

# OBJ2GLTF转换
def convert_obj_to_gltf(input_file, output_file):
    """
    Convert .obj file to .gltf using obj2gltf command line tool.

    Args:
        input_file (str): Path to the input .obj file.
        output_file (str): Path to the output .gltf file.
        
    Returns:
        bool: True if conversion is successful, False otherwise.
    """
    try:
        # Remove extra quotes from input and output file paths
        input_file = input_file.strip("'")
        output_file = output_file.strip("'")

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the command
        # command = [r'C:\Users\Ning Shi Jie\AppData\Roaming\npm\obj2gltf.cmd', '-i', input_file, '-o', output_file]
        command = [os.path.join(script_dir, 'bin', 'obj2gltf.cmd'), '-i', input_file, '-o', output_file]

        # Print the command to be executed
        print(' '.join(command))

        # Execute the command
        subprocess.run(command, check=True)
        
        # Return True if successful
        return True
    except subprocess.CalledProcessError as e:
        # If an error occurs, print the error message and return False
        print("Conversion failed:", e)
        return False

# OBJ2Other转换
def convert_obj_to_Other(input_file, output_directory, proID, output_file_type):
    try:
        # 如果输出目录不存在，则创建
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # 加载 OBJ 文件
        with pyassimp.load(input_file) as scene:
            # 创建新的 FBX 场景
            new_scene = scene

            # 导出为指定格式的文件
            output_file = os.path.join(output_directory, proID + "." + output_file_type)

            # 增加GLTF2的格式判断
            if output_file_type == 'gltf':
                pyassimp.export(new_scene, output_file, 'gltf2')
            else:
                pyassimp.export(new_scene, output_file, output_file_type)

            # 搜索并复制PNG文件
            for root, dirs, files in os.walk(os.path.dirname(input_file)):
                for file in files:
                    if file.endswith(".png"):
                        png_file = os.path.join(root, file)
                        shutil.copy(png_file, output_directory)
            print("Conversion successful!")

            # 调用函数，将指定文件夹打包成ZIP文件
            zip_directory(output_directory, upload_folder + '/' + proID + '/' + output_file_type + '_' + proID + '.zip')
            print(f'Zip压缩完成')

    except Exception as e:
        print("An error occurred:", e)

# 定义任务请求的路由
@app.route('/start_GPU_task', methods=['POST'])
def start_GPU_task():

    # 获取请求中的参数 project_id 和 video_path
    project_id = request.json.get('project_id')
    video_path = request.json.get('video_path')
    export_mesh = request.json.get('export_mesh')

    # 打印接收到的请求数据
    print('[请求数据]')
    print(f'project_id: {project_id}')
    print(f'video_path: {video_path}')
    print(f'export_mesh: {export_mesh}')

    # 检查请求参数是否完整
    if not project_id or not video_path:
        return jsonify({'status': 'Error', 'message': 'Missing parameters'}), 400
    
    # 统一路径格式，将所有反斜杠转换为正斜杠
    video_path = video_path.replace('\\', '/')

    # 找到 AI_V2M_CloudStorage\uploads 之前的所有内容并替换
    video_path = video_path.replace(base_path, upload_folder)

    # 提取文件路径的目录部分
    folder_path = os.path.dirname(video_path)
    print(f'folder_path: {folder_path}')


    # 查看数据库待计算任务
    # 标记此GPU为忙碌状态
    call_update_gpu_status('busy')

    try:
        # 判断任务类型
        taskType = call_get_project_type(project_id)
        print(f'taskType: {taskType}')

        # 从字典中获取 type 值
        task_type_value = taskType.get('type')


        if task_type_value == 'train':
            print(f'执行: train计算')

            # 执行V2算法
            # 使用回调从线程获取状态
            status_callback = StatusCallback()
            thread = FFMpegThread(target=run_colmap, args=(video_path, project_id, status_callback))
            thread.start()
            
            # 等待线程完成
            thread.join()

            # 从回调中获取状态
            status = status_callback.get_status()
            print(status)
            
            if (status):
                # 执行run_splatfacto()
                print(f'执行run_splatfacto')
                run_splatfacto(folder_path,project_id,export_mesh)
                return jsonify({'status': 'GPU success'})
            else:
                # 在任务完成后，标记此GPU为空闲
                call_update_gpu_status('idle')

                # 将当前任务状态重新写入数据库
                call_update_task_state('Error',project_id)
                return jsonify({'status': 'GPU false'})
        
        elif task_type_value == 'nerfact':
            print(f'执行: nerfact计算')
            run_nerfacto(project_id)
            
        
        elif task_type_value == 'export':
            print('export')
            # V2算法中从ID获取configPath
            configPath = call_get_config_path(project_id)

            # V2算法中从ID获取cropinfo
            # 调用接口并解析返回值
            response_data = call_get_crop_info(project_id)
            if response_data:
                crop_position = response_data.get("CropPosition")
                crop_scale = response_data.get("CropScale")
                crop_rotation = response_data.get("CropRotation")

            else:
                print("Failed to retrieve crop information.")

            # 将字符串转换为浮点数列表
            crop_position_numbers = [float(x) for x in crop_position.split(",")]
            crop_scale_numbers = [float(x) for x in crop_scale.split(",")]
            crop_rotation_numbers = [float(x) for x in crop_rotation.split(",")]

            # 将浮点数转换为字符串并保留8位小数
            formatted_crop_position_numbers = [f"{num:.8f}" for num in crop_position_numbers]
            formatted_crop_scale_numbers = [f"{num:.8f}" for num in crop_scale_numbers]
            formatted_crop_rotation_numbers = [f"{num:.8f}" for num in crop_rotation_numbers]

            # 将结果转换为NumPy数组
            result_crop_position_array = np.array(formatted_crop_position_numbers)
            result_crop_scale_array = np.array(formatted_crop_scale_numbers)
            result_crop_rotation_array = np.array(formatted_crop_rotation_numbers)

            # 执行Nerf2Mesh
            run_obj_export(configPath,project_id,video_path,result_crop_position_array,result_crop_scale_array,result_crop_rotation_array,'200000','True')

            # 拼接obj文件路径
            obj_path = upload_folder + '/' + video_path + '/mesh/mesh.obj'

            # OBJ2GLTF转换
            print('gltf')
            output_file = upload_folder + '/' + video_path + '/gltf/'
            convert_obj_to_Other(obj_path,output_file,video_path,'gltf')
            # 将当前任务Export finish状态到[客户端]数据库
            update_ExportFormat_state(video_path,Client_Service_url,'gltf')
            # 更新Mesh进度数据到[客户端]数据库
            update_ExportObj_progress(video_path,90,Client_Service_url)

            print('fbx')
            output_file = upload_folder + '/' + video_path + '/fbx/'
            # OBJ2FBX转换
            convert_obj_to_Other(obj_path,output_file,video_path,'fbx')
            # 将当前任务ExportObj finish状态到[客户端]数据库
            update_ExportFormat_state(video_path,Client_Service_url,'fbx')
            # 更新Mesh进度数据到[客户端]数据库
            update_ExportObj_progress(video_path,92,Client_Service_url)

            print('3ds')
            output_file = upload_folder + '/' + video_path + '/3ds/'
            # OBJ23ds转换
            convert_obj_to_Other(obj_path,output_file,video_path,'3ds')
            # 将当前任务ExportObj finish状态到[客户端]数据库
            update_ExportFormat_state(video_path,Client_Service_url,'3ds')
            # 更新Mesh进度数据到[客户端]数据库
            update_ExportObj_progress(video_path,94,Client_Service_url)

            print('x')
            output_file = upload_folder + '/' + video_path + '/x/'
            # OBJ2x转换
            convert_obj_to_Other(obj_path,output_file,video_path,'x')
            # 将当前任务ExportObj finish状态到[客户端]数据库
            update_ExportFormat_state(video_path,Client_Service_url,'x')
            # 更新Mesh进度数据到[客户端]数据库
            update_ExportObj_progress(video_path,96,Client_Service_url)

            print('stl')
            output_file = upload_folder + '/' + video_path + '/stl/'
            # OBJ2stl转换
            convert_obj_to_Other(obj_path,output_file,video_path,'stl')
            # 将当前任务ExportObj finish状态到[客户端]数据库
            update_ExportFormat_state(video_path,Client_Service_url,'stl')

            # 更新Mesh进度数据到[客户端]数据库
            update_ExportObj_progress(video_path,100,Client_Service_url)
            # 将当前任务ExportObj finish状态到[客户端]数据库 - 修改到所有格式执行完毕才执行
            update_ExportFormat_state(video_path,Client_Service_url,'obj')
            
            # 在任务完成后，标记此GPU为空闲
            call_update_gpu_status('idle')

            # 通知GPU Manager任务结束 执行下一个任务
            send_retrun_task(project_id)
            return jsonify({'status': 'GPU success'})
        
        elif task_type_value == 'gltf':
            print('gltf')
            # 拼接obj文件路径
            obj_path = upload_folder + '/' + video_path + '/mesh/mesh.obj'
            # output_file = upload_folder + '/' + video_path + '/gltf/mesh.gltf'
            output_file = upload_folder + '/' + video_path + '/gltf/'
            # OBJ2GLTF转换
            # convert_obj_to_gltf(obj_path,output_file)
            convert_obj_to_Other(obj_path,output_file,video_path,'gltf')

            # 更新当前任务状态
            call_update_task_state('End',project_id)

            # 将当前任务finish状态到[任务]数据库 
            call_update_task_finish(1,project_id)

            # 将当前任务Export finish状态到[客户端]数据库
            update_ExportFormat_state(video_path,Client_Service_url,'gltf')

            # 在��务完成后，标记此GPU为空闲
            call_update_gpu_status('idle')

            # 通知GPU Manager任务结束 执行下一个任务
            send_retrun_task(project_id)
            return jsonify({'status': 'GPU success'})
        
        elif task_type_value == 'fbx':
            print('fbx')
            # 拼接obj文件路径
            obj_path = upload_folder + '/' + video_path + '/mesh/mesh.obj'
            output_file = upload_folder + '/' + video_path + '/fbx/'
            # OBJ2FBX转换
            convert_obj_to_Other(obj_path,output_file,video_path,'fbx')

            # 更新当前任务状态
            call_update_task_state('End',project_id)

            # 将当前任务finish状态到[任务]数据库 
            call_update_task_finish(1,project_id)

            # 将当前任务ExportObj finish状态到[客户端]数据库
            update_ExportFormat_state(video_path,Client_Service_url,'fbx')

            # 在任务完成后，标记此GPU为空闲
            call_update_gpu_status('idle')

            # 通知GPU Manager任务结束 执行下一个任务
            send_retrun_task(project_id)
            return jsonify({'status': 'GPU success'})
        
        elif task_type_value == '3ds':
            print('3ds')
            # 拼接obj文件路径
            obj_path = upload_folder + '/' + video_path + '/mesh/mesh.obj'
            output_file = upload_folder + '/' + video_path + '/3ds/'
            # OBJ23ds转换
            convert_obj_to_Other(obj_path,output_file,video_path,'3ds')

            # 更新当前任务状态
            call_update_task_state('End',project_id)

            # 将当前任务finish状态到[任务]数据库 
            call_update_task_finish(1,project_id)

            # 将当前任务ExportObj finish状态到[客户端]数据库
            update_ExportFormat_state(video_path,Client_Service_url,'3ds')

            # 在任务完成后，标记此GPU为空闲
            call_update_gpu_status('idle')

            # 通知GPU Manager任务结束 执行下一个任务
            send_retrun_task(project_id)
            return jsonify({'status': 'GPU success'})
        
        elif task_type_value == 'x':
            print('x')
            # 拼接obj文件路径
            obj_path = upload_folder + '/' + video_path + '/mesh/mesh.obj'
            output_file = upload_folder + '/' + video_path + '/x/'
            # OBJ2x转换
            convert_obj_to_Other(obj_path,output_file,video_path,'x')

            # 更新当前任务状态
            call_update_task_state('End',project_id)

            # 将当前任务finish状态到[任务]数据库 
            call_update_task_finish(1,project_id)

            # 将当前任务ExportObj finish状态到[客户端]数据库
            update_ExportFormat_state(video_path,Client_Service_url,'x')

            # 在任务完成后，标记此GPU为空闲
            call_update_gpu_status('idle')

            # 通知GPU Manager任务结束 执行下一个任务
            send_retrun_task(project_id)
            return jsonify({'status': 'GPU success'})
        
        elif task_type_value == 'stl':
            print('stl')
            # 拼接obj文件路径
            obj_path = upload_folder + '/' + video_path + '/mesh/mesh.obj'
            output_file = upload_folder + '/' + video_path + '/stl/'
            # OBJ2stl转换
            convert_obj_to_Other(obj_path,output_file,video_path,'stl')

            # 更新当前任务状态
            call_update_task_state('End',project_id)

            # 将当前任务finish状态到[任务]数据库 
            call_update_task_finish(1,project_id)

            # 将当前任务ExportObj finish状态到[客户端]数据库
            update_ExportFormat_state(video_path,Client_Service_url,'stl')

            # 在任务完成后，标记此GPU为空闲
            call_update_gpu_status('idle')

            # 通知GPU Manager任务结束 执行下一个任务
            send_retrun_task(project_id)
            return jsonify({'status': 'GPU success'})

        elif task_type_value == 'crop':
            print('Crop calculation')
            # V2算法中从ID获取configPath
            configPath = call_get_config_path(project_id)

            # 执行pcd导出
            # run_pcd_export(configPath,video_path)

            # 根据pcd计算裁剪范围
            # 取目录
            directory = os.path.dirname(configPath)

            # 调用函数并传入参数
            transforms_data_path =  f'{upload_folder}/{video_path}/sfm/transforms.json'
            dataparser_data_path = f'{directory}/dataparser_transforms.json'
            point_cloud_path = f'{upload_folder}/{video_path}/pcd/point_cloud.ply'

            # 调用函数并获取返回值
            bounding_box_center, bounding_box_scale = calculate_bounding_box(transforms_data_path, dataparser_data_path, point_cloud_path)

            # 使用返回的包围盒中心和缩放值
            print("Bounding Box Center:", bounding_box_center)
            print("Bounding Box Scale:", bounding_box_scale)

            # 将坐标转换为字符串
            center_str = [str(coord) for coord in bounding_box_center]
            scale_str = [str(coord) for coord in bounding_box_scale]

            # 去除每个字符串中的方括号，并转换为浮点数
            crop_position_float = [float(value.strip('[]')) for value in center_str]
            crop_scale_float = [float(value.strip('[]')) for value in scale_str]

            # 将浮点数列表转换为字符串，并使用逗号连接
            center_str_result = ', '.join(map(str, crop_position_float))
            scale_str_result = ', '.join(map(str, crop_scale_float))

            # 上传自动裁剪矩阵到[客户端]数据库 这里的ID是 video_path
            updataCropPositionAndScale(video_path,center_str_result,scale_str_result)

            # 等待命令行执行完毕
            print(f'Crop calculation完成')

            # 更新当前任务状态
            call_update_task_state('End',project_id)

            # 将当前任务finish状态到[任务]数据库 
            call_update_task_finish(1,project_id)

            # 在任务完成后，标记此GPU为空闲
            call_update_gpu_status('idle')

            # 通知GPU Manager任务结束 执行下一个任务
            send_retrun_task(project_id)
            return jsonify({'status': 'GPU success'})
    
    except Exception as e:
        # 处理任何可能的异常
        print(f"Error in start_GPU_task: {e}")
        call_update_gpu_status('idle')
        return jsonify({'status': 'Error', 'message': str(e)}), 500
    
# 调用 update_task_state 更新任务状态
def call_update_task_state(status, project_id):
    """
    调用 update_task_state 接口，根据项目 ID 更新任务状态
    :param project_id: 项目 ID
    :param status: 新的任务状态
    :return: 接口返回的消息或错误信息
    """
    # 拼接完整的 URL
    endpoint = '/update_task_state'
    base_url = GPU_Manager_url

    # 准备请求数据
    data = {
        "project_id": project_id,
        "status": status
    }

    try:
        # 发送 POST 请求
        response = requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()  # 如果发生 HTTP 错误，抛出异常
        return response.json()  # 返回 JSON 响应

    except requests.exceptions.RequestException as e:
        print(f"Error sending request to update_task_state: {e}")
        return None

# 调用 update_task_finish 更新任务的 finish 状态
def call_update_task_finish(finish, project_id):
    """
    调用 update_task_finish 接口，根据项目 ID 更新任务的 finish 状态
    :param project_id: 项目 ID
    :param finish: 新的任务 finish 状态 (True/False)
    :return: 接口返回的消息或错误信息
    """
    # 拼接完整的 URL
    endpoint = '/update_task_finish'
    base_url = GPU_Manager_url

    # 准备请求数据
    data = {
        "project_id": project_id,
        "finish": finish
    }

    try:
        # 发送 POST 请求
        response = requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()  # 如果发生 HTTP 错误，抛出异常
        return response.json()  # 返回 JSON 响应

    except requests.exceptions.RequestException as e:
        print(f"Error sending request to update_task_finish: {e}")
        return None


# 添加Export任务到GPU队列 - 由客户端执行
def send_ExportTask_to_GPU_Manager(configPath,folder_name,CropPosition,CropScale):

    # 从配置表获取GPU_Manager服务器地址
    base_url = GPU_Manager_url

    # Test case with project_id and video_path parameters
    data = {"folder_name": folder_name, "configPath": configPath, "CropPosition": CropPosition, "CropScale": CropScale}
    endpoint = '/add_ExportTask'

    try:
        response = requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None

# 添加CROP计算任务到GPU队列
def send_CropTask_to_GPU_Manager(configPath,folder_name):

    # 从配置表获取GPU_Manager服务器地址
    base_url = GPU_Manager_url

    # Test case with project_id and video_path parameters
    data = {"folder_name": folder_name, "configPath": configPath}
    endpoint = '/add_CropTask'

    try:
        response = requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None
    
# 写入文件测试
def write_to_file(task_id, file_path):
    # Generate a unique filename based on task_id
    filename = os.path.join(f"{upload_folder}/{task_id}/{task_id}.txt")

    # Write task_id and file_path to the file
    with open(filename, 'w') as file:
        file.write(f"Task ID: {task_id}\n")
        file.write(f"File Path: {file_path}\n")

    print(f"Data written to file: {filename}")

# 调用 update_gpu_status 更新 GPU 的状态
def call_update_gpu_status(status):
    """
    调用 update_gpu_status 接口，更新 GPU 的状态
    :param port: GPU 服务的端口号
    :param status: 要更新的状态值 ('busy'、'idle' 或 'offline')
    :return: 接口返回的数据
    """
    # 拼接完整的 URL
    endpoint = '/update_gpu_status'
    base_url = GPU_Manager_url

    # 准备请求数据
    data = {
        "port": app.config['port'],
        "status": status
    }

    try:
        # 发送 POST 请求
        response = requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()  # 如果发生 HTTP 错误，抛出异常
        return response.json()  # 返回 JSON 响应

    except requests.exceptions.RequestException as e:
        print(f"Error sending request to update_gpu_status: {e}")
        return None

# 向指定IP端口发送post请求
def send_retrun_task(project_id):
   
    base_url = GPU_Manager_url

    # Test case with project_id and video_path parameters
    data = {'project_id': project_id}
    endpoint = '/return_task'

    try:
        response = requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None

# 通知GPU Manager 计算服务上线
def send_online_to_GPU_Manager():
    print("执行请求任务")
    base_url = GPU_Manager_url
    endpoint = '/run_task'
    data = {'GPU': 'hello'}

    try:
        response = requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None
    
class StatusCallback:
    def __init__(self):
        self.status = None
        self.lock = threading.Lock()

    def set_status(self, success=True):
        with self.lock:
            self.status = success

    def get_status(self):
        with self.lock:
            return self.status

class FFMpegThread(threading.Thread):
    def __init__(self, target, args=()):
        # 只取args的前2个值
        super(FFMpegThread, self).__init__(target=target, args=args[:2])
        # 取args的最后一个状态值
        self.status_callback = args[-1]

    def run(self):
        try:
            super(FFMpegThread, self).run()
            self.status_callback.set_status(success=True)
        except Exception as e:
            # self.status_callback.set_status(f'ffmpeg执行失败：{e}')
            print("ffmpeg执行失败")
            self.status_callback.set_status(success=False)

# 调用 update_progress 更新[任务数据库]的进度
def call_update_progress(project_id, progress):
    """
    调用 update_progress 接口，根据项目 ID 更新任务的进度
    :param project_id: 项目 ID
    :param progress: 新的任务进度
    :return: 接口返回的消息或错误信息
    """
    # 拼接完整的 URL
    endpoint = '/update_progress'
    base_url = GPU_Manager_url

    # 准备请求数据
    data = {
        "project_id": project_id,
        "progress": progress
    }

    try:
        # 发送 POST 请求
        response = requests.post(f'{base_url}{endpoint}', json=data)
        response.raise_for_status()  # 如果发生 HTTP 错误，抛出异常
        return response.json()  # 返回 JSON 响应

    except requests.exceptions.RequestException as e:
        print(f"Error sending request to update_progress: {e}")
        return None

# 更新指定ID splatfacto进度到[客户端]数据库
def update_project_progress(id_parameter, progress_val, server_address):
    try:
        # JSON data to be sent in the request
        data = {'id': id_parameter, 'progressVal': progress_val}

        # URL of the Flask application
        url = f"{server_address}/updataProjectProgress"

        # Making POST request
        response = requests.post(url, json=data)

        # Checking response status code
        if response.status_code == 200:
            # Returning response content
            return response.json()
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}

# 更新指定ID nerfacto进度到[客户端]数据库
def update_Nerfacto_progress(id_parameter, progress_val, server_address):
    try:
        # JSON data to be sent in the request
        data = {'id': id_parameter, 'progressVal': progress_val}

        # URL of the Flask application
        url = f"{server_address}/updataNerfactoProgress"

        # Making POST request
        response = requests.post(url, json=data)

        # Checking response status code
        if response.status_code == 200:
            # Returning response content
            return response.json()
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}

# 更新指定ID ExportObj进度到[客户端]数据库
def update_ExportObj_progress(id_parameter, progress_val, server_address):
    try:
        # JSON data to be sent in the request
        data = {'id': id_parameter, 'progressVal': progress_val}

        # URL of the Flask application
        url = f"{server_address}/updataExportObjProgress"

        # Making POST request
        response = requests.post(url, json=data)

        # Checking response status code
        if response.status_code == 200:
            # Returning response content
            return response.json()
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}


# 更新指定ID splatfacto训练状态到[客户端]数据库
def update_project_state(id_parameter, server_address):
    try:
        # JSON data to be sent in the request
        data = {'id': id_parameter}

        # URL of the Flask application
        url = f"{server_address}/updataProjectState"

        # Making POST request
        response = requests.post(url, json=data)

        # Checking response status code
        if response.status_code == 200:
            # Returning response content
            return response.json()
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}

# 更新指定ID nerfacto训练状态到[客户端]数据库
def update_Nerfacto_state(id_parameter, server_address):
    try:
        # JSON data to be sent in the request
        data = {'id': id_parameter}

        # URL of the Flask application
        url = f"{server_address}/updataNerfactoState"

        # Making POST request
        response = requests.post(url, json=data)

        # Checking response status code
        if response.status_code == 200:
            # Returning response content
            return response.json()
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}

# 更新指定ID ExportObj状态到[客户端]数据库
def update_ExportObj_state(id_parameter, server_address):
    try:
        # JSON data to be sent in the request
        data = {'id': id_parameter}

        # URL of the Flask application
        url = f"{server_address}/updataExportObjState"

        # Making POST request
        response = requests.post(url, json=data)

        # Checking response status code
        if response.status_code == 200:
            # Returning response content
            return response.json()
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}

# 更新指定ID ExportFormat状态到[客户端]数据库
def update_ExportFormat_state(id_parameter, server_address, format):
    try:
        # JSON data to be sent in the request
        data = {'id': id_parameter, 'format': format}

        # URL of the Flask application
        url = f"{server_address}/updataExportFormatState"

        # Making POST request
        response = requests.post(url, json=data)

        # Checking response status code
        if response.status_code == 200:
            # Returning response content
            return response.json()
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}

# 重置指定ID ExportFormat状态到[客户端]数据库
def reset_ExportFormat_state(id_parameter, server_address):
    try:
        print("resetMesh")
        # JSON data to be sent in the request
        data = {'id': id_parameter}

        # URL of the Flask application
        url = f"{server_address}/resetExportFormatState"

        # Making POST request
        response = requests.post(url, json=data)

        # Checking response status code
        if response.status_code == 200:
            # Returning response content
            return response.json()
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}
    
# 更新指定ID NerfactoConfig_Path到[客户端]数据库
def update_NerfactoConfig_Path(id_parameter, Config_Path, server_address):
    try:
        # JSON data to be sent in the request
        data = {'id': id_parameter, 'path': Config_Path}

        # URL of the Flask application
        url = f"{server_address}/NerfactoConfig_Path"

        # Making POST request
        response = requests.post(url, json=data)

        # Checking response status code
        if response.status_code == 200:
            # Returning response content
            return response.json()
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}
 
# 更新指定ID CROP矩阵[客户端]数据库
def updataCropPositionAndScale(id_parameter, CropPosition, CropScale):
    try:
        print('写入裁剪矩阵')
        # JSON data to be sent in the request
        data = {'id': id_parameter, 'CropPosition': CropPosition, 'CropScale': CropScale, 'CropRotation': "0.0, 0.0, 0.0"}

        # URL of the Flask application
        url = f"{Client_Service_url}/updataCropPositionAndScale"

        # Making POST request
        response = requests.post(url, json=data)

        # Checking response status code
        if response.status_code == 200:
            # Returning response content
            return response.json()
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}
 
# 正则表达式过滤命令行进度字符
def extract_percentage(progress_string):
    # 使用正则表达式匹配百分比
    match = re.search(r'(\d+)%', progress_string)
    
    if match:
        percentage = int(match.group(1))
        return f"{percentage}%"  # 将百分比转换为字符串
    else:
        return None
    
# 获取 ffmpeg 执行状态
@app.route('/ffmpeg_status', methods=['GET'])
def get_ffmpeg_status():
    global ffmpeg_status
    return jsonify({'status': ffmpeg_status})

# SocketIO 连接事件
@socketio.on('connect', namespace='/test')
def test_connect():
    send('Connected')

# 检查端口是否被占用
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

# 将要传递的值保存在app.config中
app.config['port'] = 5005

# 注册退出时执行的函数
def cleanup():
    call_update_gpu_status('offline')

atexit.register(cleanup)

# 获取网络交互数据
def get_download_speed(interval=1):
    # 获取当前网络数据
    initial_net_io = psutil.net_io_counters()

    # 等待一段时间
    time.sleep(interval)

    # 获取新的网络数据
    final_net_io = psutil.net_io_counters()

    # ��算接收的字节数差值
    recv_bytes = final_net_io.bytes_recv - initial_net_io.bytes_recv

    # 计算速率（以Kbps为单位）
    download_kbps = (recv_bytes / interval) / 1024

    return download_kbps

def get_upload_speed(interval=1):
    # 获取当前网络数据
    initial_net_io = psutil.net_io_counters()

    # 等待一段时间
    time.sleep(interval)

    # 获取新的网络数据
    final_net_io = psutil.net_io_counters()

    # 计算发送的字节数差值
    sent_bytes = final_net_io.bytes_sent - initial_net_io.bytes_sent

    # 计算速率（以Kbps为单位）
    upload_kbps = (sent_bytes / interval) / 1024

    return upload_kbps
# 获取网络交互数据
def get_network_usage():
    net_io = psutil.net_io_counters()
    # 获取发送和接收的字节数（以MB为单位）
    bytes_sent_mb = round(net_io.bytes_sent / (1024 ** 3), 2)
    bytes_recv_mb = round(net_io.bytes_recv / (1024 ** 3), 2)
    # 格式化为字符串
    usage_str = f"{bytes_sent_mb} / {bytes_recv_mb}GB"
    return usage_str

# 获取在线时长
def get_timedelta():
    # 获取系统启动时间戳（以秒为单位）
    boot_time_seconds = psutil.boot_time()

    # 获取当前时间戳
    current_time_seconds = psutil.time.time()

    # 计算系统运行时间（以秒为单位）
    runtime_seconds = current_time_seconds - boot_time_seconds

    # 将秒数转换为小时、分钟和秒
    hours, remainder = divmod(runtime_seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    # 格式化为字符串
    runtime_str = f"{int(hours)} h / {int(minutes)} m"
    return runtime_str

# 获取硬盘使用情况
def get_disk_usage():
    # 获取硬盘使用情况
    disk_usage = psutil.disk_usage('/')

    # 获取已用空间和总空间（以GB为单位）
    used_space_gb = round(disk_usage.used / (1024 ** 3), 0)
    total_space_gb = round(disk_usage.total / (1024 ** 3), 0)

    # 格式化为字符串
    disk_usage_str = f"{used_space_gb} / {total_space_gb}GB"
    return disk_usage_str

# 获取系统内存信息
def get_memory_info():
    memory_info = psutil.virtual_memory()

    # 获取总内存大小、已使用内存大小、可用内存大小（以GB为单位）
    total_memory_gb = round(memory_info.total / (1024 ** 3), 2)
    used_memory_gb = round(memory_info.used / (1024 ** 3), 2)
    available_memory_gb = round(memory_info.available / (1024 ** 3), 2)

    return {
        'total_memory': total_memory_gb,
        'used_memory': used_memory_gb,
        'available_memory': available_memory_gb
    }

# 获取设备IP信息
def get_ip_address():
    # 获取当前设备的网络接口信息
    network_interfaces = psutil.net_if_addrs()

    ip_address_list = []

    for interface, addrs in network_interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ip_address_list.append(addr.address)

    return ip_address_list[0]

# 获取设备硬件信息 非实时
@app.route('/get_system_info', methods=['GET'])
def get_system_info():
    try:
        # 获取在线时长
        runtime_str = get_timedelta()
        # 获取网络下载数据
        download_speed = get_download_speed()
        # 获取网络上传数据
        upload_speed = get_upload_speed()
        # 调用函数获取内存信息
        memory_info_str = get_memory_info()
        # IP信息
        IP_str = get_ip_address()
        # 获取硬盘使用情况
        disk_usage_str = get_disk_usage()
        # 网络交互量
        network_usage_str = get_network_usage()

        system_info = {
            # 系统版本
            'platform': platform.system(),
            'version': platform.version(),
            # 设备IP位置
            'ip': IP_str,
            # 硬盘空间
            'disk_usage': disk_usage_str,
            # 网络交互
            'network_usage': network_usage_str,
            # 在线时长
            'uptime': runtime_str,
            # 内存信息
            'memory_info': f"{memory_info_str['used_memory']} / {memory_info_str['total_memory']}GB",
            # 网络下载
            'download_speed': download_speed,
            # 网络上传
            'upload_speed': upload_speed,
            # cpu占用率
            'cpu': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent,
        }
        # 返回JSON格式的数据
        return jsonify(system_info)
        # return system_info

    except Exception as e:
        return jsonify({'error': str(e)})

# 实时调用内容
@app.route('/get_system_infoRuntime', methods=['GET'])
def get_system_infoRuntime():
    try:
        # 获取在线时长
        runtime_str = get_timedelta()
        system_info = {
            # 在线时长
            'uptime': runtime_str,
            # cpu占用率
            'cpu': psutil.cpu_percent(interval=1),
            # 'cpu': get_cpupercent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent,
        }
        # 返回JSON格式的数据
        return jsonify(system_info)

    except Exception as e:
        return jsonify({'error': str(e)})

# 调用函数获取系统信息
# system_info = get_system_info()

# print(f"系统版本: {system_info['platform']} {system_info['version']}")
# print(f"IP地址: {system_info['ip']}")
# print(f"在线时长: {system_info['uptime']}")
# print(f"硬盘空间: {system_info['disk_usage']}")
# print(f"交换: {system_info['network_usage']}")
# print(f"下载: {system_info['download_speed']}")
# print(f"上传: {system_info['upload_speed']}")
# print(f"CPU 使用率: {system_info['cpu']}%")
# print(f"memory 使用率: {system_info['memory']}%")
# print(f"disk 使用率: {system_info['disk']}%")

# 通知GPU Manager 计算服务上线
# 创建一个延迟执行函数
def delayed_send_online():
    time.sleep(2)
    send_online_to_GPU_Manager()

# debug=False 避免在调试模式下的多次调用问题
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask App with GPU Task Handling')
    parser.add_argument('--port', type=int, default=5006, help='Port number for the Flask app')
    args = parser.parse_args()
    # 将要传递的值保存在app.config中
    app.config['port'] = args.port
    # 注册当前GPU服务
    call_update_gpu_status('idle')

    # 创建线程执行延迟函数
    threading.Thread(target=delayed_send_online, daemon=True).start()
    
    try:
        socketio.run(app, debug=False, host='0.0.0.0', port=args.port)
    except Exception as e:
        print(f"Error: {e}")