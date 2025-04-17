from flask import Flask, render_template, request, jsonify, Response, send_from_directory
import os
import time
import random
import math
import json
import pandas as pd
import requests
import folium
from collections import Counter
import jieba
import jieba.analyse
import sqlite3
#import chardet

# 尝试导入Ark SDK，如果不可用则创建一个模拟版本
try:
    from volcenginesdkarkruntime import Ark
    # 初始化Ark客户端
    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key="0c2d99af-ab7d-4925-8b3d-6d645015c443",
    )
    print("成功初始化Ark SDK客户端，将使用真实LLM进行回答")
except ImportError:
    print("无法导入Ark SDK，将使用模拟版本进行回答")
    
    # 创建一个模拟的Ark客户端
    class MockMessage:
        def __init__(self, content=None, reasoning_content=None):
            self.content = content
            self.reasoning_content = reasoning_content
    
    class MockDelta:
        def __init__(self, content=None, reasoning_content=None):
            self.content = content
            self.reasoning_content = reasoning_content
    
    class MockChoice:
        def __init__(self, content=None, reasoning_content=None):
            self.message = MockMessage(content, reasoning_content)
            self.delta = MockDelta()
    
    class MockResponse:
        def __init__(self, choices):
            self.choices = choices
            
        def __iter__(self):
            for chunk in self.chunks:
                yield chunk
    
    class MockArk:
        def __init__(self, **kwargs):
            self.base_url = kwargs.get("base_url", "")
            self.api_key = kwargs.get("api_key", "")
            print(f"模拟Ark客户端初始化完成: {self.base_url}")
        
        class chat:
            @staticmethod
            def completions():
                return None
                
            @classmethod
            def create(cls, model, messages, stream=False):
                print(f"模拟调用LLM API: {model}, 流式响应: {stream}")
                
                # 提取用户输入
                user_message = ""
                for msg in messages:
                    if msg.get("role") == "user":
                        user_message = msg.get("content", "")
                        break
                
                print(f"处理用户问题: '{user_message}'")
                
                # 提取关键词作为旅行主题
                keywords = []
                if "西湖" in user_message:
                    keywords.append("西湖")
                if "灵隐寺" in user_message:
                    keywords.append("灵隐寺")
                if "佛教" in user_message:
                    keywords.append("佛教")
                if "茶" in user_message:
                    keywords.append("茶文化")
                if "历史" in user_message:
                    keywords.append("历史")
                if "美食" in user_message:
                    keywords.append("美食")
                
                # 创建一个思考过程
                reasoning = f"""
                分析用户问题: "{user_message}"
                
                1. 提取关键信息:
                   - 用户可能关注的景点: {', '.join(keywords) if keywords else '未明确指定'}
                   - 旅行主题: {'、'.join(keywords) if keywords else '一般文化体验'}
                   
                2. 旅行建议思路:
                   - 根据用户兴趣推荐相关景点
                   - 提供合理的行程安排
                   - 考虑交通和游览时间
                   
                3. 回答框架:
                   - 针对用户兴趣提供定制回答
                   - 推荐1-2天的游览路线
                   - 提供实用的旅行建议
                """
                
                # 根据不同关键词生成不同回答
                if "灵隐寺" in user_message:
                    answer = """## 推荐1天佛教文化路线

### 第1天路线

1. **灵隐寺**
   杭州著名的佛教寺庙，位于西湖西北面，始建于东晋咸和年间，香火鼎盛，是中国重要的佛教禅宗道场。

2. **飞来峰石窟**
   位于灵隐寺旁，有奇特怪石和众多佛教造像，是江南地区规模最大的石窟群，最早开凿于五代时期。

3. **永福寺**
   位于法云安缦酒店对面，清幽雅静，游客较少，可在此感受佛教文化的宁静与庄严。

4. **龙井村茶室**
   参观寺庙后，可前往附近的龙井村，品尝正宗龙井茶，体验茶禅一味的文化内涵。

5. **法喜寺**
   也称"小灵隐"，环境清幽，游客稀少，可在此静心冥想，感受禅意。

### 旅行建议

- 最佳游览时间：8:30-16:00，上午人较少
- 交通方式：可乘坐公交K807路、Y9路到灵隐站下车
- 建议携带：舒适的鞋子、相机、香火钱
- 天气提醒：如遇雨天，可在寺内品茶、抄经，感受内心平静

灵隐寺门票45元，飞来峰景区门票35元，通常需要同时购买两个景点门票。寺内禁止吸烟，请着装得体。参观时请保持安静，尊重宗教场所。"""
                elif "西湖" in user_message:
                    answer = """## 推荐1天西湖景区路线

### 第1天路线

1. **断桥残雪**
   西湖十景之一，白蛇传传说地，可欣赏西湖全景，是游览西湖的经典起点。

2. **白堤**
   连接断桥与平湖秋月，堤上杨柳依依，两侧景色优美，步行约20分钟。

3. **平湖秋月**
   西湖十景之一，可在湖畔欣赏西湖美景，有多处亭台楼阁点缀其中。

4. **岳王庙**
   纪念南宋抗金名将岳飞的场所，感受中华民族气节，了解历史文化。

5. **雷峰塔**
   新建的仿古塔，与三潭印月、宝石山隔湖相望，可登塔俯瞰西湖全景。

6. **苏堤春晓**
   西湖十景之一，贯穿西湖南北，两侧垂柳成荫，是徒步或骑行的绝佳选择。

### 旅行建议

- 最佳游览时间：8:00-17:00，清晨或黄昏景色最佳
- 交通方式：步行、游船或租赁自行车环湖游览
- 建议携带：舒适的鞋子、相机、遮阳伞
- 天气提醒：晴天视野开阔，是拍摄西湖全景的好时机

西湖景区大部分景点免费，只有雷峰塔(40元)、岳王庙(25元)等少数景点收费。推荐在湖边小店品尝西湖醋鱼、龙井虾仁等杭州特色美食。步行全程约需6-8小时，可根据体力选择公交或游船衔接部分路段。"""
                else:
                    answer = """## 推荐1天杭州文化体验路线

### 第1天路线

1. **西湖景区**
   杭州标志性景点，包含断桥残雪、平湖秋月、苏堤春晓等十景，环境优美，充满诗情画意。

2. **灵隐寺**
   著名佛教寺庙，始建于东晋，可搭配飞来峰石窟一起游览，感受佛教文化的庄严与宁静。

3. **龙井村**
   中国著名的茶文化发源地之一，可品尝正宗龙井茶，了解传统制茶工艺。

4. **河坊街/南宋御街**
   古色古香的传统商业街区，可品尝杭州特色小吃，购买丝绸等特色商品。

5. **西溪湿地**
   城市中的"绿肺"，有"宋代雅致"的水乡风光，适合傍晚时分游览，欣赏日落美景。

### 旅行建议

- 最佳游览时间：8:00-17:00
- 交通方式：公交、地铁、步行或打车
- 建议携带：舒适的鞋子、相机、遮阳伞
- 天气提醒：天气适宜，按计划游览即可，景色会很棒！

杭州公共交通便利，景点间距离适中。西湖景区大部分景点免费，只有雷峰塔、岳王庙等少数景点收费。"""
                
                if not stream:
                    # 非流式响应，直接返回结果
                    if any(msg.get("role") == "system" and "JSON格式返回" in msg.get("content", "") for msg in messages):
                        # 如果是提取旅行偏好的系统提示
                        content = '{"theme": "文化体验", "days": 1, "energy": "中等"}'
                        if "西湖" in user_message:
                            content = '{"theme": "西湖景区", "days": 1, "energy": "中等"}'
                        elif "灵隐寺" in user_message or "佛教" in user_message:
                            content = '{"theme": "佛教文化", "days": 1, "energy": "中等"}'
                        elif "茶" in user_message:
                            content = '{"theme": "茶文化", "days": 1, "energy": "低"}'
                        elif "历史" in user_message:
                            content = '{"theme": "历史文化", "days": 2, "energy": "中等"}'
                    else:
                        content = answer
                    
                    return MockResponse([MockChoice(content=content)])
                else:
                    # 流式响应，返回迭代器
                    print("创建模拟流式响应")
                    response = MockResponse([])
                    response.chunks = []
                    
                    # 创建模拟的推理流式响应块
                    for line in reasoning.strip().split('\n'):
                        if line.strip():
                            chunk = MockResponse([])
                            choice = MockChoice()
                            choice.delta = MockDelta(reasoning_content=line + "\n")
                            chunk.choices = [choice]
                            response.chunks.append(chunk)
                            
                    # 添加分隔标记
                    separator_chunk = MockResponse([])
                    separator_choice = MockChoice()
                    separator_choice.delta = MockDelta() # 空的delta，只是用作标记
                    separator_chunk.choices = [separator_choice]
                    response.chunks.append(separator_chunk)
                    
                    # 创建内容响应块
                    for line in answer.split('\n'):
                        # 添加一个整行
                        chunk = MockResponse([])
                        choice = MockChoice()
                        choice.delta = MockDelta(content=line + "\n")
                        chunk.choices = [choice]
                        response.chunks.append(chunk)
                    
                    print(f"创建了{len(response.chunks)}个模拟响应块")
                    return response
    
    # 使用模拟客户端
    client = MockArk(
        base_url="https://mock-api.example.com",
        api_key="mock-api-key"
    )

