import sqlite3
from app.config import Config
from app.utils import (
    get_db_connection,
    execute_with_retry
)

database_path = Config.DATABASE_PATH

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