#
# app 端 api 实现
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
app_api_bp = Blueprint('app_api_bp', __name__)

# 获取配置数据
database_path = Config.DATABASE_PATH
updata_url = Config.UPDATA_URL
edit_url = Config.EDIT_URL
CloudStorage = Config.CLOUD_STORAGE
ClientIP = Config.ClientIP


# 注册账号
@app_api_bp.route('/app_api/v1/signup', methods=['POST'])
def handle_signup():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirmPassword = data.get('confirmPassword')

        # 必填项验证
        if not username:
            return jsonify({
                'status': 'error',
                'message': 'Username is required.',
            })
        elif not email:
            return jsonify({
                'status': 'error',
                'message': 'Email is required.',
            })
        elif not password:
            return jsonify({
                'status': 'error',
                'message': 'Password is required.',
            })
        elif not confirmPassword:
            return jsonify({
                'status': 'error',
                'message': 'Confirm password is required.'
            })

        # 邮箱合法性校验
        if not is_valid_email(email):
            return jsonify({
                'status': 'error',
                'message': 'Please provide a valid email address.'
            })
            
        # 密码校验（两次是否一致）
        if password != confirmPassword:
            return jsonify({
                'status': 'error',
                'message': 'Passwords do not match.'
            })


        # 连接数据库
        conn = get_db_connection(database_path)
        cursor = conn.cursor()

        # 用户名校验（用户名不能重复）
        check_username = '''
            select id from user 
            where username = ?
        '''
        
        cursor.execute(check_username, (username,))
        check_username_result = cursor.fetchone()

        if check_username_result:
            return jsonify({
                'status': 'error',
                'message': 'Username already exists. Please choose a different one.',
            })

        # 邮箱校验 (邮箱不能重复)
        check_email = '''
            select id from user
            where email = ?
        '''
        cursor.execute(check_email, (email,))
        check_email_result = cursor.fetchone()

        if check_email_result:
            return jsonify({
                'status': 'error',
                'message': 'Email already exists. Please choose a different one.',
            })
        
        # 密码加密
        # hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        
        # 注册用户
        signup_sql = '''
            insert into user 
            (username, email, password, review)
            values (?, ?, ?, ?)
        '''
        
        # 密码加密版
        # cursor.execute(signup_sql, (username, email, hashed_password.decode('utf-8'), 1))
        cursor.execute(signup_sql, (username, email, password, 1))
        conn.commit()
        conn.close()

        # 注册成功
        return jsonify({
            'status': 'success',
            'message': 'Registration successful. Welcome aboard!'
        }), 200

    except IntegrityError as e:  # 处理数据库约束错误
        return jsonify({
            'status': 'error',
            'message': 'Database error: Unable to register user.',
            'details': str(e)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred.',
            'details': str(e)
        })