# 尝试导入天气模块
try:
    from weather import get_comprehensive_weather
except ImportError:
    # 如果导入失败，创建一个简单的模拟函数
    def get_comprehensive_weather(api_key, location, days=3):
        print(f"模拟获取天气数据: {location}, {days}天")
        return {
            "location": {"name": location, "region": "浙江", "country": "中国"},
            "current": {
                "temp_c": 25, "feelslike_c": 26, "condition": {"text": "晴", "code": 1000},
                "humidity": 65, "wind_kph": 7, "is_day": 1
            },
            "forecast": {
                "forecastday": [
                    {
                        "date": "2023-07-01",
                        "day": {
                            "maxtemp_c": 28, "mintemp_c": 22,
                            "condition": {"text": "多云", "code": 1003},
                            "daily_chance_of_rain": 20
                        }
                    },
                    {
                        "date": "2023-07-02",
                        "day": {
                            "maxtemp_c": 29, "mintemp_c": 23,
                            "condition": {"text": "晴", "code": 1000},
                            "daily_chance_of_rain": 10
                        }
                    },
                    {
                        "date": "2023-07-03",
                        "day": {
                            "maxtemp_c": 30, "mintemp_c": 24,
                            "condition": {"text": "晴", "code": 1000},
                            "daily_chance_of_rain": 5
                        }
                    }
                ]
            }
        }

# WeatherAPI.com的API密钥
WEATHER_API_KEY = 'fa2a12d01c2245c8a9880339251004' # 使用weather.py中的API密钥

# 初始化Flask应用
app = Flask(__name__)

