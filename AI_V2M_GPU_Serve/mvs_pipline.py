import subprocess,toml
import os
import re

# 读取 TOML 文件
with open('config_modeling_serve.toml', 'r') as file:
    toml_data = toml.load(file)

command_colmap = toml_data.get('cmd', {}).get('convert', {}).get('colmap')
command_openMVS = toml_data.get('cmd', {}).get('convert', {}).get('openMVS')

# sfm转txt
def convert_colmap_model_to_txt(input_path, output_path, output_type='TXT'):
    """
    Converts a COLMAP model using colmap model_converter.

    Parameters:
    input_path (str): Path to the input COLMAP model.
    output_path (str): Path to the output directory.
    output_type (str): Type of the output model (default is 'TXT').

    Returns:
    bool: True if the conversion was successful, False otherwise.
    """
    try:
        # Ensure the output directory exists
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            print(f"Created output directory: {output_path}")

        # Construct the command
        command = [
            command_colmap + 'COLMAP.bat','model_converter',
            '--input_path', input_path,
            '--output_path', output_path,
            '--output_type', output_type
        ]
        
        # Run the command
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Check the output
        if result.returncode == 0:
            print("Conversion successful.")
            return True
        else:
            print("Conversion failed.")
            print("Error message:", result.stderr.decode())
            return False
    except subprocess.CalledProcessError as e:
        print("Error during conversion:", e)
        print("Error message:", e.stderr.decode())
        return False

# cameras.txt格式修改
def EditCameraTXT(output_path):
    cameras_path = output_path + '/cameras.txt' 
    # 读取文件内容
    with open(cameras_path, 'r') as file:
        lines = file.readlines()
    
    # 修改相机模型名称并保留字段
    with open(cameras_path, 'w') as file:
        for line in lines:
            if line.startswith("#") or line.strip() == "":
                # 保留注释和空行
                file.write(line)
            else:
                # 解析相机参数行
                parts = line.split()
                if parts[1] == 'OPENCV':
                    parts[1] = 'PINHOLE'
                    parts = parts[:8]  # 只保留前6个字段
                file.write(" ".join(parts) + "\n")

# sfm转bin
def convert_colmap_model_to_bin(input_path, output_path, output_type='BIN'):
    """
    Converts a COLMAP model from TXT to BIN using colmap model_converter.

    Parameters:
    input_path (str): Path to the input COLMAP model in TXT format.
    output_path (str): Path to the output directory for the BIN format model.
    output_type (str): Type of the output model (default is 'BIN').

    Returns:
    bool: True if the conversion was successful, False otherwise.
    """
    try:
        # Ensure the output directory exists
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            print(f"Created output directory: {output_path}")
            
        # Construct the command
        command = [
            command_colmap + 'COLMAP.bat','model_converter',
            '--input_path', input_path,
            '--output_path', output_path,
            '--output_type', output_type
        ]
        
        # Run the command
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Check the output
        if result.returncode == 0:
            print("Conversion to BIN successful.")
            return True
        else:
            print("Conversion to BIN failed.")
            print("Error message:", result.stderr.decode())
            return False
    except subprocess.CalledProcessError as e:
        print("Error during conversion:", e)
        print("Error message:", e.stderr.decode())
        return False

# 正则表达式过滤命令行进度字符
def extract_percentage(progress_string):
    # 使用正则表达式匹配百分比
    match = re.search(r'(\d+)%', progress_string)
    
    if match:
        percentage = int(match.group(1))
        return f"{percentage}%"  # 将百分比转换为字符串
    else:
        return None

# 清理.dmap文件
def clean_dmap_files(directory):
    try:
        # 确保目录存在
        if not os.path.exists(directory):
            print(f"目录不存在: {directory}")
            return False
        
        # 获取目录下所有文件
        files = os.listdir(directory)
        
        # 统计删除的文件数量
        deleted_count = 0
        
        # 遍历文件，删除.dmap文件
        for file in files:
            if file.endswith('.dmap'):
                file_path = os.path.join(directory, file)
                os.remove(file_path)
                print(f"已删除文件: {file_path}")
                deleted_count += 1
        
        print(f"总共删除了 {deleted_count} 个.dmap文件")
        return True

    except Exception as e:
        print(f"清理文件时出错: {e}")
        return False

# InterfaceCOLMAP
def InterfaceCOLMAP(input_path, workin_directory):
    try:
        # Ensure the output directory exists
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            print(f"Created output directory: {output_path}")

        # Construct the command
        command = [
            command_openMVS + 'InterfaceCOLMAP',
            '-i', input_path,
            '-o', 'scene.mvs',
            '-w', workin_directory
        ]
        
        # Run the command
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Check the output
        if result.returncode == 0:
            print("Conversion successful.")
            return True
        else:
            print("Conversion failed.")
            print("Error message:", result.stderr.decode())
            return False
    except subprocess.CalledProcessError as e:
        print("Error during conversion:", e)
        print("Error message:", e.stderr.decode())
        return False


# InterfaceMVSNet
def InterfaceMVSNet(input_path, workin_directory):
    try:
        # Construct the command
        command = [
            command_openMVS + 'InterfaceMVSNet',
            '-i', input_path,
            '-o', 'scene.mvs',
            '-w', workin_directory
        ]
        
        # Run the command
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Check the output
        if result.returncode == 0:
            print("Conversion successful.")
            return True
        else:
            print("Conversion failed.")
            print("Error message:", result.stderr.decode())
            return False
    except subprocess.CalledProcessError as e:
        print("Error during conversion:", e)
        print("Error message:", e.stderr.decode())
        return False

