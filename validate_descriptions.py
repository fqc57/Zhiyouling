import sqlite3
import os
import re

def get_db_connection():
    """连接到数据库"""
    db_path = 'travel_db.sqlite'
    
    if not os.path.exists(db_path):
        print(f"错误：数据库文件 '{db_path}' 不存在!")
        print(f"当前工作目录: {os.getcwd()}")
        print("请确保数据库文件路径正确")
        exit(1)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def find_pois_table(conn):
    """查找包含POI数据的表"""
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"数据库中的表: {tables}")
    
    # 查找可能的POI表
    pois_table = None
    for table in tables:
        if 'poi' in table.lower():
            # 检查表是否有cultural_description字段
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [row[1] for row in cursor.fetchall()]
            if 'cultural_description' in columns:
                pois_table = table
                print(f"找到包含cultural_description字段的表: {pois_table}")
                break
    
    # 如果没有找到带cultural_description的POI表，尝试找任何POI表
    if not pois_table:
        for table in tables:
            if 'poi' in table.lower():
                pois_table = table
                print(f"找到可能的POI表（但无cultural_description字段）: {pois_table}")
                break
    
    return pois_table

def show_sample_descriptions(conn, table_name):
    """显示数据库中cultural_description字段的样本内容"""
    cursor = conn.cursor()
    
    # 获取所有包含指定无意义值的记录
    bad_values = ["nan", "normal", "0.0", "desc", "20240624", "video", "title"]
    
    print("\n=== 包含特定无意义值的记录 ===")
    for bad_value in bad_values:
        # 使用LIKE查询查找包含特定值的记录
        cursor.execute(f"SELECT id, name, cultural_description FROM {table_name} WHERE cultural_description LIKE ? AND cultural_description IS NOT NULL LIMIT 5", (f'%{bad_value}%',))
        rows = cursor.fetchall()
        
        if rows:
            print(f"\n找到 {len(rows)} 条包含 '{bad_value}' 的记录:")
            for row in rows:
                print(f"[{row['id']}] {row['name']}")
                print(f"文化描述: {row['cultural_description']}")
                
                # 使用不同的正则表达式尝试匹配
                tests = [
                    (f"作为单词边界: '\\b{bad_value}\\b'", re.search(r'\b' + re.escape(bad_value) + r'\b', row['cultural_description']) is not None),
                    (f"作为部分文本: '{bad_value}'", bad_value in row['cultural_description']),
                    (f"作为JSON键: '\"{bad_value}\":'", f'"{bad_value}":' in row['cultural_description']),
                    (f"作为标签: '{bad_value}:'", f'{bad_value}:' in row['cultural_description']),
                    (f"大写形式: '{bad_value.upper()}'", bad_value.upper() in row['cultural_description'].upper()),
                ]
                
                print("检测结果:")
                for desc, result in tests:
                    print(f"  - {desc}: {'✓' if result else '✗'}")
                print("-" * 80)

def clean_description_completely(text, bad_values):
    """彻底清理文本中的所有指定值"""
    if text is None:
        return None
        
    cleaned = text
    
    # 尝试多种清理方法
    for bad_value in bad_values:
        # 清理各种形式
        patterns = [
            re.escape(bad_value),                      # 精确匹配
            r'"' + re.escape(bad_value) + r'"',        # 引号包围
            r'"' + re.escape(bad_value) + r'"' + r':', # JSON键
            re.escape(bad_value) + r':',               # 标签形式
            r'\b' + re.escape(bad_value) + r'\b',      # 单词边界
            re.escape(bad_value) + r'=',               # 等号形式
        ]
        
        # 对每个模式进行清理（大小写不敏感）
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # 清理多次处理造成的多余空格
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r':\s+:', ':', cleaned)  # 清理可能的连续冒号
    cleaned = re.sub(r',,', ',', cleaned)     # 清理连续逗号
    
    return cleaned

def validate_and_fix_descriptions(conn, table_name):
    """验证并修复所有cultural_description记录"""
    cursor = conn.cursor()
    
    # 首先展示一些样本
    show_sample_descriptions(conn, table_name)
    
    # 询问用户是否继续清理
    response = input("\n是否进行彻底清理? (y/n): ")
    if response.lower() != 'y':
        print("操作已取消")
        return
    
    # 获取所有记录
    cursor.execute(f"SELECT id, name, cultural_description FROM {table_name} WHERE cultural_description IS NOT NULL")
    rows = cursor.fetchall()
    print(f"\n开始清理 {len(rows)} 条记录...")
    
    # 定义无意义值
    bad_values = ["nan", "normal", "0.0", "desc", "20240624", "video", "title"]
    
    # 统计
    updated_count = 0
    
    # 处理每条记录
    for row in rows:
        original = row['cultural_description']
        cleaned = clean_description_completely(original, bad_values)
        
        if cleaned != original:
            # 更新记录
            cursor.execute(f"UPDATE {table_name} SET cultural_description = ? WHERE id = ?", (cleaned, row['id']))
            updated_count += 1
            
            # 每10条记录显示一次进度
            if updated_count % 10 == 0:
                print(f"已处理 {updated_count} 条记录...")
    
    # 提交更改
    conn.commit()
    print(f"\n清理完成: 更新了 {updated_count} 条记录")
    
    # 验证清理结果
    print("\n=== 验证清理结果 ===")
    for bad_value in bad_values:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name} WHERE cultural_description LIKE ? AND cultural_description IS NOT NULL", (f'%{bad_value}%',))
        count = cursor.fetchone()['count']
        print(f"仍然包含 '{bad_value}' 的记录数: {count}")

def main():
    print("开始验证cultural_description字段...")
    
    try:
        # 连接数据库
        conn = get_db_connection()
        
        # 查找包含POI数据的表
        pois_table = find_pois_table(conn)
        if not pois_table:
            print("错误：未找到包含POI数据的表")
            return
        
        # 验证并修复描述
        validate_and_fix_descriptions(conn, pois_table)
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 