# 创建SQLite数据库连接
def get_db_connection():
    conn = sqlite3.connect('travel_db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

# 初始化数据库
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建POI表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pois (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        description TEXT,
        category TEXT,
        rating REAL,
        ticket_price REAL,
        visit_time INTEGER,
        category_type TEXT
    )
    ''')
    
    # 创建文化标签表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cultural_tags (
        id INTEGER PRIMARY KEY,
        poi_id INTEGER,
        tag TEXT NOT NULL,
        weight REAL DEFAULT 1.0,
        FOREIGN KEY (poi_id) REFERENCES pois (id)
    )
    ''')
    
    # 创建用户评论表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY,
        poi_id INTEGER,
        content TEXT NOT NULL,
        keywords TEXT,
        sentiment REAL,
        FOREIGN KEY (poi_id) REFERENCES pois (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# 添加示例POI数据
def add_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM pois")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # 插入西湖景点数据
        pois = [
            (1, "西湖断桥", 30.2587, 120.1486, "断桥是《白蛇传》故事发生地，也是西湖十景之一", "景点", 4.7, 0, 60, "景点"),
            (2, "雷峰塔", 30.2317, 120.1485, "雷峰塔与白蛇传传说密切相关，是南宋时期建造", "古迹", 4.5, 40, 90, "古迹"),
            (3, "龙井村", 30.2193, 120.1056, "西湖龙井茶原产地，有十八棵御茶树等景点", "文化体验", 4.6, 0, 120, "文化体验"),
            (4, "岳庙", 30.2542, 120.1327, "纪念南宋抗金名将岳飞的祠庙", "历史古迹", 4.4, 25, 60, "历史古迹"),
            (5, "南宋官窑遗址", 30.1923, 120.1309, "南宋时期皇家御用瓷器的烧制地", "历史遗址", 4.3, 30, 120, "历史遗址"),
            (6, "孤山", 30.2546, 120.1428, "西湖中最大的自然岛，有西泠印社等景点", "自然景观", 4.5, 0, 90, "自然景观"),
            (7, "中国茶叶博物馆", 30.2278, 120.1364, "展示中国茶文化历史的专业博物馆", "博物馆", 4.7, 0, 150, "博物馆"),
            (8, "青藤茶馆", 30.2585, 120.1481, "西湖边有名的传统茶馆，环境优美", "茶馆", 4.6, 60, 120, "茶馆"),
            (9, "胡雪岩故居", 30.2497, 120.1775, "清末著名徽商胡雪岩的豪宅，展示徽派建筑", "历史建筑", 4.4, 25, 90, "历史建筑"),
            (10, "灵隐寺", 30.2441, 120.1226, "历史悠久的佛教寺庙，周围自然环境优美", "寺庙", 4.8, 45, 180, "寺庙")
        ]
        
        cursor.executemany(
            "INSERT INTO pois (id, name, latitude, longitude, description, category, rating, ticket_price, visit_time, category_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            pois
        )
        
        # 插入文化标签数据
        cultural_tags = [
            (1, 1, "白蛇传", 1.5, "景点"),
            (2, 1, "爱情传说", 1.2, "景点"),
            (3, 1, "拍照胜地", 1.0, "景点"),
            (4, 2, "白蛇传", 1.5, "古迹"),
            (5, 2, "南宋建筑", 1.3, "古迹"),
            (6, 2, "佛教文化", 1.1, "寺庙"),
            (7, 3, "茶文化", 1.8, "文化体验"),
            (8, 3, "龙井茶", 1.6, "文化体验"),
            (9, 3, "乾隆下江南", 1.4, "文化体验"),
            (10, 4, "南宋历史", 1.7, "历史古迹"),
            (11, 4, "岳飞精忠报国", 1.5, "历史古迹"),
            (12, 4, "爱国主义", 1.3, "历史古迹"),
            (13, 5, "南宋历史", 1.6, "历史遗址"),
            (14, 5, "古陶瓷", 1.4, "历史遗址"),
            (15, 5, "非遗技艺", 1.2, "文化体验"),
            (16, 6, "西泠印社", 1.5, "景点"),
            (17, 6, "文人雅士", 1.3, "景点"),
            (18, 6, "自然景观", 1.0, "自然景观"),
            (19, 7, "茶文化", 1.7, "文化体验"),
            (20, 7, "历史文物", 1.5, "博物馆"),
            (21, 8, "茶文化", 1.6, "茶馆"),
            (22, 8, "休闲体验", 1.2, "茶馆"),
            (23, 9, "徽商文化", 1.5, "文化体验"),
            (24, 9, "徽派建筑", 1.4, "历史建筑"),
            (25, 10, "佛教文化", 1.7, "寺庙"),
            (26, 10, "自然景观", 1.3, "自然景观")
        ]
        
        cursor.executemany(
            "INSERT INTO cultural_tags (id, poi_id, tag, weight, category) VALUES (?, ?, ?, ?, ?)",
            cultural_tags
        )
        
        # 插入用户评论数据
        comments = [
            (1, 1, "断桥人太多！推荐早起6点去，晨雾中的断桥像水墨画。桥东侧200米有家藕粉店超好吃！", "早起,晨雾,人多,美食", 0.7, "景点"),
            (2, 1, "《白蛇传》故事发生地，可以听讲解了解许仙白娘子的故事，冬天来看雪景最美。", "白蛇传,故事,雪景", 0.9, "景点"),
            (3, 2, "雷峰塔落日绝美！建议下午5点去，塔顶能看到西湖全景。旁边有个小众拍照点，塔西侧500米的小亭子人少！", "落日,拍照,全景,人少", 0.8, "景点"),
            (4, 3, "龙井村采茶体验超棒！茶农会教炒茶，记得去'十八棵御茶树'打卡，乾隆钦点的贡茶园！", "采茶,炒茶,御茶树,乾隆", 0.9, "文化体验"),
            (5, 4, "岳飞墓值得一看，'精忠报国'四个大字震撼人心，记得读一读碑文了解岳飞的故事。", "精忠报国,历史,故事", 0.8, "历史古迹"),
            (6, 5, "南宋官窑遗址门票30元，可以亲手做陶器！关联龙井茶文化，古代茶具都是这里烧制的～", "陶器,体验,茶具,历史", 0.7, "历史遗址"),
            (7, 6, "孤山梅花开了！推荐骑行路线：断桥→白堤→孤山，沿途有清代行宫遗址，人少景美！", "梅花,骑行,历史遗迹", 0.9, "景点"),
            (8, 7, "免费博物馆！展示了唐宋茶具，还能体验宋代点茶。馆后茶园适合拍古风照～", "免费,茶具,体验,拍照", 0.8, "博物馆"),
            (9, 8, "雨天必去青藤茶馆！人均60元，窗外是西湖雨景，配龙井茶和茶点，氛围感拉满～", "雨天,龙井茶,氛围,景观", 0.9, "茶馆"),
            (10, 9, "胡雪岩故居展示了清末徽商的辉煌，建筑非常精美，推荐请讲解了解背后的商业传奇。", "徽商,建筑,历史,故事", 0.8, "历史建筑"),
            (11, 10, "灵隐寺香火旺盛，建议避开节假日。寺前的飞来峰石窟值得细看，有宋代以来的石刻。", "佛教,石窟,避开节假日", 0.7, "寺庙")
        ]
        
        cursor.executemany(
            "INSERT INTO comments (id, poi_id, content, keywords, sentiment, category) VALUES (?, ?, ?, ?, ?, ?)",
            comments
        )
        
        conn.commit()
    
    conn.close()

# 初始化数据库和加载数据
init_db()
add_sample_data()

# 自动对POI进行分类
def auto_classify_pois():
    print("开始自动对POI进行分类...")
    try:
        # 获取所有POI数据
        conn = get_db_connection()
        pois = conn.execute('SELECT id, name, description, category, category_type FROM pois').fetchall()
        pois = [dict(poi) for poi in pois]
        
        # poi.py中定义的分类列表
        valid_categories = [
            "自然景观", "历史古迹", "文化场所", "购物区域", "美食街区"
        ]
        
        # 类别颜色映射（与poi.py中保持一致）
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
        
        # 检查哪些POI需要重新分类
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
                
            except Exception as e:
                print(f"分类 '{poi['name']}' 时出错: {str(e)}")
                continue
        
        # 提交所有更改
        conn.commit()
        conn.close()
        
        print(f"成功为 {classified_count} 个POI分类，之前已有 {len(already_classified)} 个POI分类完成")
        
    except Exception as e:
        print(f"POI自动分类过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()

# 在应用启动时自动运行分类
auto_classify_pois()

# ====================== 路由定义 ======================

# 主页路由
@app.route('/')
def index():
    return render_template('index_integrated.html')

# 新增统一界面路由
@app.route('/unified')
def unified_interface():
    return render_template('unified.html')


# 空间RAG部分的路由
@app.route('/rag')
def rag_page():
    return render_template('rag.html')

# 知识图谱部分的路由
@app.route('/knowledge_graph')
def knowledge_graph():
    return render_template('knowledge_graph.html')

# 图表可视化路由 - 使用graph文件夹中的实现
@app.route('/graph')
def graph_visualization():
    return render_template('graph/templates/index.html')
    
# 聊天部分的路由
@app.route('/chat')
def chat_page():
    return render_template('chat.html')

# ====================== POI数据API ======================

# 获取所有POI数据
@app.route('/api/pois')
def get_pois():
    conn = get_db_connection()
    pois = conn.execute('SELECT * FROM pois').fetchall()
    conn.close()
    
    return jsonify([dict(poi) for poi in pois])


# 空间感知RAG实现类
class SpatialAwareRAG:
    def __init__(self, theme, days, energy):
        self.theme = theme
        self.days = days
        self.energy = energy
        self.execution_log = []
        self.execution_times = {}
        self.pois = []
        self.cultural_tags = []
        self.comments = []
        self.selected_pois = []
        
    def log_step_start(self, step_name):
        self.execution_log.append(f"开始: {step_name}")
        return time.time()
        
    def log_step_end(self, step_name, start_time):
        end_time = time.time()
        execution_time = end_time - start_time
        self.execution_times[step_name] = execution_time
        self.execution_log.append(f"完成: {step_name}, 耗时: {execution_time:.3f}秒")
        return execution_time
    
    # 步骤1: 用户输入与空间感知
    def process_user_input(self):
        start_time = self.log_step_start("用户输入与空间感知")
        
        # 处理用户输入，转换为系统可理解的查询参数
        query_params = {
            'theme': self.theme,
            'days': self.days,
            'energy_level': self.energy
        }
        
        # 设置每天游览时间
        if self.energy == '高':
            self.max_time_per_day = 10 * 60  # 10小时（分钟）
        elif self.energy == '低':
            self.max_time_per_day = 6 * 60   # 6小时（分钟）
        else:
            self.max_time_per_day = 8 * 60   # 8小时（分钟）
            
        self.max_total_time = self.days * self.max_time_per_day
        
        # 模拟空间约束处理
        time.sleep(0.2)  # 模拟处理时间
        
        self.log_step_end("用户输入与空间感知", start_time)
        return query_params
    
    # 步骤2: 空间数据检索
    def retrieve_spatial_data(self):
        start_time = self.log_step_start("空间数据检索")
        
        # 从数据库检索POI点
        conn = get_db_connection()
        cursor = conn.execute('''
            SELECT * FROM pois
        ''')
        self.pois = [dict(poi) for poi in cursor.fetchall()]
        conn.close()
        
        # 模拟空间索引和检索过程
        time.sleep(0.3)  # 模拟处理时间
        
        # 记录结果
        retrieved_poi_count = len(self.pois)
        
        self.log_step_end("空间数据检索", start_time)
        return retrieved_poi_count
    
    # 步骤3: 文化语义检索
    def retrieve_cultural_semantic(self):
        start_time = self.log_step_start("文化语义检索")
        
        # 从数据库获取文化标签
        conn = get_db_connection()
        cursor = conn.execute('''
            SELECT t.*, p.name as poi_name
            FROM cultural_tags t
            JOIN pois p ON t.poi_id = p.id
            WHERE t.tag LIKE ?
        ''', (f'%{self.theme}%',))
        self.cultural_tags = [dict(tag) for tag in cursor.fetchall()]
        
        # 获取评论
        cursor = conn.execute('''
            SELECT c.*, p.name as poi_name
            FROM comments c
            JOIN pois p ON c.poi_id = p.id
        ''')
        self.comments = [dict(comment) for comment in cursor.fetchall()]
        conn.close()
        
        # 提取文化语义特征
        cultural_features = {}
        
        # 基于标签的特征提取
        for tag in self.cultural_tags:
            poi_id = tag['poi_id']
            if poi_id not in cultural_features:
                cultural_features[poi_id] = {
                    'tag_count': 0,
                    'total_weight': 0,
                    'tags': []
                }
            cultural_features[poi_id]['tag_count'] += 1
            cultural_features[poi_id]['total_weight'] += tag['weight']
            cultural_features[poi_id]['tags'].append(tag['tag'])
        
        # 基于评论的特征提取
        for comment in self.comments:
            poi_id = comment['poi_id']
            if poi_id in cultural_features:
                if 'sentiment_avg' not in cultural_features[poi_id]:
                    cultural_features[poi_id]['sentiment_avg'] = 0
                    cultural_features[poi_id]['comment_count'] = 0
                
                cultural_features[poi_id]['sentiment_avg'] += comment['sentiment']
                cultural_features[poi_id]['comment_count'] += 1
        
        # 计算平均情感得分
        for poi_id in cultural_features:
            if 'comment_count' in cultural_features[poi_id] and cultural_features[poi_id]['comment_count'] > 0:
                cultural_features[poi_id]['sentiment_avg'] /= cultural_features[poi_id]['comment_count']
        
        self.cultural_features = cultural_features
        
        # 模拟语义处理
        time.sleep(0.4)  # 模拟处理时间
        
        tag_count = len(self.cultural_tags)
        comment_count = len(self.comments)
        
        self.log_step_end("文化语义检索", start_time)
        return tag_count, comment_count
    
    # 步骤4: 多模态融合排序
    def multimodal_fusion_ranking(self):
        start_time = self.log_step_start("多模态融合排序")
        
        # 为每个POI计算综合得分
        poi_scores = {}
        
        # 中心点设为第一个POI或默认位置
        center_lat = 30.2500  # 杭州西湖中心点约为 30.25, 120.15
        center_lon = 120.1500
        
        # 空间距离权重
        distance_weight = 0.3
        
        # 文化相关性权重
        cultural_weight = 0.4
        
        # 评分与价格权重
        rating_weight = 0.2
        price_weight = 0.1
        
        # 对每个POI计算综合得分
        for poi in self.pois:
            poi_id = poi['id']
            score = 0
            
            # 1. 计算空间距离分数（距离越近，分数越高）
            dist = self.haversine_distance(center_lat, center_lon, poi['latitude'], poi['longitude'])
            # 归一化距离为0-1之间的分数，距离越近分数越高
            max_dist = 10.0  # 假设最大考虑距离为10公里
            distance_score = 1 - min(dist / max_dist, 1)
            
            # 2. 文化相关性分数
            cultural_score = 0
            if poi_id in self.cultural_features:
                # 标签数量和权重贡献
                tag_weight = self.cultural_features[poi_id]['total_weight']
                # 标签与主题的相关性（假设已在文化标签查询时过滤）
                theme_relevance = 1.0 if any(self.theme in tag for tag in self.cultural_features[poi_id]['tags']) else 0.5
                # 情感得分贡献
                sentiment_score = self.cultural_features[poi_id].get('sentiment_avg', 0.5)
                
                cultural_score = (tag_weight * theme_relevance * sentiment_score) / 3.0
                # 归一化为0-1
                cultural_score = min(cultural_score, 1.0)
            
            # 3. 评分分数（已经是0-5之间，归一化为0-1）
            rating_score = poi['rating'] / 5.0
            
            # 4. 价格分数（门票越便宜分数越高）
            max_price = 100  # 假设最高门票为100元
            price_score = 1 - min(poi['ticket_price'] / max_price, 1)
            
            # 计算综合得分
            score = (
                distance_weight * distance_score +
                cultural_weight * cultural_score +
                rating_weight * rating_score +
                price_weight * price_score
            )
            
            poi_scores[poi_id] = {
                'poi': poi,
                'score': score,
                'components': {
                    'distance': distance_score,
                    'cultural': cultural_score,
                    'rating': rating_score,
                    'price': price_score
                }
            }
        
        # 按分数降序排序
        sorted_pois = sorted(
            poi_scores.values(), 
            key=lambda x: x['score'], 
            reverse=True
        )
        
        # 模拟处理时间
        time.sleep(0.2)
        
        # 贪心算法选择POI
        self.selected_pois = []
        total_time = 0
        
        for poi_data in sorted_pois:
            poi = poi_data['poi']
            visit_time = poi['visit_time']
            
            # 考虑交通时间（简化处理，假设每个景点间30分钟）
            if self.selected_pois:
                visit_time += 30
            
            if total_time + visit_time <= self.max_total_time:
                self.selected_pois.append(dict(poi))
                total_time += visit_time
        
        selected_count = len(self.selected_pois)
        
        self.log_step_end("多模态融合排序", start_time)
        return selected_count, sorted_pois[:3]
    
    # 步骤5: 大模型增强生成
    def llm_enhancement(self):
        start_time = self.log_step_start("大模型增强生成")
        
        # 为每个POI生成文化解说
        for poi in self.selected_pois:
            poi['cultural_description'] = generate_cultural_description(poi)
        
        # 记录解说生成的信息
        desc_lengths = [len(poi['cultural_description']) for poi in self.selected_pois]
        avg_length = sum(desc_lengths) / len(desc_lengths) if desc_lengths else 0
        total_tokens = sum(len(desc.split()) for desc in [poi['cultural_description'] for poi in self.selected_pois])
        
        # 模拟LLM处理时间
        time.sleep(0.5)
        
        self.log_step_end("大模型增强生成", start_time)
        return len(self.selected_pois), total_tokens
    
    # 步骤6: 路线规划与可视化
    def route_planning(self):
        start_time = self.log_step_start("路线规划与可视化")
        
        # 按天分组路线
        self.routes = []
        current_day = []
        current_day_time = 0
        
        for poi in self.selected_pois:
            visit_time = poi['visit_time']
            transport_time = 30 if current_day else 0
            
            if current_day_time + visit_time + transport_time <= self.max_time_per_day:
                current_day.append(poi)
                current_day_time += visit_time + transport_time
            else:
                self.routes.append(current_day)
                current_day = [poi]
                current_day_time = poi['visit_time']
        
        if current_day:
            self.routes.append(current_day)
        
        # 计算总游览时间
        total_visit_time = sum(poi['visit_time'] for poi in self.selected_pois)
        # 计算交通时间
        transport_time = 30 * (len(self.selected_pois) - len(self.routes))
        # 总时间
        total_time = total_visit_time + transport_time
        
        # 模拟路线规划处理
        time.sleep(0.3)
        
        self.log_step_end("路线规划与可视化", start_time)
        return len(self.routes), len(self.selected_pois), f"{total_time // 60}小时{total_time % 60}分钟"
    
    # 执行完整RAG流程
    def execute_full_rag_pipeline(self):
        # 记录开始时间
        pipeline_start = time.time()
        
        # 步骤1: 用户输入与空间感知
        query_params = self.process_user_input()
        
        # 步骤2: 空间数据检索
        retrieved_poi_count = self.retrieve_spatial_data()
        
        # 步骤3: 文化语义检索
        tag_count, comment_count = self.retrieve_cultural_semantic()
        
        # 步骤4: 多模态融合排序
        selected_count, top_pois = self.multimodal_fusion_ranking()
        
        # 步骤5: 大模型增强生成
        desc_count, total_tokens = self.llm_enhancement()
        
        # 步骤6: 路线规划与可视化
        days_count, poi_count, total_time = self.route_planning()
        
        # 计算总执行时间
        pipeline_end = time.time()
        total_execution_time = pipeline_end - pipeline_start
        
        # 构建执行结果摘要
        pipeline_summary = {
            "total_execution_time": total_execution_time,
            "step_times": self.execution_times,
            "steps_data": {
                "user_input": {
                    "theme": self.theme,
                    "days": self.days,
                    "energy": self.energy
                },
                "spatial_retrieval": {
                    "retrieved_pois": retrieved_poi_count
                },
                "cultural_semantic": {
                    "tag_count": tag_count,
                    "comment_count": comment_count
                },
                "multimodal_fusion": {
                    "selected_count": selected_count,
                    "top_pois": [p['poi']['name'] for p in top_pois]
                },
                "llm_enhancement": {
                    "description_count": desc_count,
                    "total_tokens": total_tokens
                },
                "route_planning": {
                    "days_count": days_count,
                    "poi_count": poi_count,
                    "total_time": total_time
                }
            },
            "routes": self.routes
        }
        
        return pipeline_summary

    # 计算两点之间的Haversine距离（公里）
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        # 将经纬度转换为弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine公式
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # 地球平均半径（公里）
        
        return c * r
# 获取RAG流程数据
@app.route('/api/rag_flow', methods=['POST'])
def get_rag_flow():
    data = request.json
    theme = data.get('theme', '茶文化')
    days = int(data.get('days', 1))
    energy = data.get('energy', '中等')
    
    # 创建空间感知RAG实例并执行
    rag = SpatialAwareRAG(theme, days, energy)
    result = rag.execute_full_rag_pipeline()
    
    # 构建前端友好的响应格式
    response = {
        "steps": [
            {
                "name": "用户输入与空间感知",
                "description": f"接收到用户主题：{theme}，{days}天，{energy}强度",
                "status": "completed",
                "time": f"{result['step_times'].get('用户输入与空间感知', 0):.1f}s",
                "data": result["steps_data"]["user_input"]
            },
            {
                "name": "空间数据检索",
                "description": f"从数据库检索相关POI点",
                "status": "completed",
                "time": f"{result['step_times'].get('空间数据检索', 0):.1f}s",
                "data": result["steps_data"]["spatial_retrieval"]
            },
            {
                "name": "文化语义检索",
                "description": "提取文化标签和用户评论",
                "status": "completed",
                "time": f"{result['step_times'].get('文化语义检索', 0):.1f}s",
                "data": result["steps_data"]["cultural_semantic"]
            },
            {
                "name": "多模态融合排序",
                "description": "融合地理和文化数据",
                "status": "completed",
                "time": f"{result['step_times'].get('多模态融合排序', 0):.1f}s",
                "data": result["steps_data"]["multimodal_fusion"]
            },
            {
                "name": "大模型增强生成",
                "description": "生成富有文化深度的讲解",
                "status": "completed",
                "time": f"{result['step_times'].get('大模型增强生成', 0):.1f}s",
                "data": result["steps_data"]["llm_enhancement"]
            },
            {
                "name": "路线规划与可视化",
                "description": "根据时间和体力约束规划路线",
                "status": "completed",
                "time": f"{result['step_times'].get('路线规划与可视化', 0):.1f}s",
                "data": result["steps_data"]["route_planning"]
            }
        ],
        "total_time": f"{result['total_execution_time']:.1f}s",
        "theme": theme,
        "routes": result["routes"]
    }
    
    return jsonify(response)

# 根据文化主题获取路线
@app.route('/api/routes', methods=['POST'])
def get_routes():
    data = request.json
    theme = data.get('theme', '茶文化')  # 默认茶文化主题
    days = data.get('days', 1)  # 默认1天行程
    energy = data.get('energy', '中等')  # 默认中等体力值
    
    # 创建空间感知RAG实例并执行
    rag = SpatialAwareRAG(theme, days, energy)
    result = rag.execute_full_rag_pipeline()
    
    # 返回路线结果
    return jsonify({
        'theme': theme,
        'days': days,
        'energy': energy,
        'routes': result['routes']
    })

# 生成地图可视化
@app.route('/api/map', methods=['POST'])
def generate_map():
    data = request.json
    routes = data.get('routes', [])
    
    try:
        # 创建地图，但不指定瓦片图层
        m = folium.Map(
            location=[30.2500, 120.1500], 
            zoom_start=13,
            tiles=None  # 禁用默认瓦片图层
        )
        
        # 添加高德地图瓦片图层（普通地图）
        amap_url = 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
        
        # 添加高德地图图层
        folium.TileLayer(
            tiles=amap_url,
            attr='&copy; <a href="https://www.amap.com/">高德地图</a>',
            name='高德地图',
            overlay=False,
            control=True
        ).add_to(m)

        # 可选：添加高德卫星图层
        amap_satellite_url = 'https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}'
        folium.TileLayer(
            tiles=amap_satellite_url,
            attr='&copy; <a href="https://www.amap.com/">高德卫星图</a>',
            name='高德卫星图',
            overlay=False,
            control=True
        ).add_to(m)
        
        # 添加图层控制器，允许用户切换图层
        folium.LayerControl().add_to(m)
        
        # 只有当routes不为空时才添加路线标记
        if routes and len(routes) > 0:
            colors = ['red', 'blue', 'green', 'purple', 'orange']
            
            for day_index, day_route in enumerate(routes):
                color = colors[day_index % len(colors)]
                
                # 添加景点标记
                for poi_index, poi in enumerate(day_route):
                    popup_content = f"<b>{poi['name']}</b><br>{poi.get('description', '')}"
                    if 'cultural_description' in poi:
                        popup_content += f"<br><br>{poi['cultural_description']}"
                    
                    tooltip_content = f"第{day_index+1}天 - 景点{poi_index+1}: {poi['name']}"
                    
                    folium.Marker(
                        [poi['latitude'], poi['longitude']],
                        popup=popup_content,
                        tooltip=tooltip_content,
                        icon=folium.Icon(color=color, icon='info-sign')
                    ).add_to(m)
                    
                    # 连接路线
                    if poi_index > 0:
                        prev_poi = day_route[poi_index-1]
                        folium.PolyLine(
                            [(prev_poi['latitude'], prev_poi['longitude']), 
                             (poi['latitude'], poi['longitude'])],
                            color=color,
                            weight=3,
                            opacity=0.7,
                            dash_array='5, 10'
                        ).add_to(m)
        
        # 确保static目录存在
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        
        # 保存地图到static目录
        map_file = 'route_map.html'
        map_path = os.path.join(static_dir, map_file)
        m.save(map_path)
        
        # 获取地图HTML内容以便直接返回
        map_html = m._repr_html_()
        
        # 返回相对于static的URL路径和HTML内容
        return jsonify({
            "map_url": f"/static/{map_file}",
            "map_html": map_html
        })
        
    except Exception as e:
        print(f"生成地图时出错: {str(e)}")
        return jsonify({"error": str(e), "map_url": ""})



# 用于生成文化解说的辅助函数
def generate_cultural_description(poi):
    # 预设文化解说
    preset_descriptions = {
        "西湖断桥": "断桥因《白蛇传》而闻名，是西湖爱情文化的象征。传说许仙与白娘子在此相遇，留下千古佳话。每到冬季，断桥积雪更是形成'断桥残雪'的绝美景观，为西湖十景之一。桥的东侧曾是城郊接壤处，商贸繁荣，至今周边仍有许多历史悠久的杭帮美食小店。",
        "雷峰塔": "雷峰塔建于北宋咸平三年(公元1000年)，是吴越国王钱俶为庆祝夫人黄氏得子而建。塔与《白蛇传》中白娘子被法海压在塔下的故事紧密相连，象征着对自由爱情的追求。现今的雷峰塔是2002年重建的，塔内收藏有大量佛教文物和出土文献，是了解南宋佛教文化和建筑艺术的重要场所。",
        "龙井村": "龙井村是西湖龙井茶的原产地，有'春风满面茶飘香'之美誉。村中最著名的是'十八棵御茶树'，相传为乾隆皇帝游览西湖时亲自册封的贡茶树。每年春季，这里举行传统茶文化活动，游客可以参与采茶、炒茶等体验，深入了解中国茶道文化的精髓，感受'一览众山小'的茶园风光。"
    }
    
    name = poi['name']
    description = poi['description']
    
    # 获取景点文化标签
    conn = get_db_connection()
    cursor = conn.execute('''
        SELECT tag FROM cultural_tags 
        WHERE poi_id = ?
    ''', (poi['id'],))
    tags = [row['tag'] for row in cursor.fetchall()]
    conn.close()
    
    # 如果有预设描述，则使用预设；否则生成一个通用描述
    return preset_descriptions.get(name, f"{name}是杭州著名的{poi['category']}景点，{description}。这里蕴含着丰富的{', '.join(tags)}等文化元素，是了解杭州历史文化的重要窗口。游览时可以深入体验当地特色，感受杭州的独特魅力。建议花费{poi['visit_time']}分钟细细品味这里的文化底蕴。")

# 分析评论关键词
@app.route('/api/analyze_comments')
def analyze_comments():
    # 手动指定5个热门杭州景点及其热度
    top_attractions = [
        ("西湖", 10),           # 最热门
        ("灵隐寺", 8),
        ("西湖断桥", 7),
        ("雷峰塔", 6),
        ("龙井村", 5)
    ]
    
    return jsonify({
        "keywords": [{"keyword": k, "count": c} for k, c in top_attractions]
    })

# ====================== 知识图谱API ======================

# 读取POI数据
def load_pois_for_graph():
    # 从数据库读取POI数据
    conn = get_db_connection()
    pois = conn.execute('SELECT *, category_type FROM pois').fetchall()
    pois = [dict(poi) for poi in pois]
    
    # 为每个POI添加额外属性
    for poi in pois:
        # 添加默认值
        poi["reviews"] = random.randint(100, 1000)
        poi["popularity"] = random.randint(60, 95)
        poi["address"] = f"浙江省杭州市西湖区{poi['name']}附近"
        poi["opening_hours"] = "全天开放" if poi["ticket_price"] == 0 else "08:30-17:30"
        poi["best_season"] = "四季皆宜"
        poi["historical_significance"] = f"{poi['name']}有着丰富的历史文化背景，是杭州著名的{poi['category']}。"
        poi["image"] = f"static/images/{poi['id']}.jpg"
        poi["year"] = 2010 + random.randint(0, 10)
    
    # 增加分类信息
    categories = [
        {"name": "自然景观", "color": "#2c7bb6", "icon": "tree"},
        {"name": "历史古迹", "color": "#d7191c", "icon": "landmark"},
        {"name": "文化场所", "color": "#fdae61", "icon": "museum"},
        {"name": "购物区域", "color": "#abd9e9", "icon": "store"},
        {"name": "美食街区", "color": "#66bd63", "icon": "utensils"},
        {"name": "景点", "color": "#2c7bb6", "icon": "tree"},
        {"name": "古迹", "color": "#d7191c", "icon": "landmark"},
        {"name": "文化体验", "color": "#fdae61", "icon": "museum"},
        {"name": "历史遗址", "color": "#66bd63", "icon": "archway"},
        {"name": "博物馆", "color": "#fdae61", "icon": "museum"},
        {"name": "茶馆", "color": "#fee08b", "icon": "coffee"},
        {"name": "历史建筑", "color": "#f46d43", "icon": "home"},
        {"name": "寺庙", "color": "#d73027", "icon": "place-of-worship"}
    ]
    
    conn.close()
    return pois, categories

# 使用DeepSeek LLM对POI实体进行分类
@app.route('/api/classify_pois', methods=['POST'])
def classify_pois():
    try:
        # 获取所有POI数据
        conn = get_db_connection()
        pois = conn.execute('SELECT id, name, description, category FROM pois').fetchall()
        pois = [dict(poi) for poi in pois]
        
        # 预定义的分类列表
        valid_categories = [
            "景点", "古迹", "文化体验", "历史古迹", "历史遗址", 
            "自然景观", "博物馆", "茶馆", "历史建筑", "寺庙"
        ]
        
        # 已分类和待分类的POIs
        already_classified = []
        to_be_classified = []
        
        # 检查哪些POI需要重新分类
        for poi in pois:
            if poi['category'] in valid_categories and poi['category'] != "景点":
                already_classified.append(poi)
            else:
                to_be_classified.append(poi)
        
        # 如果没有需要分类的POI，直接返回结果
        if not to_be_classified:
            return jsonify({
                "status": "success",
                "message": "所有POI已经有正确的分类",
                "classified_count": 0,
                "already_classified": len(already_classified)
            })
        
        # 构建系统提示
        system_prompt = f"""
        你是一个旅游数据分析专家。请根据POI的名称和描述，将其分类到以下预定义的类别之一：
        {', '.join(valid_categories)}
        
        每次只返回一个最合适的类别名称，不需要解释。请确保分类准确，考虑中国传统文化和旅游特点。
        """
        
        # 逐个调用LLM对每个POI进行分类
        classified_count = 0
        for poi in to_be_classified:
            # 构建用户提示
            user_prompt = f"POI名称：{poi['name']}\n描述：{poi['description']}\n请从预定义类别中为这个POI选择一个最合适的类别。"
            
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
                        category = "景点"
                
                # 更新数据库
                conn.execute(
                    "UPDATE pois SET category = ? WHERE id = ?",
                    (category, poi['id'])
                )
                
                print(f"将POI '{poi['name']}' 分类为 '{category}'")
                classified_count += 1
                
            except Exception as e:
                print(f"分类 '{poi['name']}' 时出错: {str(e)}")
                continue
        
        # 提交所有更改
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": f"成功为 {classified_count} 个POI分类",
            "classified_count": classified_count,
            "already_classified": len(already_classified)
        })
        
    except Exception as e:
        print(f"POI分类过程中出错: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"分类过程出错: {str(e)}"
        }), 500

