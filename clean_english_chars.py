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
    
    return pois_table

def display_sample_english(conn, table_name):
    """显示包含英文字母的样本数据"""
    cursor = conn.cursor()
    
    # 查找包含英文字母的记录
    cursor.execute(
        f"SELECT id, name, cultural_description FROM {table_name} " +
        f"WHERE cultural_description REGEXP '[a-zA-Z]' AND cultural_description IS NOT NULL LIMIT 5"
    )
    
    try:
        rows = cursor.fetchall()
        if rows:
            print(f"\n找到 {len(rows)} 条包含英文字母的记录:")
            for row in rows:
                print(f"[{row['id']}] {row['name']}")
                print(f"原文化描述: {row['cultural_description']}")
                
                # 预览清理效果
                cleaned = clean_english_chars(row['cultural_description'])
                print(f"清理后预览: {cleaned}")
                print("-" * 70)
        else:
            print("使用REGEXP查询失败，尝试使用LIKE查询...")
            # SQLite可能不支持REGEXP，使用LIKE代替
            display_sample_english_like(conn, table_name)
    except sqlite3.OperationalError:
        print("数据库不支持REGEXP查询，尝试使用LIKE查询...")
        display_sample_english_like(conn, table_name)

def display_sample_english_like(conn, table_name):
    """使用LIKE查询显示样本数据"""
    cursor = conn.cursor()
    
    # 使用LIKE匹配一些常见英文字母
    english_patterns = ['%a%', '%e%', '%i%', '%o%', '%u%', '%t%', '%s%']
    
    rows = []
    for pattern in english_patterns:
        cursor.execute(
            f"SELECT id, name, cultural_description FROM {table_name} " +
            f"WHERE cultural_description LIKE ? AND cultural_description IS NOT NULL LIMIT 2", 
            (pattern,)
        )
        rows.extend(cursor.fetchall())
        if len(rows) >= 5:
            break
    
    if rows:
        print(f"\n找到 {len(rows)} 条可能包含英文字母的记录:")
        for row in rows:
            print(f"[{row['id']}] {row['name']}")
            print(f"原文化描述: {row['cultural_description']}")
            
            # 预览清理效果
            cleaned = clean_english_chars(row['cultural_description'])
            print(f"清理后预览: {cleaned}")
            print("-" * 70)
    else:
        print("未找到包含英文字母的样本记录")

def clean_english_chars(text):
    """清理文本中的英文字母"""
    if text is None:
        return None
    
    # 1. 替换英文单词和字母序列
    cleaned = re.sub(r'[a-zA-Z]+', '', text)
    
    # 2. 清理可能留下的标点和多余空格
    cleaned = re.sub(r'\s+', ' ', cleaned)  # 合并多余空格
    cleaned = re.sub(r'[,，]{2,}', '，', cleaned)  # 合并连续逗号
    cleaned = re.sub(r'[:：]{2,}', '：', cleaned)  # 合并连续冒号
    cleaned = re.sub(r'[""]+"', '"', cleaned)  # 清理连续引号
    
    # 3. 清理失去内容的括号
    cleaned = re.sub(r'\(\s*\)', '', cleaned)
    cleaned = re.sub(r'\[\s*\]', '', cleaned)
    cleaned = re.sub(r'【\s*】', '', cleaned)
    
    return cleaned.strip()

def clean_all_english(conn, table_name):
    """清理所有记录中的英文字母"""
    cursor = conn.cursor()
    
    # 首先显示一些样本
    display_sample_english(conn, table_name)
    
    # 询问用户是否继续
    response = input("\n是否清理所有记录中的英文字母? (y/n): ")
    if response.lower() != 'y':
        print("操作已取消")
        return
    
    # 获取所有非空记录
    cursor.execute(f"SELECT id, name, cultural_description FROM {table_name} WHERE cultural_description IS NOT NULL")
    rows = cursor.fetchall()
    print(f"\n开始处理 {len(rows)} 条记录...")
    
    # 统计信息
    updated_count = 0
    
    # 处理每条记录
    for row in rows:
        original = row['cultural_description']
        cleaned = clean_english_chars(original)
        
        # 如果有变化，更新记录
        if cleaned != original:
            cursor.execute(
                f"UPDATE {table_name} SET cultural_description = ? WHERE id = ?",
                (cleaned, row['id'])
            )
            updated_count += 1
            
            # 输出进度
            if updated_count % 10 == 0:
                print(f"已处理 {updated_count} 条记录...")
    
    # 提交更改
    conn.commit()
    print(f"\n清理完成: 更新了 {updated_count} 条记录")

def main():
    print("开始清理cultural_description字段中的英文字母...")
    
    try:
        # 连接数据库
        conn = get_db_connection()
        
        # 查找包含POI数据的表
        pois_table = find_pois_table(conn)
        if not pois_table:
            print("错误：未找到包含POI数据的表")
            return
        
        # 清理所有英文字母
        clean_all_english(conn, pois_table)
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()