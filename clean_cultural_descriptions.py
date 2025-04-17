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

def ensure_cultural_description_field(conn, table_name):
    """确保表中有cultural_description字段"""
    cursor = conn.cursor()
    
    # 检查字段是否存在
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'cultural_description' not in columns:
        print(f"表 {table_name} 中不存在cultural_description字段，正在添加...")
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN cultural_description TEXT;")
            conn.commit()
            print("成功添加cultural_description字段")
            return True
        except Exception as e:
            print(f"添加字段时出错: {str(e)}")
            return False
    else:
        print(f"表 {table_name} 已存在cultural_description字段")
        return True

def display_sample_data(conn, table_name):
    """显示几个包含无意义值的样本数据"""
    cursor = conn.cursor()
    bad_values = ["nan", "normal", "0.0", "desc", "20240624", "video", "title"]
    
    print("\n=== 显示包含无意义值的样本 ===")
    for bad_value in bad_values:
        cursor.execute(
            f"SELECT id, name, cultural_description FROM {table_name} " +
            f"WHERE cultural_description LIKE ? AND cultural_description IS NOT NULL LIMIT 2", 
            (f'%{bad_value}%',)
        )
        
        rows = cursor.fetchall()
        if rows:
            print(f"\n找到 {len(rows)} 条包含 '{bad_value}' 的记录:")
            for row in rows:
                print(f"[{row['id']}] {row['name']}")
                print(f"文化描述: {row['cultural_description']}")
                print("-" * 70)

def clean_cultural_descriptions(conn, table_name):
    """彻底清理cultural_description字段中的无意义值"""
    cursor = conn.cursor()
    
    # 显示几个样本
    display_sample_data(conn, table_name)
    
    # 获取带有cultural_description的所有POI
    cursor.execute(f"SELECT id, name, cultural_description FROM {table_name} WHERE cultural_description IS NOT NULL")
    pois = cursor.fetchall()
    print(f"\n开始处理 {len(pois)} 条记录...")
    
    # 定义需要清理的无意义值
    bad_values = ["nan", "normal", "0.0", "desc", "20240624", "video", "title"]
    
    # 统计信息
    updated_count = 0
    empty_count = 0
    
    # 处理每个POI
    for poi in pois:
        poi_id = poi['id']
        name = poi['name']
        desc = poi['cultural_description']
        
        # 跳过空值
        if desc is None or desc.strip() == '':
            empty_count += 1
            continue
        
        # 保存原始描述
        original_desc = desc
        cleaned_desc = desc
        
        # 使用多种模式进行清理
        for bad_value in bad_values:
            # 1. 清理作为完整单词的值 (如 "nan", " nan ", "nan.")
            cleaned_desc = re.sub(r'\b' + re.escape(bad_value) + r'\b', '', cleaned_desc, flags=re.IGNORECASE)
            
            # 2. 清理作为普通文本的值
            cleaned_desc = re.sub(re.escape(bad_value), '', cleaned_desc, flags=re.IGNORECASE)
            
            # 3. 清理JSON格式值 (如 "desc": "value")
            cleaned_desc = re.sub(r'"' + re.escape(bad_value) + r'":', '', cleaned_desc, flags=re.IGNORECASE)
            cleaned_desc = re.sub(r'"' + re.escape(bad_value) + r'"', '', cleaned_desc, flags=re.IGNORECASE)
            
            # 4. 清理作为标签的值 (如 "title: something")
            cleaned_desc = re.sub(re.escape(bad_value) + r':', '', cleaned_desc, flags=re.IGNORECASE)
            cleaned_desc = re.sub(re.escape(bad_value) + r'=', '', cleaned_desc, flags=re.IGNORECASE)
        
        # 清理多余的空格、标点和格式
        cleaned_desc = re.sub(r'\s+', ' ', cleaned_desc)  # 多个空格变一个
        cleaned_desc = re.sub(r':\s*:', ':', cleaned_desc)  # 连续冒号
        cleaned_desc = re.sub(r',,', ',', cleaned_desc)     # 连续逗号
        cleaned_desc = cleaned_desc.strip()
        
        # 如果描述发生变化，更新数据库
        if cleaned_desc != original_desc:
            print(f"清理 [{poi_id}] {name} 的文化描述:")
            print(f"  原始: {original_desc}")
            print(f"  清理后: {cleaned_desc}")
            
            cursor.execute(
                f"UPDATE {table_name} SET cultural_description = ? WHERE id = ?",
                (cleaned_desc, poi_id)
            )
            updated_count += 1
            
            # 每10条记录显示一次进度
            if updated_count % 10 == 0:
                print(f"已处理 {updated_count} 条记录...")
    
    # 提交更改
    conn.commit()
    print(f"\n清理完成: 更新了 {updated_count} 条记录，跳过了 {empty_count} 条空记录")
    
    # 验证清理结果
    print("\n=== 验证清理结果 ===")
    for bad_value in bad_values:
        cursor.execute(
            f"SELECT COUNT(*) as count FROM {table_name} " +
            f"WHERE cultural_description LIKE ? AND cultural_description IS NOT NULL", 
            (f'%{bad_value}%',)
        )
        count = cursor.fetchone()['count']
        print(f"仍然包含 '{bad_value}' 的记录数: {count}")

def main():
    print("开始彻底清理cultural_description字段...")
    
    try:
        # 连接数据库
        conn = get_db_connection()
        
        # 查找包含POI数据的表
        pois_table = find_pois_table(conn)
        if not pois_table:
            print("错误：未找到包含POI数据的表")
            return
            
        # 确保表中有cultural_description字段
        if not ensure_cultural_description_field(conn, pois_table):
            print("错误：无法确保cultural_description字段存在")
            return
            
        # 清理cultural_description字段
        clean_cultural_descriptions(conn, pois_table)
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 