# 登录账号
@app_api_bp.route('/app_api/v1/signin', methods=['POST'])
def handle_signin():
    try:
        request_data = request.json
        account = request_data.get('account')
        password = request_data.get('password')

        # 判断账户是 用户名还是邮箱
        if is_valid_email(account):
            # 如果邮箱校验合法，则是邮箱
            signin_sql = '''
                select id, username, email, password, review, avatar from user
                where email = ?
            '''
        else:
            # 是用户名(note:有一个风险，如果用户名也是邮箱格式，则会误判，需要限制用户名格式)
            signin_sql = '''
                select id, username, email, password, review, avatar from user
                where username = ?
            ''' 

        # 连接数据库
        conn = get_db_connection(database_path)
        cursor = conn.cursor()

        # 检测用户是否存在
        cursor.execute(signin_sql, (account,))
        user = cursor.fetchone()

        # 用户不存在
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'The account does not exist. Please check your username or email.'
            })

        # 解包查询结果
        user_id, username, email, stored_password, review, avatar = user

        # 密码错误
        if password != stored_password:
            return jsonify({
                'status': 'error',
                'message': 'Incorrect password. Please try again.'
            })

        # 账号审核中
        if review != 1:
            return jsonify({
                'status': 'error',
                'message': 'Your account is under review. Please wait for approval.'
            })
        
        # 所有条件都通过，登录成功
        return jsonify({
            'status': 'success',
            'message': 'Login successful. Welcome back!',
            'data': {
                'user_id': user_id,
                'username': username,
                'email': email,
                'review': review,
                'avatar': avatar
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'database error',
            'details': str(e)
        })



# 获取物件列表 Captures | Explore (包含搜索)
@app_api_bp.route('/app_api/v1/objects', methods=['POST'])
def get_Objects():
    data = request.json # 传入的参数
    user_id = data.get('user_id') # 用户 id
    page_num = int(data.get('page', 1)) # 请求的页面
    search = data.get('search', '') # 搜索关键字
    limit = int(data.get('limit', 18)) # 每页数量
    cacl_status = int(data.get('project_state', -1)) # 指定的物件状态（0计算中， 计算完成1）
    object_type = data.get('type', '') # 查询的类型 Captures | Explore

    try:
        # 校验分页参数
        if page_num <= 0 or limit <= 0:
            return jsonify({
                'status': 'error',
                'message': 'Invalid pagination parameters'
            })

        # 构建分页的偏移量
        offset = (page_num - 1) * limit


        # 连接数据库
        conn = get_db_connection(database_path)
        cursor = conn.cursor()

        # 根据类型动态查询
        if object_type == 'Captures':
            # 查询用户自己的数据
            if cacl_status == -1:
                query = f'''
                    select * from project
                    where project_user_id = ?
                    and is_deleted = 0 
                    and project_title like ?
                    order by project_id desc
                    limit ? offset ? 
                '''
                cursor.execute(query, (user_id, f"%{search}%", limit, offset))
            else:
                # 查询不同计算状态的物件列表
                query = f'''
                    select * from project
                    where project_user_id = ?
                    and project_state = ?
                    and is_deleted = 0 
                    and project_title like ?
                    order by project_id desc
                    limit ? offset ? 
                '''
                cursor.execute(query, (user_id, cacl_status, f"%{search}%", limit, offset))
            object_data = cursor.fetchall()

            # 统计用户自己的数据
            count_query = '''
                select count(*) from project 
                where project_user_id = ?
                and is_deleted = 0
            '''

            count_params = (user_id,)

        elif object_type == 'Explore':
            # 查询其他用户公开数据
            query = '''
                select * from project
                where project_user_id !=?
                and project_public = 1
                and is_deleted = 0
                and project_title like ?
                order by project_id desc
                limit ? offset ?
            '''

            cursor.execute(query, (user_id, f"%{search}%", limit, offset))
            object_data = cursor.fetchall()

            # 统计其他用户公开数据
            count_query = '''
                select count(*) from project
                where project_user_id != ?
                and project_public = 1
                and is_deleted = 0
            '''

            count_params = (user_id,)

        else:
            # 不支持查询类型
            return jsonify({
                'status': 'error',
                'message': 'Invalid object type'
            })

        
        # 获取查询结果
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        data = [dict(zip(column_names, row)) for row in object_data]

        # 执行计数查询
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]

        # 关闭连接
        conn.close()


        # 返回查询结果
        return jsonify({
            'status': 'success',
            'data': data,
            'updata_http': updata_url,
            'edit_http': edit_url,
            'pagination': {
                'current_page': page_num,
                'total_pages': (total_count + limit - 1) // limit, 
                'total_count': total_count,
                'per_page': limit
                
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'database error',
            'details': str(e)
        })
    finally:
        conn.close() # 关闭数据库连接



# 删除多个物件
@app_api_bp.route('/app_api/v1/objects', methods=['DELETE'])
def delete_Objects():
    try:
        # 获取请求体中的 project_id 列表
        data = request.json
        project_ids = data.get('project_ids', []) # 必须传入 project_ids 列表
        user_id = data.get('user_id')

        # 校验参数是否有效
        if not project_ids or not isinstance(project_ids, list):
            return jsonify({
                'status': 'error',
                'message': 'Invalid project_ids. Please provide a list of IDs.'
            })

        # 连接数据库
        conn = get_db_connection(database_path)
        cursor = conn.cursor()

        # 检查每个 project_id 是否存在，并尝试删除
        deleted_ids = []
        not_found_ids = []

        query_sql = '''
            select * from project
            where project_id = ?
            and project_user_id = ?
            and is_deleted = 0
        '''

        delete_sql = '''
            update project set is_deleted = 1
            where project_id = ?
            and project_user_id = ?
        '''

        for project_id in project_ids:
            cursor.execute(query_sql, (project_id, user_id,))
            project = cursor.fetchone()

            if project: # 物件存在
                cursor.execute(delete_sql, (project_id, user_id,))
                deleted_ids.append(project_id)
            else: # 物件不存在或已被删除
                not_found_ids.append(project_id)

        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': 'Batch deletion completed.',
            'deleted_ids': deleted_ids,
            'not_found_ids': not_found_ids
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'database error',
            'details': str(e)
        }) 



