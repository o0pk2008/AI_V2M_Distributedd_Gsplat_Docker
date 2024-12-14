import sqlite3
from app.config import Config
from app.utils import (
    get_db_connection,
    execute_with_retry
)

database_path = Config.DATABASE_PATH

# user 表增加新字段
# 注：对于已存在的表，添加字段时，无法直接获取时间戳做默认值，会报错
user_add_cols = {
    'nickname': 'nickname text default ""',
    'avatar': 'avatar text default ""',
    'phone': 'phone text default ""',
    # 'create_time': 'create_time datetime default ""',
    # 'update_time': 'update_time datetime default ""',
    # 'create_time': 'create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    # 'update_time': 'update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', # 每次记录更新时，自动更新时间戳
}

# projct 表新增的字段
project_add_cols = {
    'is_deleted': 'is_deleted integer default 0 not null',
}


# 检查字段是否存在
def column_exists(conn, table_name, column_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


# 给数据表添加字段
def add_columns(database_path, table_name, columns):
    conn = get_db_connection(database_path)
    cursor = conn.cursor()

    for column_name, sql_definition in columns.items():
        if not column_exists(conn, table_name, column_name):
            print(f"添加字段:{column_name}")
            cursor.execute(f"alter table {table_name} add column {sql_definition}")

    conn.commit()
    conn.close()


# 给所有表格添加要扩充的字段
def update_all_tables():
    add_columns(database_path, 'project', project_add_cols)
    add_columns(database_path, 'user', user_add_cols)