# 生成POI之间的连接关系
def generate_links(pois, categories):
    links = []
    
    # 同类别间的连接
    for category in categories:
        category_pois = [poi for poi in pois if poi["category"] == category["name"]]
        
        # 连接同类别中的一些节点
        for i in range(len(category_pois) - 1):
            if random.random() > 0.3:  # 70%概率创建连接
                links.append({
                    "source": category_pois[i]["id"],
                    "target": category_pois[i + 1]["id"],
                    "strength": 0.7,
                    "type": "same-category"
                })
    
    # 跨类别连接
    for poi in pois:
        for i in range(2):  # 每个POI平均连接到2个其他随机POI
            target_poi = pois[math.floor(random.random() * len(pois))]
            if (target_poi["id"] != poi["id"] and 
                not any(link["source"] == poi["id"] and link["target"] == target_poi["id"] for link in links) and
                not any(link["source"] == target_poi["id"] and link["target"] == poi["id"] for link in links)):
                links.append({
                    "source": poi["id"],
                    "target": target_poi["id"],
                    "strength": 0.3,
                    "type": "cross-category"
                })
    
    # 热门地点之间的连接
    popular_pois = [poi for poi in pois if poi.get("popularity", 0) > 80]
    for poi in popular_pois:
        for target_poi in [p for p in pois if p["id"] != poi["id"] and p.get("popularity", 0) > 75]:
            if not any(link["source"] == poi["id"] and link["target"] == target_poi["id"] for link in links) and not any(link["source"] == target_poi["id"] and link["target"] == poi["id"] for link in links):
                links.append({
                    "source": poi["id"],
                    "target": target_poi["id"],
                    "strength": 0.5,
                    "type": "popular-connection"
                })
    
    return links