# 获取单个物件详情
@app_api_bp.route('/app_api/v1/objects/<int:project_id>', methods=['POST'])
def get_object(project_id):
    try:
        data = request.json # 传入的参数
        user_id = data.get('user_id') # 用户 id

        # 连接数据库
        conn = get_db_connection(database_path)
        cursor = conn.cursor()

        # 查询物件信息
        query = '''
            select * from project
            where project_id = ?
            and project_user_id = ?
            and is_deleted = 0
        '''

        cursor.execute(query, (project_id, user_id, ))
        object_data = cursor.fetchone() # 查询的结果

        object_info = None # 设置返回的数据

        if object_data:
            export_info = {
                'export_obj_progress': object_data['export_obj_progress'],
                'export_obj_state': object_data['export_obj_state'], 
                'export_gltf_state': object_data['export_gltf_state'], 
                'export_fbx_state': object_data['export_fbx_state'], 
                'export_ply_state': object_data['export_ply_state'], 
                'export_3ds_state': object_data['export_3ds_state'],
                'export_x_state': object_data['export_x_state'], 
                'export_stl_state': object_data['export_stl_state'], 
                'export_mesh': object_data['export_mesh'],
            }
            crop_info = {
                'CropPosition': object_data['CropPosition'], 
                'CropScale': object_data['CropScale'], 
                'CropRotation': object_data['CropRotation'],
            }
            nerfacto_info = {
                'nerfacto_config_path': object_data['nerfacto_config_path'],
                'nerfacto_progress': object_data['nerfacto_progress'], 
                'nerfacto_status': object_data['nerfacto_status'], 
            }
            object_info = {
                'project_id': object_data['project_id'],
                'project_name': object_data['project_name'], 
                'project_date': object_data['project_date'],
                'project_user': object_data['project_user'],
                'project_title': object_data['project_title'], 
                'project_public': object_data['project_public'], 
                'project_state': object_data['project_state'], 
                'project_progress': object_data['project_progress'], 
                'project_edit': object_data['project_edit'], 
                'project_down_num': object_data['project_down_num'], 
                'project_like_num': object_data['project_like_num'], 
                'project_user_id': object_data['project_user_id'], 
                'project_color': object_data['project_color'], 
                'export': export_info,
                'crop': crop_info,
                'nerfacto': nerfacto_info,
                "updata_http": updata_url, 
                "edit_http": edit_url,
                "client_ip": ClientIP
            }

        cursor.close()
        conn.close()

        return jsonify({
            'status': 'success',
            'data': object_info
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'database error',
            'details': str(e)
        })   



