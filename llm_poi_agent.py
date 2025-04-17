def llm_poi_agent(recommendation_text, client, conn=None):
    """
    基于LLM旅游推荐，提取景点并生成详细POI信息，然后更新数据库
    
    Args:
        recommendation_text: LLM生成的旅游推荐文本
        client: LLM客户端实例
        conn: 可选的数据库连接（如果未提供会创建新连接）
        
    Returns:
        更新的POI数量
    """
    import re
    import json
    import sqlite3
    import random
    
    # 如果未提供连接，创建新连接
    if conn is None:
        conn = sqlite3.connect('travel_db.sqlite')
        conn.row_factory = sqlite3.Row
    
    print("正在分析旅游推荐内容...")
    
    # 首先提取明确的推荐POI
    poi_pattern = r'\d+\.\s+\*\*([^*]+)\*\*\s+([^\n]+)'
    extracted_pois = re.findall(poi_pattern, recommendation_text)
    
    if not extracted_pois:
        print("未能从推荐文本中提取景点信息")
        return 0
    
    print(f"从推荐文本中提取了{len(extracted_pois)}个景点")
    
    # 收集推荐POI的名称
    extracted_poi_names = [poi[0] for poi in extracted_pois]
    
    # 2. 构建系统提示 - 根据实际数据库结构进行调整
    system_prompt = """
    你是一个旅游数据专家。请为给定的推荐景点生成详细的POI信息，格式必须严格遵循要求。
    
    为每个景点生成以下信息：
    1. name: 景点名称（保持原名）
    2. category: 具体类别（如：景点、古迹、寺庙、博物馆、茶馆等）
    3. category_type: 大类别（必须从以下选择一个：自然景观、历史古迹、文化场所、购物区域、美食街区）
    4. description: 详细描述（100-200字）
    5. latitude: 纬度（精确到小数点后4位）
    6. longitude: 经度（精确到小数点后4位）
    7. rating: 评分（1.0-5.0之间的小数）
    8. ticket_price: 门票价格（人民币元，免费为0）
    9. visit_time: 推荐游览时间（分钟）
    10. cultural_tags: 相关文化标签数组（至少3个标签）
    
    返回必须是完整规范的JSON，格式如下：
    {
      "pois": [
        {
          "name": "西湖",
          "category": "景点",
          "category_type": "自然景观",
          "description": "...",
          "latitude": 30.2590,
          "longitude": 120.1490,
          "rating": 4.8,
          "ticket_price": 0,
          "visit_time": 180,
          "cultural_tags": ["自然风光", "文化遗产", "历史名胜"]
        },
        ...
      ]
    }
    
    确保所有坐标准确，名称和描述真实合理，门票价格和游览时间符合实际情况。
    """
    
    # 3. 构建用户提示 - 使用更安全的字符串构建方式
    poi_names = ', '.join([poi[0] for poi in extracted_pois])
    
    # 创建景点描述的文本，避免使用嵌套的f-string
    poi_descriptions = []
    for i, poi in enumerate(extracted_pois):
        poi_descriptions.append(f"{i+1}. {poi[0]}: {poi[1]}")
    poi_descriptions_text = '\n'.join(poi_descriptions)
    
    user_prompt = f"""
    请为以下推荐景点生成详细的POI信息：
    
    {poi_names}
    
    各景点简要描述：
    {poi_descriptions_text}
    
    请确保返回完整的JSON数据，包含所有必需字段，格式严格按要求。每个景点都要包含完整信息。
    """
    
    # 4. 调用LLM生成POI详细信息
    try:
        print("调用LLM生成POI详细信息...")
        response = client.chat.completions.create(
            model="deepseek-r1-distill-qwen-32b-250120",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=False
        )
        
        content = response.choices[0].message.content
        print(f"收到LLM响应，长度: {len(content)}")
        
        # 5. 解析JSON
        try:
            # 尝试直接解析JSON
            try:
                result = json.loads(content)
            except:
                # 尝试提取JSON部分
                json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
                match = re.search(json_pattern, content)
                if match:
                    json_str = match.group(1)
                    result = json.loads(json_str)
                else:
                    # 最后一次尝试 - 寻找大括号
                    json_pattern = r'({[\s\S]*})'
                    match = re.search(json_pattern, content)
                    if match:
                        json_str = match.group(1)
                        result = json.loads(json_str)
                    else:
                        raise ValueError("无法从响应中提取JSON")
            
            # 确保结果包含pois字段
            if "pois" not in result:
                raise ValueError("响应中缺少pois字段")
                
            extracted_pois = result["pois"]
            print(f"成功解析JSON，包含{len(extracted_pois)}个POI")
            
            # 生成额外POI
            # 创建新的系统提示，生成与现有POI相关但不重复的额外景点
            additional_system_prompt = """
            你是一个旅游数据专家。请为用户生成额外的POI信息，这些景点应该与已有的推荐景点相关联，但不重复已有景点。
            格式必须严格遵循要求。
            
            为每个景点生成以下信息：
            1. name: 景点名称（必须是真实存在的景点，不要与已有景点重复）
            2. category: 具体类别（如：景点、古迹、寺庙、博物馆、茶馆等）
            3. category_type: 大类别（必须从以下选择一个：自然景观、历史古迹、文化场所、购物区域、美食街区）
            4. description: 详细描述（100-200字）
            5. latitude: 纬度（精确到小数点后4位）
            6. longitude: 经度（精确到小数点后4位）
            7. rating: 评分（1.0-5.0之间的小数）
            8. ticket_price: 门票价格（人民币元，免费为0）
            9. visit_time: 推荐游览时间（分钟）
            10. cultural_tags: 相关文化标签数组（至少3个标签）
            
            返回必须是完整规范的JSON，格式如下：
            {
              "pois": [
                {
                  "name": "景点名称",
                  "category": "具体类别",
                  "category_type": "大类别",
                  "description": "详细描述",
                  "latitude": 纬度,
                  "longitude": 经度,
                  "rating": 评分,
                  "ticket_price": 门票价格,
                  "visit_time": 游览时间,
                  "cultural_tags": ["标签1", "标签2", "标签3"]
                },
                ...
              ]
            }
            
            确保所有信息准确真实，特别是景点名称、位置坐标、类别和描述。
            """
            
            additional_user_prompt = f"""
            已有的推荐景点包括：
            {', '.join([poi['name'] for poi in extracted_pois])}
            
            请根据这些已有景点，推荐与它们相关的额外景点，数量大约是已有景点的两倍（约{len(extracted_pois)*2}个）。
            
            这些新景点应该：
            1. 与已有景点相关联或类似（如在相同或邻近地区、相似主题、历史文化联系等）
            2. 不重复已有景点
            3. 是真实存在的景点
            4. 按照要求的JSON格式输出
            
            请确保返回的JSON数据完整有效，并且不要包含已有的景点。
            """
            
            # 调用LLM生成额外POI
            print(f"调用LLM生成额外POI信息（目标数量：{len(extracted_pois)*2}个）...")
            additional_response = client.chat.completions.create(
                model="deepseek-r1-distill-qwen-32b-250120",
                messages=[
                    {"role": "system", "content": additional_system_prompt},
                    {"role": "user", "content": additional_user_prompt}
                ],
                stream=False
            )
            
            additional_content = additional_response.choices[0].message.content
            print(f"收到额外POI响应，长度: {len(additional_content)}")
            
            # 解析额外POI的JSON
            try:
                # 尝试直接解析JSON
                try:
                    additional_result = json.loads(additional_content)
                except:
                    # 尝试提取JSON部分
                    json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
                    match = re.search(json_pattern, additional_content)
                    if match:
                        json_str = match.group(1)
                        additional_result = json.loads(json_str)
                    else:
                        # 最后一次尝试 - 寻找大括号
                        json_pattern = r'({[\s\S]*})'
                        match = re.search(json_pattern, additional_content)
                        if match:
                            json_str = match.group(1)
                            additional_result = json.loads(json_str)
                        else:
                            raise ValueError("无法从额外POI响应中提取JSON")
                
                # 确保结果包含pois字段
                if "pois" not in additional_result:
                    raise ValueError("额外POI响应中缺少pois字段")
                
                additional_pois = additional_result["pois"]
                print(f"成功解析额外POI JSON，包含{len(additional_pois)}个额外POI")
                
                # 过滤掉重复的POI
                existing_names = {poi["name"] for poi in extracted_pois}
                filtered_additional_pois = [
                    poi for poi in additional_pois 
                    if poi["name"] not in existing_names
                ]
                
                print(f"过滤后剩余{len(filtered_additional_pois)}个额外POI")
                
                # 合并原始POI和额外POI
                all_pois = extracted_pois + filtered_additional_pois
                print(f"总共有{len(all_pois)}个POI将被添加到数据库")
                
                # 记录原始推荐的POI名称，用于后续高亮显示
                original_poi_names = {poi["name"] for poi in extracted_pois}
                
            except Exception as e:
                print(f"处理额外POI时出错: {str(e)}，将只使用原始POI")
                all_pois = extracted_pois
                original_poi_names = {poi["name"] for poi in extracted_pois}
            
            # 6. 更新数据库
            cursor = conn.cursor()
            
            # 清空现有表 - 安全做法
            print("正在清空现有表...")
            try:
                cursor.execute("DELETE FROM comments")
                cursor.execute("DELETE FROM cultural_tags")
                cursor.execute("DELETE FROM pois")
            except Exception as e:
                print(f"清空表时出错: {str(e)}，尝试继续...")
            
            # 插入新POI数据
            print(f"开始插入{len(all_pois)}个POI...")
            poi_id = 1
            cultural_tag_id = 1
            
            for poi in all_pois:
                # 检查是否是原始推荐中的POI（用于后续高亮）
                is_highlighted = poi["name"] in original_poi_names
                
                # 插入POI记录，不包含highlighted字段
                cursor.execute("""
                INSERT INTO pois (
                    id, name, category, category_type, description, 
                    latitude, longitude, rating, ticket_price, visit_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    poi_id,
                    poi["name"],
                    poi["category"],
                    poi["category_type"],
                    poi["description"],
                    poi["latitude"],
                    poi["longitude"],
                    poi["rating"],
                    poi["ticket_price"],
                    poi["visit_time"]
                ))
                
                # 插入文化标签 - 去掉category字段
                for tag in poi.get("cultural_tags", []):
                    cursor.execute("""
                    INSERT INTO cultural_tags (id, poi_id, tag, weight)
                    VALUES (?, ?, ?, ?)
                    """, (
                        cultural_tag_id,
                        poi_id,
                        tag,
                        random.uniform(1.0, 1.8)
                    ))
                    cultural_tag_id += 1
                
                # 生成默认评论
                sentiment = random.uniform(0.6, 0.95)
                cursor.execute("""
                INSERT INTO comments (poi_id, content, keywords, sentiment)
                VALUES (?, ?, ?, ?)
                """, (
                    poi_id,
                    f"{poi['name']}是一个很棒的地方！{poi['description'][:50]}...",
                    ','.join(poi.get("cultural_tags", [])[:3]),
                    sentiment
                ))
                
                poi_id += 1
            
            # 提交事务
            conn.commit()
            print(f"成功更新数据库，插入了{len(all_pois)}个POI")
            return len(all_pois)
            
        except Exception as e:
            print(f"处理LLM响应或更新数据库时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            return 0
            
    except Exception as e:
        print(f"调用LLM生成POI信息时出错: {str(e)}")
        return 0
    finally:
        # 如果我们创建了连接，则关闭它
        if conn is not None and not conn.in_transaction:
            conn.close() 