@app.route('/api/graph_data')
def get_graph_data():
    pois, categories = load_pois_for_graph()
    links = generate_links(pois, categories)
    
    # 生成节点数据
    nodes = []
    for poi in pois:
        # 优先使用category_type字段，如果为空则回退到category字段
        category = poi.get('category_type') or poi['category']
        color = None
        for cat in categories:
            if cat['name'] == category:
                color = cat['color']
                break
        
        if not color:
            color = "#607D8B"  # 默认颜色
        
        node = {
            "id": poi['id'],
            "name": poi['name'],
            "category": category,
            "color": color,
            "highlighted": False,  # 默认不高亮
            "rating": poi['rating'],
            "description": poi['description'],
            "coordinates": [poi['latitude'], poi['longitude']],
            "properties": {
                "price": poi['ticket_price'],
                "visit_time": poi['visit_time']
            }
        }
        nodes.append(node)
    
    # 获取所有使用的类别
    used_categories = set(node['category'] for node in nodes)
    
    # 过滤出实际在POI中使用的类别
    filtered_categories = [
        {"name": cat['name'], "color": cat['color']} 
        for cat in categories 
        if cat['name'] in used_categories
    ]
    
    return jsonify({
        "nodes": nodes,
        "links": links,
        "categories": filtered_categories
    })

