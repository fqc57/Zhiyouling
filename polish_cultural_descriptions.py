import requests
import json
import sqlite3
import time
import os

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
    
    return True, pois_table

def ensure_cultural_description_field(conn, pois_table):
    """确保数据库中有存储润色后的文化描述的字段"""
    cursor = conn.cursor()
    
    # 检查是否已有cultural_description字段
    cursor.execute(f"PRAGMA table_info({pois_table});")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'cultural_description' not in columns:
        print(f"向表 '{pois_table}' 添加 'cultural_description' 字段...")
        try:
            cursor.execute(f"ALTER TABLE {pois_table} ADD COLUMN cultural_description TEXT;")
            conn.commit()
            print("成功添加字段")
        except sqlite3.Error as e:
            print(f"添加字段时出错: {str(e)}")
            return False
    
    return True

def generate_cultural_description(poi):
    """生成景点的文化描述（从app_integrated.py中移植）"""
    preset_descriptions = {
        "西湖断桥": "断桥因《白蛇传》而闻名，是西湖爱情文化的象征。传说许仙与白娘子在此相遇，留下千古佳话。每到冬季，断桥积雪更是形成'断桥残雪'的绝美景观，为西湖十景之一。桥的东侧曾是城郊接壤处，商贸繁荣，至今周边仍有许多历史悠久的杭帮美食小店。",
        "雷峰塔": "雷峰塔建于北宋咸平三年(公元1000年)，是吴越国王钱俶为庆祝夫人黄氏得子而建。塔与《白蛇传》中白娘子被法海压在塔下的故事紧密相连，象征着对自由爱情的追求。现今的雷峰塔是2002年重建的，塔内收藏有大量佛教文物和出土文献，是了解南宋佛教文化和建筑艺术的重要场所。",
        "龙井村": "龙井村是西湖龙井茶的原产地，有'春风满面茶飘香'之美誉。村中最著名的是'十八棵御茶树'，相传为乾隆皇帝游览西湖时亲自册封的贡茶树。每年春季，这里举行传统茶文化活动，游客可以参与采茶、炒茶等体验，深入了解中国茶道文化的精髓，感受'一览众山小'的茶园风光。"
    }
    
    name = poi['name']
    
    # 如果数据库中已有cultural_description，则使用它
    if 'cultural_description' in poi and poi['cultural_description']:
        return poi['cultural_description']
    
    # 如果有预设描述，则使用预设
    if name in preset_descriptions:
        return preset_descriptions[name]
    
    # 否则生成一个通用描述
    description = poi['description'] if 'description' in poi else ""
    category = poi['category'] if 'category' in poi else "景点"
    visit_time = poi['visit_time'] if 'visit_time' in poi else 60
    
    # 获取景点文化标签（如果数据库有cultural_tags表）
    tags = []
    try:
        conn = get_db_connection()
        cursor = conn.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='cultural_tags';
        ''')
        if cursor.fetchone():
            cursor = conn.execute('''
                SELECT tag FROM cultural_tags 
                WHERE poi_id = ?
            ''', (poi['id'],))
            tags = [row['tag'] for row in cursor.fetchall()]
        conn.close()
    except:
        pass
    
    # 生成通用描述
    if tags:
        return f"{name}是杭州著名的{category}景点，{description}。这里蕴含着丰富的{', '.join(tags)}等文化元素，是了解杭州历史文化的重要窗口。游览时可以深入体验当地特色，感受杭州的独特魅力。建议花费{visit_time}分钟细细品味这里的文化底蕴。"
    else:
        return f"{name}是杭州著名的{category}景点，{description}。这里承载着丰富的历史文化，是了解杭州特色的重要窗口。游览时可以深入体验当地特色，感受杭州的独特魅力。建议花费{visit_time}分钟细细品味这里的文化底蕴。"

def polish_cultural_description(original_desc, poi_name):
    """使用通义千问API润色文化描述"""
    # API配置
    api_key = "sk-qircmatuqnhkurgdzzjcorkmttxnbisgecvzajjigsbeervq"  # 替换为您的API密钥
    api_url = "https://api.siliconflow.cn/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建提示，要求润色并限制字数
    prompt = f"""请润色以下杭州景点'{poi_name}'的文化描述，使其更加生动精炼，突出文化内涵和历史价值，严格控制在100字以内：

{original_desc}

请直接返回润色后的描述，不要加任何前缀或说明。"""
    
    payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": [
            {"role": "system", "content": "你是一位中国文化专家，擅长提炼景点的文化内涵，用优美简洁的语言表达。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 150
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
                # 确保不超过100个字
                if len(content) > 100:
                    content = content[:100]
                return content
        
        # 如果API调用失败，返回原描述
        print(f"为'{poi_name}'润色文化描述失败：{response.status_code}, {response.text}")
        return original_desc
    
    except Exception as e:
        print(f"润色'{poi_name}'文化描述时出错: {str(e)}")
        return original_desc

def update_all_cultural_descriptions():
    """更新所有POI的文化描述"""
    print("开始更新景点文化描述...")
    
    conn = get_db_connection()
    try:
        # 验证数据库结构
        is_valid, pois_table = verify_db_structure(conn)
        if not is_valid:
            print("无法继续，数据库结构验证失败")
            return
        
        # 确保数据库有cultural_description字段
        if not ensure_cultural_description_field(conn, pois_table):
            print("无法继续，无法创建cultural_description字段")
            return
        
        # 获取所有POI
        query = f'SELECT * FROM {pois_table}'
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
            
            # 生成原始文化描述
            original_desc = generate_cultural_description(dict(poi))
            
            print(f"处理景点 [{poi_id}] {poi_name}...")
            
            # 润色描述
            polished_desc = polish_cultural_description(original_desc, poi_name)
            
            # 如果描述有变化，更新数据库
            if polished_desc != original_desc:
                conn.execute(
                    f"UPDATE {pois_table} SET cultural_description = ? WHERE id = ?",
                    (polished_desc, poi_id)
                )
                updated_count += 1
                print(f"  原文化描述: {original_desc}")
                print(f"  新文化描述: {polished_desc}")
            else:
                print(f"  文化描述未变: {original_desc}")
            
            # 避免API限流，添加短暂延迟
            time.sleep(1)
        
        # 提交更改
        conn.commit()
        print(f"\n成功更新了 {updated_count} 个景点文化描述")
    
    except Exception as e:
        print(f"更新文化描述过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    update_all_cultural_descriptions()