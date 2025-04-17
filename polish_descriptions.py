import requests
import json
import sqlite3
import time
import os

def get_db_connection():
    """连接到数据库"""
    # 使用正确的数据库文件
    db_path = 'travel_db.sqlite'
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"错误：数据库文件 '{db_path}' 不存在!")
        print(f"当前工作目录: {os.getcwd()}")
        print("请确保数据库文件路径正确")
        exit(1)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def verify_db_structure(conn):
    """验证数据库结构，确保表和列存在"""
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"数据库中的表: {tables}")
    
    # 检查是否有pois表或类似的表
    pois_table = None
    for table in tables:
        if 'poi' in table.lower():
            pois_table = table
            print(f"找到可能的POI表: {pois_table}")
            break
    
    if not pois_table:
        print("错误：无法找到包含POI数据的表!")
        return False, None
    
    # 获取表结构
    cursor.execute(f"PRAGMA table_info({pois_table});")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"表 '{pois_table}' 的列: {columns}")
    
    # 检查必要的列
    required_columns = ['id', 'name', 'description']
    missing_columns = [col for col in required_columns if col not in columns]
    
    if missing_columns:
        print(f"错误：表 '{pois_table}' 缺少必要的列: {missing_columns}")
        return False, None
    
    return True, pois_table

def polish_description(original_desc, poi_name):
    """使用通义千问API润色描述"""
    # API配置
    api_key = "sk-qircmatuqnhkurgdzzjcorkmttxnbisgecvzajjigsbeervq"  # 替换为您的API密钥
    api_url = "https://api.siliconflow.cn/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建提示，要求润色并限制字数
    prompt = f"请润色以下杭州景点'{poi_name}'的描述，使其更加生动精炼，严格控制在50字以内，不要使用标点符号计数：\n\n{original_desc}"
    
    payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": [
            {"role": "system", "content": "你是一位擅长简洁精炼文案的旅游内容编辑。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    try:
        # 发送请求
        response = requests.post(api_url, headers=headers, json=payload)
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                # 清理可能的引号和额外空格
                content = content.strip().strip('"').strip()
                # 确保不超过50个字
                if len(content) > 50:
                    content = content[:50]
                return content
        
        # 如果API调用失败，返回原描述
        print(f"为'{poi_name}'润色描述失败：{response.status_code}, {response.text}")
        return original_desc
    
    except Exception as e:
        print(f"润色'{poi_name}'描述时出错: {str(e)}")
        return original_desc

def update_all_descriptions():
    """更新所有POI的description字段"""
    print("开始更新景点描述...")
    
    conn = get_db_connection()
    try:
        # 验证数据库结构
        is_valid, pois_table = verify_db_structure(conn)
        if not is_valid:
            print("无法继续，数据库结构验证失败")
            return
        
        # 获取所有POI
        query = f'SELECT id, name, description FROM {pois_table}'
        print(f"执行查询: {query}")
        pois = conn.execute(query).fetchall()
        print(f"找到 {len(pois)} 个POI记录")
        
        if not pois:
            print("没有找到POI数据，请检查数据库内容")
            return
        
        updated_count = 0
        for poi in pois:
            poi_id = poi['id']
            poi_name = poi['name']
            original_desc = poi['description']
            
            print(f"处理景点 [{poi_id}] {poi_name}...")
            
            # 润色描述
            polished_desc = polish_description(original_desc, poi_name)
            
            # 如果描述有变化，更新数据库
            if polished_desc != original_desc:
                conn.execute(
                    f"UPDATE {pois_table} SET description = ? WHERE id = ?",
                    (polished_desc, poi_id)
                )
                updated_count += 1
                print(f"  原描述: {original_desc}")
                print(f"  新描述: {polished_desc}")
            else:
                print(f"  描述未变: {original_desc}")
            
            # 避免API限流，添加短暂延迟
            time.sleep(1)
        
        # 提交更改
        conn.commit()
        print(f"\n成功更新了 {updated_count} 个景点描述")
    
    except Exception as e:
        print(f"更新描述过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    update_all_descriptions() 