# DensifyPointCloud
def densify_point_cloud(workin_directory):
    try:
        # Ensure the output directory exists
        if not os.path.exists(workin_directory):
            os.makedirs(workin_directory)
            print(f"Created working directory: {workin_directory}")

        # Construct the command
        command = [
            command_openMVS + 'DensifyPointCloud', 'scene.mvs',
            '-w', workin_directory,
            '--remove-dmaps', '1',
            # '--max-resolution', '2048'
        ]
        
        # Run the command and capture output line by line
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # 关闭命令行输出
        process.stdout.close()
        return_code = process.wait()

        if return_code == 0:
            print('densify_point_cloud执行完成') 

        else:
            print(f'densify_point_cloud执行失败，返回码: {return_code}')  # 在执行失败时打印消息

    except subprocess.CalledProcessError as e:
        print("Error during densification:", e)
        print("Error message:", e.stderr.decode())
        return False

# ReconstructMesh
def ReconstructMesh(workin_directory):
    try:
        # Ensure the output directory exists
        if not os.path.exists(workin_directory):
            os.makedirs(workin_directory)
            print(f"Created working directory: {workin_directory}")

        # Construct the command
        command = [
            command_openMVS + 'ReconstructMesh', 'scene_dense.mvs',
            # '-p', 'scene_dense.ply',
            '-w', workin_directory,
            '--target-face-num', '1000000',
            '--close-holes', '100',
            # '--remove-spurious', '0',
            # '--remove-spikes', '0',
            # '-d', '0.01',
            # '--edge-length', '0.05',
            # '--crop-to-roi', '1',            
            # '--free-space-support', '1',            
        ]
        
        # Run the command and capture output line by line
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # 关闭命令行输出
        process.stdout.close()
        return_code = process.wait()

        if return_code == 0:
            print('ReconstructMesh执行完成') 

        else:
            print(f'ReconstructMesh执行失败，返回码: {return_code}')  # 在执行失败时打印消息

    except subprocess.CalledProcessError as e:
        print("Error during densification:", e)
        print("Error message:", e.stderr.decode())
        return False

# RefineMesh
def RefineMesh(workin_directory):
    try:
        # Ensure the output directory exists
        if not os.path.exists(workin_directory):
            os.makedirs(workin_directory)
            print(f"Created working directory: {workin_directory}")

        # Construct the command
        command = [
            command_openMVS + 'RefineMesh', 'scene_dense.mvs',
            '-m', 'scene_dense_mesh.ply',
            '-o', 'scene_dense_mesh_refine.mvs',
            '-w', workin_directory,
            # '--remove-spurious', '0',
            # '--remove-spikes', '0',
        ]
        
        # Run the command and capture output line by line
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # 关闭命令行输出
        process.stdout.close()
        return_code = process.wait()

        if return_code == 0:
            print('ReconstructMesh执行完成') 

        else:
            print(f'ReconstructMesh执行失败，返回码: {return_code}')  # 在执行失败时打印消息

    except subprocess.CalledProcessError as e:
        print("Error during densification:", e)
        print("Error message:", e.stderr.decode())
        return False

# TextureMesh
def TextureMesh(workin_directory):
    try:
        # Ensure the output directory exists
        if not os.path.exists(workin_directory):
            os.makedirs(workin_directory)
            print(f"Created working directory: {workin_directory}")

        # Construct the command
        command = [
            command_openMVS + 'TextureMesh', 'scene_dense_mesh.mvs',
            # '-m', 'scene_dense_mesh.ply',
            '-o', 'scene_dense_mesh_refine_texture.mvs',
            '-w', workin_directory
        ]
        
        # Run the command and capture output line by line
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # 关闭命令行输出
        process.stdout.close()
        return_code = process.wait()

        if return_code == 0:
            print('TextureMesh执行完成') 

        else:
            print(f'TextureMesh执行失败，返回码: {return_code}')  # 在执行失败时打印消息

    except subprocess.CalledProcessError as e:
        print("Error during densification:", e)
        print("Error message:", e.stderr.decode())
        return False


# Example usage:
input_path = 'E:/Python/AI_V2M_Distributedd_Gsplat/AI_V2M_CloudStorage/uploads/20241111_5010/sfm/colmap/sparse/0'
output_path = 'E:/Python/AI_V2M_Distributedd_Gsplat/AI_V2M_CloudStorage/uploads/20241111_5010/sfm/colmap/sparse_txt'
outputBin_path = 'E:/Python/AI_V2M_Distributedd_Gsplat/AI_V2M_CloudStorage/uploads/20241111_5010/sfm/colmap/sparse'
colmap_path = 'E:/Python/AI_V2M_Distributedd_Gsplat/AI_V2M_CloudStorage/uploads/20241111_5010/sfm/colmap'
image_path = 'E:/Python/AI_V2M_Distributedd_Gsplat/AI_V2M_CloudStorage/uploads/20241111_5010/sfm'

# step_01
convert_colmap_model_to_txt(input_path, output_path)
# step_02
EditCameraTXT(output_path)
# step_03
convert_colmap_model_to_bin(output_path,outputBin_path)
# step_04
InterfaceCOLMAP(colmap_path,image_path)
# InterfaceMVSNet(image_path,image_path)
# step_05
densify_point_cloud(image_path)
# step_06
# clean_dmap_files(image_path)
# step_07
ReconstructMesh(image_path)
# step_08
# RefineMesh(image_path)
# step_09
TextureMesh(image_path)