# 编辑单个物件属性（名称、是否公开）
@app_api_bp.route('/app_api/v1/objects/<int:project_id>', methods=['PUT'])
def edit_object(project_id):
    try:
        # 获取请求体数据
        data = request.json
        user_id = data.get('user_id')  # 确保传入 user_id 验证权限

        # 检查是否传入需要更新的字段
        updatable_fields = [
            "project_title",  # 物件名称
            "project_public", # 物件是否公开
            "project_down_num", # 物件下载数量
            "project_like_num", # 物件点赞量
        ]

        updates = {key: value for key, value in data.items() if key in updatable_fields}

        if not updates:
            return jsonify({
                "status": "error",
                "message": "No valid fields provided to update."
            })

        # 检查物件是否存在并属于当前用户
        conn = get_db_connection(database_path)
        cursor = conn.cursor()
        check_query = '''
            SELECT * FROM project 
            WHERE project_id = ? AND project_user_id = ? AND is_deleted = 0
        '''
        cursor.execute(check_query, (project_id, user_id))
        project = cursor.fetchone()

        if not project:
            return jsonify({
                "status": "error",
                "message": "Object not found or permission denied."
            })

        # 动态生成更新 SQL 语句
        update_clauses = ", ".join([f"{key} = ?" for key in updates.keys()])
        update_values = list(updates.values())
        update_query = f'''
            UPDATE project
            SET {update_clauses}
            WHERE project_id = ? AND project_user_id = ?
        '''

        # 执行更新操作
        cursor.execute(update_query, update_values + [project_id, user_id])
        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Object updated successfully.",
            "updated_fields": updates
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Database error",
            "details": str(e)
        })



# 删除单个物件
@app_api_bp.route('/app_api/v1/objects/<int:project_id>', methods=['DELETE'])
def delete_object(project_id):
    try:
        data = request.json # 传入的参数
        user_id = data.get('user_id') # 用户 id

        # 连接数据库
        conn = get_db_connection(database_path)
        cursor = conn.cursor()

        # 查询物件是否存在
        query = '''
            select * from project
            where project_id = ?
            and project_user_id = ?
        '''
        cursor.execute(query, (project_id, user_id))
        project = cursor.fetchone()

        if not project:
            return jsonify({
                'status': 'error',
                'message': f'Object with id {project_id} not found'
            })

        # 删除记录（标记删除）
        delete_sql = '''
            update project set is_deleted = 1
            where project_id = ?
        '''
        cursor.execute(delete_sql, (project_id,))
        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': f'Object with id {project_id} has been deleted.'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'database error',
            'details': str(e)
        })    



# 物件数据上传
@app_api_bp.route('/app_api/v1/upload', methods=['POST'])
def upload_object():
    print('app端：开始物件上传')
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                return jsonify({
                    'status': 'error',
                    'message': 'No file selected.'
                })

            file = request.files['file']

            if file.filename == '':
                return jsonify({
                    'status': 'error',
                    'message': 'File name is empty.'
                })

            if not allowed_file(file.filename):
                return jsonify({
                    'status': 'error',
                    'message': 'Unsupported file format.'
                })

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
            name = request.form.get('project_title')
            # 获取浏览权限
            privacy = request.form.get('project_public')
            # 获取用户信息（todo：应该不是传入）
            user_name = request.form.get('username')
            # 获取用户信息（todo：应该不是传入）
            user_id = request.form.get('user_id')
            # 获取是否计算mesh, 默认为 0
            # export_mesh = request.form.get('export_mesh')
            export_mesh = 0

            if name:
                # 调用保存到数据库的函数
                save_to_database(folder_name, name ,privacy,user_name,user_id,export_mesh)
            else:
                # 调用保存到数据库的函数
                save_to_database(folder_name,'default',privacy,user_name,user_id,export_mesh)
            
            print('app端：保存视频到数据库')

            # 使用回调从线程获取状态
            # status_callback = StatusCallback()
            # thread = FFMpegThread(target=run_ffmpeg, args=(folder_path, file_path, folder_name, status_callback))
            # thread.start()

            # 等待线程完成
            # thread.join()

            # 从回调中获取状态
            # status = status_callback.get_status()
            
            # 请求GPU_Manager服务器进行运算
            send_task_to_GPU_Manager(file_path, folder_name, export_mesh)
            print('app端：请求GPU_Manager服务器进行运算')

            # 继续执行回调
            return jsonify({
                "status": 'success',
                "folder_path": folder_path, 
                "file_path": file_path, 
                "folder_name": folder_name, 
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'database error',
            'details': str(e)
        }) 