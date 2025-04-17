#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
POI自动分类脚本

该脚本使用DeepSeek LLM对旅游景点(POI)进行分类，
并将分类结果存储到travel_db.sqlite数据库中的新字段。
"""

import sqlite3
import time
import sys

# 尝试导入Ark SDK，如果不可用则退出
try:
    from volcenginesdkarkruntime import Ark
    # 初始化Ark客户端
    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key="0c2d99af-ab7d-4925-8b3d-6d645015c443",
    )
    print("成功初始化Ark SDK客户端，将使用真实LLM进行分类")
except ImportError:
    print("错误：无法导入Ark SDK，请确保已安装volcenginesdkarkruntime库")
    print("可通过运行 pip install volcenginesdkarkruntime 安装")
    print("程序将退出")
    sys.exit(1)

# 创建SQLite数据库连接
def get_db_connection():
    conn = sqlite3.connect('travel_db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

# 检查并创建category_type字段
def ensure_category_type_field():
    """确保数据库中存在category_type字段，如果不存在则创建"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取pois表的结构信息
    cursor.execute("PRAGMA table_info(pois)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # 如果字段不存在，添加新字段
    if 'category_type' not in columns:
        print("在pois表中添加category_type字段...")
        cursor.execute("ALTER TABLE pois ADD COLUMN category_type TEXT")
        conn.commit()
        print("字段添加成功")
    else:
        print("category_type字段已存在")
    
    conn.close()

# 自动对POI进行分类
def classify_pois():
    print("开始自动对POI进行分类...")
    try:
        # 确保数据库中有category_type字段
        ensure_category_type_field()
        
        # 获取所有POI数据
        conn = get_db_connection()
        pois = conn.execute('SELECT id, name, description, category, category_type FROM pois').fetchall()
        pois = [dict(poi) for poi in pois]
        
        # graph/poi.py中定义的分类列表
        valid_categories = [
            "自然景观", "历史古迹", "文化场所", "购物区域", "美食街区"
        ]
        
        # 类别颜色映射
        category_colors = {
            "自然景观": "#2c7bb6",
            "历史古迹": "#d7191c",
            "文化场所": "#fdae61",
            "购物区域": "#abd9e9",
            "美食街区": "#66bd63"
        }
        
        # 已分类和待分类的POIs
        already_classified = []
        to_be_classified = []
        
        # 检查哪些POI需要分类
        for poi in pois:
            if poi['category_type'] in valid_categories:
                already_classified.append(poi)
            else:
                to_be_classified.append(poi)
        
        # 如果没有需要分类的POI，直接返回
        if not to_be_classified:
            print(f"所有POI已经有正确的分类，共{len(already_classified)}个")
            conn.close()
            return
        
        # 构建系统提示
        system_prompt = f"""
        你是一个旅游景点分类专家。请根据POI的名称和描述，将其分类到以下预定义的类别之一：
        {', '.join(valid_categories)}
        
        每次只返回一个最合适的类别名称，不要提供解释。
        
        分类标准：
        - 自然景观：包括湖泊、公园、山川、植物园等自然景点
        - 历史古迹：包括古塔、古桥、古寺庙、历史遗址等具有历史意义的建筑或地点
        - 文化场所：包括博物馆、艺术馆、文化街区、展览馆等文化体验场所
        - 购物区域：包括商业街、购物中心、特色商店街等
        - 美食街区：以餐饮和美食体验为主的区域
        """
        
        # 逐个调用LLM对每个POI进行分类
        classified_count = 0
        for poi in to_be_classified:
            # 构建用户提示
            user_prompt = f"POI名称：{poi['name']}\n描述：{poi['description']}\n请从以下类别中为这个POI分类：自然景观, 历史古迹, 文化场所, 购物区域, 美食街区"
            
            try:
                # 调用LLM API
                response = client.chat.completions.create(
                    model="deepseek-r1-distill-qwen-32b-250120",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    stream=False
                )
                
                # 从响应中提取分类结果
                content = response.choices[0].message.content.strip()
                
                # 确保分类结果在有效类别中
                if content in valid_categories:
                    category = content
                else:
                    # 如果返回的不是预定义类别，尝试匹配最相近的
                    for valid_cat in valid_categories:
                        if valid_cat in content:
                            category = valid_cat
                            break
                    else:
                        # 如果没有匹配，使用默认类别
                        category = "文化场所"
                
                # 更新数据库
                conn.execute(
                    "UPDATE pois SET category_type = ? WHERE id = ?",
                    (category, poi['id'])
                )
                
                print(f"将POI '{poi['name']}' 分类为 '{category}'")
                classified_count += 1
                
                # 避免过快发送请求
                time.sleep(0.5)
                
            except Exception as e:
                print(f"分类 '{poi['name']}' 时出错: {str(e)}")
                continue
        
        # 提交所有更改
        conn.commit()
        conn.close()
        
        print(f"成功为 {classified_count} 个POI分类，之前已有 {len(already_classified)} 个POI分类完成")
        print(f"总POI数量: {len(pois)}")
        
    except Exception as e:
        print(f"POI自动分类过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()

# 如果直接运行该脚本
if __name__ == "__main__":
    print("POI自动分类脚本启动")
    classify_pois()
    print("分类完成") 