# 为graph页面提供的数据API
@app.route('/api/data')
def get_data():
    # 从graph/poi.py的函数导入实现
    from graph.poi import load_pois, generate_links
    
    pois, categories = load_pois()
    links = generate_links(pois, categories)
    
    return jsonify({
        "nodes": pois,
        "links": links,
        "categories": categories
    })

# ====================== 智能问答API ======================

# 转义文本中的特殊字符，使其在JSON中安全
def escape_for_json(text):
    return json.dumps(text)[1:-1]

@app.route('/api/chat', methods=['GET', 'POST'])
def chat_api():
    if request.method == 'POST':
        data = request.json
        prompt = data.get('message', '')
        if not prompt:
            prompt = data.get('prompt', '')
        extract_preferences = data.get('extract_preferences', False)
        update_graph = data.get('update_graph', True)  # 新增参数，控制是否更新知识图谱
    else:  # GET 方法
        prompt = request.args.get('prompt', '')
        extract_preferences = request.args.get('extract_preferences', 'false').lower() == 'true'
        update_graph = request.args.get('update_graph', 'true').lower() == 'true'
    
    print(f"处理API请求: '{prompt}', 提取偏好: {extract_preferences}, 更新图谱: {update_graph}")
    
    if not prompt:
        return jsonify({"error": "没有提供问题内容"}), 400
    
    messages = [{"role": "user", "content": prompt}]
    
    try:
        # 如果需要提取旅行偏好
        if extract_preferences:
            # 添加系统指令，让模型分析旅行偏好
            system_message = {
                "role": "system", 
                "content": """
                分析用户的旅行需求，提取以下信息：
                1. 旅行主题/兴趣 (如历史文化、自然风光、茶文化、美食体验等)
                2. 行程天数 (默认为1天)
                3. 体力/强度水平 (高、中等、低)
                以JSON格式返回，不要有任何其他解释内容:
                {
                  "theme": "主题",
                  "days": 数字,
                  "energy": "高/中等/低"
                }
                """
            }
            messages.insert(0, system_message)
            
            print(f"提取旅行偏好中，用户输入: {prompt}")
            
            try:
                # 调用LLM，非流式响应
                response = client.chat.completions.create(
                    model="deepseek-r1-distill-qwen-32b-250120",
                    messages=messages,
                    stream=False,
                )
                
                try:
                    # 尝试解析LLM返回的JSON
                    content = response.choices[0].message.content
                    print(f"LLM返回内容: {content}")
                    
                    # 使用健壮的JSON提取函数
                    result = extract_json_from_text(content)
                    
                    if result and all(k in result for k in ['theme', 'days', 'energy']):
                        print(f"成功提取旅行偏好: {result}")
                        return jsonify(result)
                except Exception as e:
                    print(f"JSON解析失败: {e}, 使用备用方法提取偏好")
                    # JSON解析失败，回退到备用方法
                
                # 如果LLM响应不可用或JSON解析失败，使用备用方法
                print("LLM提取偏好失败，使用备用提取方法")
                result = extract_preferences_from_text(prompt)
                return jsonify(result)
                
            except Exception as e:
                print(f"提取旅行偏好时出错: {e}, 使用备用方法")
                # 使用备用方法从文本中提取偏好
                result = extract_preferences_from_text(prompt)
                return jsonify(result)
        
        # 常规对话流式响应
        print(f"处理用户常规对话: {prompt}")
        
        # 添加系统提示，要求LLM以结构化方式输出旅游路线规划
        system_message = {
            "role": "system",
            "content": """你是YouLing，一位专业的旅游顾问，擅长回答中国国内旅游相关问题。请提供准确、全面、实用的旅游建议，并遵循以下要求：

1. 专注于回答旅游相关问题，包括景点推荐、行程规划、交通建议、食宿推荐、旅游贴士、季节选择、花费预算等
2. 在回答问题时，尽量引用具体的信息，如地点名称、营业时间、票价、地址、交通路线等，使回答更有参考价值
3. 保持礼貌友好的语气，但不需要过多客套话
4. 对于旅游行程安排请求，必须以标准markdown格式提供结构化的旅行路线，采用以下格式：
   - 标题：## 推荐[X]天[目的地/主题]路线
   - 每天行程：### 第[N]天路线
   - 列出景点（只包含真实景点，不要使用任何占位符）：
     1. **景点名称**
        简短描述，包含地址、开放时间、建议游玩时间、交通等有用信息
   - 旅行建议部分：仅包含有实际内容的建议，如最佳游览时间、交通方式、建议携带物品、天气提醒等
   - 不要包含空的部分，如没有内容的"饮食推荐"、"住宿推荐"、"花费预算"等
   - 避免使用"景点1"、"景点2"这类无意义的占位符

5. 对于非旅游问题，婉拒回答并引导用户提出旅游相关问题
6. 回答应当简明扼要，信息密度高，避免冗长
7. 不要编造虚假信息，如不确定请坦诚表明

无论如何，你的回答都应该是有用的、安全的，并专注于旅游领域。"""
        }
        
        # 将系统提示添加到消息列表的开头
        messages.insert(0, system_message)
        
        # 用于存储完整回答的变量和已更新的图谱数据
        full_content = ""
        updated_graph_data = None
        
        # 流式响应逻辑
        def generate_stream_response():
            nonlocal full_content, updated_graph_data
            
            # 尝试调用真实LLM API
            try:
                print("使用LLM API获取旅游推荐...")
                response = client.chat.completions.create(
                    model="deepseek-r1-distill-qwen-32b-250120",
                    messages=messages,
                    stream=True,
                )
                
                is_reasoning = True
                
                for chunk in response:
                    if not chunk.choices or len(chunk.choices) == 0:
                        continue
                        
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        # 处理推理内容
                        content = delta.reasoning_content
                        content = escape_for_json(content)
                        yield f"data: {{\"type\": \"reasoning\", \"content\": \"{content}\"}}\n\n"
                    elif hasattr(delta, 'content') and delta.content:
                        if is_reasoning:
                            yield "data: {\"type\": \"separator\"}\n\n"
                            is_reasoning = False
                        # 处理内容
                        content = delta.content
                        content = escape_for_json(content)
                        yield f"data: {{\"type\": \"content\", \"content\": \"{content}\"}}\n\n"
                        # 累积完整内容
                        full_content += delta.content
                    # 如果是分隔标记
                    elif is_reasoning and len(chunk.choices) > 0:
                        yield "data: {\"type\": \"separator\"}\n\n"
                        is_reasoning = False
                
                # 更新知识图谱（如果启用）
                if update_graph and full_content and "**" in full_content:
                    try:
                        yield f"data: {{\"type\": \"status\", \"content\": \"正在基于推荐更新知识图谱...\"}}\n\n"
                        
                        # 导入POI Agent函数
                        from llm_poi_agent import llm_poi_agent
                        
                        # 创建数据库连接
                        conn = get_db_connection()
                        
                        # 调用agent处理
                        count = llm_poi_agent(full_content, client, conn)
                        
                        if count > 0:
                            # 更新成功，重新获取最新的图谱数据
                            with app.app_context():
                                # 获取JSON数据而不是Response对象
                                response = get_graph_data()
                                updated_graph_data = response.get_json()
                                
                            status_msg = f"已更新知识图谱，添加了{count}个景点"
                            # 发送更新的图谱数据
                            graph_json = json.dumps(updated_graph_data)
                            yield f"data: {{\"type\": \"graph_data\", \"content\": {graph_json}}}\n\n"
                        else:
                            try:
                                # 即使没有新增POI，也要确保知识图谱显示
                                with app.app_context():
                                    response = get_graph_data()
                                    graph_data = response.get_json()
                                    graph_json = json.dumps(graph_data)
                                    yield f"data: {{\"type\": \"graph_data\", \"content\": {graph_json}}}\n\n"
                                status_msg = "无法从推荐中提取新的POI信息，但已加载现有知识图谱"
                            except Exception as e:
                                print(f"获取现有知识图谱时出错: {str(e)}")
                                status_msg = "无法从推荐中提取有效的POI信息"
                        
                        yield f"data: {{\"type\": \"status\", \"content\": \"{escape_for_json(status_msg)}\"}}\n\n"
                    except Exception as e:
                        print(f"更新知识图谱时出错: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        error_msg = escape_for_json(str(e))
                        # 即使更新失败，也尝试加载现有知识图谱
                        try:
                            with app.app_context():
                                response = get_graph_data()
                                graph_data = response.get_json()
                                graph_json = json.dumps(graph_data)
                                yield f"data: {{\"type\": \"graph_data\", \"content\": {graph_json}}}\n\n"
                        except Exception as e2:
                            print(f"在错误恢复过程中获取知识图谱时出错: {str(e2)}")
                        yield f"data: {{\"type\": \"status\", \"content\": \"更新知识图谱时出错: {error_msg}\"}}\n\n"
                
                # 无论知识图谱是否更新成功，都保证发送结束事件
                yield "data: {\"type\": \"end\"}\n\n"
                
            except Exception as e:
                # 如果API调用失败，使用模拟响应
                print(f"API调用失败: {e}，使用模拟响应...")
                
                # 模拟思考过程和回答
                reasoning = f"""
                分析用户问题: "{prompt}"
                
                1. 提取关键信息:
                   - 用户可能关注的景点: {'未明确指定'}
                   - 旅行主题: {'一般文化体验'}
                   
                2. 旅行建议思路:
                   - 根据用户兴趣推荐相关景点
                   - 提供合理的行程安排
                   - 考虑交通和游览时间
                """
                
                # 生成结构化的答案
                answer = """## 推荐1天杭州文化体验路线

### 第1天路线

1. **西湖景区**
   杭州标志性景点，包含断桥残雪、平湖秋月、苏堤春晓等十景，环境优美，充满诗情画意。

2. **灵隐寺**
   著名佛教寺庙，始建于东晋，可搭配飞来峰石窟一起游览，感受佛教文化的庄严与宁静。

3. **龙井村**
   中国著名的茶文化发源地之一，可品尝正宗龙井茶，了解传统制茶工艺。

4. **河坊街/南宋御街**
   古色古香的传统商业街区，可品尝杭州特色小吃，购买丝绸等特色商品。

5. **西溪湿地**
   城市中的"绿肺"，有"宋代雅致"的水乡风光，适合傍晚时分游览，欣赏日落美景。

### 旅行建议

- 最佳游览时间：8:00-17:00
- 交通方式：公交、地铁、步行或打车
- 建议携带：舒适的鞋子、相机、遮阳伞
- 天气提醒：天气适宜，按计划游览即可，景色会很棒！

杭州公共交通便利，景点间距离适中。西湖景区大部分景点免费，只有雷峰塔、岳王庙等少数景点收费。"""

                full_content = answer  # 保存完整回答用于更新知识图谱
                
                # 首先发送思考过程
                for line in reasoning.strip().split('\n'):
                    if line.strip():
                        content = escape_for_json(line + "\n")
                        yield f"data: {{\"type\": \"reasoning\", \"content\": \"{content}\"}}\n\n"
                        time.sleep(0.05)  # 添加小延迟
                
                # 发送分隔符
                yield "data: {\"type\": \"separator\"}\n\n"
                time.sleep(0.2)  # 添加延迟
                
                # 发送回答内容
                for line in answer.split('\n'):
                    content = escape_for_json(line + "\n")
                    yield f"data: {{\"type\": \"content\", \"content\": \"{content}\"}}\n\n"
                    time.sleep(0.05)  # 添加小延迟
                
                # 更新知识图谱（如果启用）
                if update_graph:
                    try:
                        yield f"data: {{\"type\": \"status\", \"content\": \"正在基于推荐更新知识图谱...\"}}\n\n"
                        time.sleep(0.5)  # 添加延迟，模拟处理
                        
                        # 导入POI Agent函数
                        from llm_poi_agent import llm_poi_agent
                        
                        # 创建数据库连接
                        conn = get_db_connection()
                        
                        # 调用agent处理
                        count = llm_poi_agent(full_content, client, conn)
                        
                        if count > 0:
                            # 更新成功，重新获取最新的图谱数据
                            with app.app_context():
                                # 获取JSON数据而不是Response对象
                                response = get_graph_data()
                                updated_graph_data = response.get_json()
                                
                            status_msg = f"已更新知识图谱，添加了{count}个景点"
                            # 发送更新的图谱数据
                            graph_json = json.dumps(updated_graph_data)
                            yield f"data: {{\"type\": \"graph_data\", \"content\": {graph_json}}}\n\n"
                        else:
                            try:
                                # 即使没有新增POI，也要确保知识图谱显示
                                with app.app_context():
                                    response = get_graph_data()
                                    graph_data = response.get_json()
                                    graph_json = json.dumps(graph_data)
                                    yield f"data: {{\"type\": \"graph_data\", \"content\": {graph_json}}}\n\n"
                                status_msg = "无法从推荐中提取新的POI信息，但已加载现有知识图谱"
                            except Exception as e:
                                print(f"获取现有知识图谱时出错: {str(e)}")
                                status_msg = "无法从推荐中提取有效的POI信息"
                        
                        yield f"data: {{\"type\": \"status\", \"content\": \"{escape_for_json(status_msg)}\"}}\n\n"
                    except Exception as e:
                        print(f"更新知识图谱时出错: {str(e)}")
                        error_msg = escape_for_json(str(e))
                        # 即使更新失败，也尝试加载现有知识图谱
                        try:
                            with app.app_context():
                                response = get_graph_data()
                                graph_data = response.get_json()
                                graph_json = json.dumps(graph_data)
                                yield f"data: {{\"type\": \"graph_data\", \"content\": {graph_json}}}\n\n"
                        except Exception as e2:
                            print(f"在错误恢复过程中获取知识图谱时出错: {str(e2)}")
                        yield f"data: {{\"type\": \"status\", \"content\": \"更新知识图谱时出错: {error_msg}\"}}\n\n"
                
                # 无论知识图谱是否更新成功，都保证发送结束事件
                yield "data: {\"type\": \"end\"}\n\n"
        
        # 使用Stream响应
        return app.response_class(generate_stream_response(), mimetype='text/event-stream')
            
    except Exception as e:
        print(f"Chat API error: {e}")
        import traceback
        traceback.print_exc()
        # 返回错误信息
        return jsonify({"error": f"处理请求时出错: {str(e)}"}), 500

# 从文本中提取旅行偏好的辅助函数
def extract_preferences_from_text(text):
    # 提取主题
    theme = "文化体验"  # 默认主题
    
    # 更全面的主题检测
    if "西湖" in text or "断桥" in text or "雷峰塔" in text or "白堤" in text or "苏堤" in text:
        theme = "西湖景区"
    elif "灵隐寺" in text or "佛教" in text or "飞来峰" in text or "法喜" in text:
        theme = "佛教文化"
    elif "茶" in text or "龙井" in text or "茶园" in text or "茶艺" in text:
        theme = "茶文化"
    elif "历史" in text or "博物馆" in text or "古迹" in text or "文物" in text or "宋朝" in text:
        theme = "历史文化"
    elif "美食" in text or "饮食" in text or "小吃" in text or "餐厅" in text or "菜" in text:
        theme = "美食体验"
    elif "自然" in text or "风景" in text or "山" in text or "徒步" in text or "湿地" in text:
        theme = "自然风光"
    elif "购物" in text or "市场" in text or "商场" in text or "特产" in text:
        theme = "购物体验"
    
    # 提取天数
    days = 1  # 默认1天
    if "1天" in text or "一天" in text or "1日" in text:
        days = 1
    elif "2天" in text or "两天" in text or "二天" in text or "2日" in text:
        days = 2
    elif "3天" in text or "三天" in text or "3日" in text:
        days = 3
    elif "4天" in text or "四天" in text or "4日" in text:
        days = 4
    elif "5天" in text or "五天" in text or "5日" in text:
        days = 5
    elif "多天" in text or "长期" in text or "一周" in text:
        days = 5
        
    # 提取体力水平/强度
    energy = "中等"  # 默认中等强度
    if "轻松" in text or "休闲" in text or "缓慢" in text or "慢节奏" in text or "悠闲" in text:
        energy = "低"
    elif "高强度" in text or "快节奏" in text or "紧凑" in text or "充实" in text or "体力" in text:
        energy = "高"
    
    print(f"从文本中提取的旅行偏好: 主题={theme}, 天数={days}, 强度={energy}")
    
    # 确保返回一个有效的偏好字典
    return {
        "theme": theme,
        "days": days,
        "energy": energy
    }

# 新增用于同时返回路线和知识图谱高亮数据的API
@app.route('/api/unified_data', methods=['POST'])
def unified_data():
    try:
        data = request.json
        theme = data.get('theme', '文化体验')
        days = int(data.get('days', 1))
        energy = data.get('energy', '中等')
        
        print(f"处理统一数据请求: 主题={theme}, 天数={days}, 强度={energy}")
        
        # 创建空间感知RAG实例并执行
        rag = SpatialAwareRAG(theme, days, energy)
        result = rag.execute_full_rag_pipeline()
        
        # 找到被选中的POI
        selected_poi_ids = []
        for day in result['routes']:
            for poi in day:
                selected_poi_ids.append(poi['id'])
        
        print(f"选中的POI点: {selected_poi_ids}")
        
        # 构建知识图谱数据，并标记选中的节点
        graph_data = get_graph_data_with_highlights(selected_poi_ids)
        
        response_data = {
            'theme': theme,
            'days': days,
            'energy': energy,
            'routes': result['routes'],
            'graph_data': graph_data
        }
        
        print(f"统一数据生成完成，共{len(selected_poi_ids)}个POI点，{len(result['routes'])}天行程")
        return jsonify(response_data)
    except Exception as e:
        print(f"统一数据API错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"处理请求时出错: {str(e)}"}), 500

# 辅助函数：生成带有高亮标记的知识图谱数据
def get_graph_data_with_highlights(highlighted_poi_ids):
    try:
        # 从数据库加载POI数据
        pois, categories_list = load_pois_for_graph()
        
        # 创建类别颜色映射
        category_colors = {}
        for category in categories_list:
            category_colors[category['name']] = category['color']
        
        # 生成节点数据
        nodes = []
        for poi in pois:
            # 检查是否为高亮节点 - 仅根据传入的高亮ID列表判断，不依赖数据库字段
            is_highlighted = poi['id'] in highlighted_poi_ids
            
            # 优先使用category_type字段，如果为空则回退到category字段
            category = poi.get('category_type') or poi['category']
            color = category_colors.get(category, "#607D8B")  # 默认颜色
            
            node = {
                "id": poi['id'],
                "name": poi['name'],
                "category": category,
                "color": color,
                "highlighted": is_highlighted,  # 添加高亮标记
                "rating": poi['rating'],
                "description": poi['description'],
                "coordinates": [poi['latitude'], poi['longitude']],
                "properties": {
                    "price": poi['ticket_price'],
                    "visit_time": poi['visit_time']
                }
            }
            nodes.append(node)
        
        # 生成连接
        links = generate_links(pois, categories_list)
        
        # 获取所有使用的类别
        used_categories = set(node['category'] for node in nodes)
        
        # 过滤出实际在POI中使用的类别
        filtered_categories = [
            {"name": cat['name'], "color": cat['color']} 
            for cat in categories_list 
            if cat['name'] in used_categories
        ]
        
        return {
            "nodes": nodes,
            "links": links,
            "categories": filtered_categories
        }
    
    except Exception as e:
        print(f"生成知识图谱数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return {"nodes": [], "links": [], "categories": []}

# 静态文件路由
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# 天气API端点
@app.route('/api/weather')
def weather_api():
    location = request.args.get('location', '杭州')
    days = request.args.get('days', '3')
    
    try:
        days = int(days)
        if days < 1:
            days = 1
        elif days > 7:
            days = 7
    except ValueError:
        days = 3
    
    try:
        # 调用天气API获取数据
        print(f"正在获取{location}的天气数据...")
        
        # 确保天气函数正常工作，否则使用模拟数据
        try:
            raw_weather_data = get_comprehensive_weather(WEATHER_API_KEY, location, days)
            print(f"成功获取天气数据: {type(raw_weather_data)}")
            
            # 如果返回的数据不是JSON格式，则需要创建一个结构化的数据
            if not isinstance(raw_weather_data, dict):
                print("天气API返回的不是字典数据，创建模拟数据...")
                weather_data = create_mock_weather_data(location, days)
            else:
                weather_data = raw_weather_data
        except Exception as weather_error:
            print(f"天气API调用失败: {weather_error}，使用模拟数据")
            weather_data = create_mock_weather_data(location, days)
            
        return jsonify(weather_data)
    except Exception as e:
        print(f"获取天气数据失败: {e}")
        return jsonify(create_mock_weather_data(location, days, True))

# 创建模拟天气数据
def create_mock_weather_data(location, days, is_error=False):
    """创建模拟天气数据，格式与WeatherAPI.com兼容"""
    current_date = time.strftime("%Y-%m-%d")
    
    # 如果是错误情况，添加错误标记
    error_info = {"error": "无法获取真实天气数据"} if is_error else {}
    
    # 基本数据结构
    weather_data = {
        **error_info,
        "location": {
            "name": location,
            "region": "浙江",
            "country": "中国",
            "lat": 30.29,
            "lon": 120.16,
            "tz_id": "Asia/Shanghai",
            "localtime": time.strftime("%Y-%m-%d %H:%M")
        },
        "current": {
            "temp_c": 25,
            "temp_f": 77,
            "is_day": 1 if 6 <= int(time.strftime("%H")) <= 18 else 0,
            "condition": {
                "text": "晴",
                "code": 1000
            },
            "wind_mph": 5.6,
            "wind_kph": 9.0,
            "wind_degree": 350,
            "wind_dir": "N",
            "pressure_mb": 1015,
            "pressure_in": 30.0,
            "precip_mm": 0.0,
            "precip_in": 0.0,
            "humidity": 65,
            "cloud": 25,
            "feelslike_c": 26.5,
            "feelslike_f": 79.7,
            "vis_km": 10.0,
            "vis_miles": 6.2,
            "uv": 5.0,
            "gust_mph": 6.7,
            "gust_kph": 10.8
        },
        "forecast": {
            "forecastday": []
        }
    }
    
    # 添加预报数据
    for i in range(days):
        # 模拟不同天气条件
        conditions = ["晴", "多云", "小雨", "阴"]
        condition_codes = [1000, 1003, 1183, 1006]
        
        idx = i % len(conditions)
        condition = conditions[idx]
        code = condition_codes[idx]
        
        # 温度随机波动
        max_temp = 25 + random.randint(-3, 5)
        min_temp = max_temp - random.randint(5, 10)
        
        # 创建单日预报
        forecast_day = {
            "date": time.strftime("%Y-%m-%d", time.localtime(time.time() + 86400 * i)),
            "day": {
                "maxtemp_c": max_temp,
                "maxtemp_f": max_temp * 9/5 + 32,
                "mintemp_c": min_temp,
                "mintemp_f": min_temp * 9/5 + 32,
                "avgtemp_c": (max_temp + min_temp) / 2,
                "avgtemp_f": (max_temp + min_temp) / 2 * 9/5 + 32,
                "maxwind_mph": random.randint(5, 15),
                "maxwind_kph": random.randint(8, 25),
                "totalprecip_mm": 0.0 if condition == "晴" else random.randint(0, 10),
                "totalprecip_in": 0.0 if condition == "晴" else random.randint(0, 10) / 25.4,
                "totalsnow_cm": 0.0,
                "avgvis_km": 10.0,
                "avgvis_miles": 6.2,
                "avghumidity": random.randint(50, 85),
                "daily_will_it_rain": 0 if condition != "小雨" else 1,
                "daily_chance_of_rain": 0 if condition != "小雨" else random.randint(30, 90),
                "daily_will_it_snow": 0,
                "daily_chance_of_snow": 0,
                "condition": {
                    "text": condition,
                    "code": code
                },
                "uv": 4.0
            },
            "astro": {
                "sunrise": "06:30 AM",
                "sunset": "18:30 PM",
                "moonrise": "21:30 PM",
                "moonset": "09:30 AM",
                "moon_phase": "满月" if i % 28 == 14 else "上弦月" if i % 28 < 14 else "下弦月",
                "moon_illumination": random.randint(0, 100)
            }
        }
        
        weather_data["forecast"]["forecastday"].append(forecast_day)
    
    return weather_data

def extract_json_from_text(text):
    """从文本中提取JSON对象，使用多种策略尝试提取"""
    import json
    import re
    
    # 策略1：直接解析整个文本
    try:
        return json.loads(text)
    except:
        pass
    
    # 策略2：查找第一个完整的JSON对象 {内容}
    try:
        match = re.search(r'({.*?})', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except:
        pass
    
    # 策略3：尝试修复常见JSON错误并解析
    try:
        # 移除可能干扰解析的引号和特殊字符
        cleaned_text = re.sub(r'[\'"`](?=[\'"`])', '', text)
        # 尝试查找并解析
        match = re.search(r'({.*?})', cleaned_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except:
        pass
    
    return None

if __name__ == '__main__':
    app.run(debug=True, port=5000)