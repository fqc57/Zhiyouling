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
import chardet

# 尝试导入Ark SDK，如果不可用则创建一个模拟版本
try:
    from volcenginesdkarkruntime import Ark
    # 初始化Ark客户端
    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key="0c2d99af-ab7d-4925-8b3d-6d645015c443",
    )
except ImportError:
    # 创建模拟客户端，用于演示目的
    class MockArk:
        class ChatCompletions:
            def create(self, model, messages, stream=False):
                # 模拟流式响应
                class MockResponse:
                    def __init__(self):
                        self.choices = []
                        self.count = 0
                        # 预设的思考内容和回答
                        self.reasoning = [
                            "让我思考一下这个旅游规划问题...",
                            "首先，我需要分析用户的偏好和约束条件。",
                            "根据用户的问题，他们对杭州旅游感兴趣，需要进行行程规划。",
                            "杭州的主要景点包括西湖、灵隐寺、西溪湿地等。",
                            "考虑到时间和交通因素，我会按照地理位置和景点类型进行合理分组。",
                            "西湖`周边景点可以安排在一起，包括断桥、雷峰塔等。",
                            "我还需要考虑景点的开放时间、游览所需时间和最佳游览季节。"
                        ]
                        self.answers = [
                            "根据您的需求，我为您规划了以下杭州3天行程：",
                            "\n第1天：西湖景区",
                            "- 上午：断桥残雪 → 白堤 → 平湖秋月",
                            "- 下午：雷峰塔 → 六和塔",
                            "- 晚上：西湖音乐喷泉，南宋御街夜景",
                            "\n第2天：历史文化体验",
                            "- 上午：灵隐寺 → 飞来峰",
                            "- 下午：西溪湿地公园",
                            "- 晚上：河坊街品尝杭州特色美食",
                            "\n第3天：特色景点",
                            "- 上午：龙井村，体验茶文化",
                            "- 下午：杭州博物馆 → 中国丝绸博物馆",
                            "- 晚上：清河坊古街，购买伴手礼",
                            "\n贴心提示：",
                            "1. 西湖景区建议早起，避开人流高峰",
                            "2. 龙井村春季可体验采茶活动",
                            "3. 杭州特色美食有西湖醋鱼、东坡肉、龙井虾仁等",
                            "\n希望您在杭州旅游愉快！"
                        ]
                    
                    def __iter__(self):
                        return self
                    
                    def __next__(self):
                        # 模拟每次返回一小部分内容
                        if self.count < len(self.reasoning) + len(self.answers):
                            response = type('obj', (object,), {
                                'choices': [
                                    type('obj', (object,), {
                                        'delta': type('obj', (object,), {})
                                    })
                                ]
                            })
                            
                            # 先返回推理内容，然后返回最终答案
                            if self.count < len(self.reasoning):
                                text = self.reasoning[self.count]
                                response.choices[0].delta.reasoning_content = text
                            else:
                                text = self.answers[self.count - len(self.reasoning)]
                                response.choices[0].delta.content = text
                                
                            self.count += 1
                            return response
                        else:
                            raise StopIteration
                
                return MockResponse()
        
        def __init__(self):
            self.chat = type('obj', (object,), {'completions': self.ChatCompletions()})
    
    client = MockArk()

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
        visit_time INTEGER
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
            (1, "西湖断桥", 30.2587, 120.1486, "断桥是《白蛇传》故事发生地，也是西湖十景之一", "景点", 4.7, 0, 60),
            (2, "雷峰塔", 30.2317, 120.1485, "雷峰塔与白蛇传传说密切相关，是南宋时期建造", "古迹", 4.5, 40, 90),
            (3, "龙井村", 30.2193, 120.1056, "西湖龙井茶原产地，有十八棵御茶树等景点", "文化体验", 4.6, 0, 120),
            (4, "岳庙", 30.2542, 120.1327, "纪念南宋抗金名将岳飞的祠庙", "历史古迹", 4.4, 25, 60),
            (5, "南宋官窑遗址", 30.1923, 120.1309, "南宋时期皇家御用瓷器的烧制地", "历史遗址", 4.3, 30, 120),
            (6, "孤山", 30.2546, 120.1428, "西湖中最大的自然岛，有西泠印社等景点", "自然景观", 4.5, 0, 90),
            (7, "中国茶叶博物馆", 30.2278, 120.1364, "展示中国茶文化历史的专业博物馆", "博物馆", 4.7, 0, 150),
            (8, "青藤茶馆", 30.2585, 120.1481, "西湖边有名的传统茶馆，环境优美", "茶馆", 4.6, 60, 120),
            (9, "胡雪岩故居", 30.2497, 120.1775, "清末著名徽商胡雪岩的豪宅，展示徽派建筑", "历史建筑", 4.4, 25, 90),
            (10, "灵隐寺", 30.2441, 120.1226, "历史悠久的佛教寺庙，周围自然环境优美", "寺庙", 4.8, 45, 180)
        ]
        
        cursor.executemany(
            "INSERT INTO pois (id, name, latitude, longitude, description, category, rating, ticket_price, visit_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            pois
        )
        
        # 插入文化标签数据
        cultural_tags = [
            (1, 1, "白蛇传", 1.5),
            (2, 1, "爱情传说", 1.2),
            (3, 1, "拍照胜地", 1.0),
            (4, 2, "白蛇传", 1.5),
            (5, 2, "南宋建筑", 1.3),
            (6, 2, "佛教文化", 1.1),
            (7, 3, "茶文化", 1.8),
            (8, 3, "龙井茶", 1.6),
            (9, 3, "乾隆下江南", 1.4),
            (10, 4, "南宋历史", 1.7),
            (11, 4, "岳飞精忠报国", 1.5),
            (12, 4, "爱国主义", 1.3),
            (13, 5, "南宋历史", 1.6),
            (14, 5, "古陶瓷", 1.4),
            (15, 5, "非遗技艺", 1.2),
            (16, 6, "西泠印社", 1.5),
            (17, 6, "文人雅士", 1.3),
            (18, 6, "自然景观", 1.0),
            (19, 7, "茶文化", 1.7),
            (20, 7, "历史文物", 1.5),
            (21, 8, "茶文化", 1.6),
            (22, 8, "休闲体验", 1.2),
            (23, 9, "徽商文化", 1.5),
            (24, 9, "徽派建筑", 1.4),
            (25, 10, "佛教文化", 1.7),
            (26, 10, "自然景观", 1.3)
        ]
        
        cursor.executemany(
            "INSERT INTO cultural_tags (id, poi_id, tag, weight) VALUES (?, ?, ?, ?)",
            cultural_tags
        )
        
        # 插入用户评论数据
        comments = [
            (1, 1, "断桥人太多！推荐早起6点去，晨雾中的断桥像水墨画。桥东侧200米有家藕粉店超好吃！", "早起,晨雾,人多,美食", 0.7),
            (2, 1, "《白蛇传》故事发生地，可以听讲解了解许仙白娘子的故事，冬天来看雪景最美。", "白蛇传,故事,雪景", 0.9),
            (3, 2, "雷峰塔落日绝美！建议下午5点去，塔顶能看到西湖全景。旁边有个小众拍照点，塔西侧500米的小亭子人少！", "落日,拍照,全景,人少", 0.8),
            (4, 3, "龙井村采茶体验超棒！茶农会教炒茶，记得去'十八棵御茶树'打卡，乾隆钦点的贡茶园！", "采茶,炒茶,御茶树,乾隆", 0.9),
            (5, 4, "岳飞墓值得一看，'精忠报国'四个大字震撼人心，记得读一读碑文了解岳飞的故事。", "精忠报国,历史,故事", 0.8),
            (6, 5, "南宋官窑遗址门票30元，可以亲手做陶器！关联龙井茶文化，古代茶具都是这里烧制的～", "陶器,体验,茶具,历史", 0.7),
            (7, 6, "孤山梅花开了！推荐骑行路线：断桥→白堤→孤山，沿途有清代行宫遗址，人少景美！", "梅花,骑行,历史遗迹", 0.9),
            (8, 7, "免费博物馆！展示了唐宋茶具，还能体验宋代点茶。馆后茶园适合拍古风照～", "免费,茶具,体验,拍照", 0.8),
            (9, 8, "雨天必去青藤茶馆！人均60元，窗外是西湖雨景，配龙井茶和茶点，氛围感拉满～", "雨天,龙井茶,氛围,景观", 0.9),
            (10, 9, "胡雪岩故居展示了清末徽商的辉煌，建筑非常精美，推荐请讲解了解背后的商业传奇。", "徽商,建筑,历史,故事", 0.8),
            (11, 10, "灵隐寺香火旺盛，建议避开节假日。寺前的飞来峰石窟值得细看，有宋代以来的石刻。", "佛教,石窟,避开节假日", 0.7)
        ]
        
        cursor.executemany(
            "INSERT INTO comments (id, poi_id, content, keywords, sentiment) VALUES (?, ?, ?, ?, ?)",
            comments
        )
        
        conn.commit()
    
    conn.close()

# 初始化数据库和加载数据
init_db()
add_sample_data()

# ====================== 路由定义 ======================

# 主页路由
@app.route('/')
def index():
    return render_template('index_integrated.html')

# 空间RAG部分的路由
@app.route('/rag')
def rag_page():
    return render_template('rag.html')

# 知识图谱部分的路由
@app.route('/knowledge_graph')
def knowledge_graph():
    return render_template('knowledge_graph.html')

# 智能问答部分的路由
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


# 空间感知RAG API
@app.route('/api/routes', methods=['POST'])
def get_routes():
    data = request.json
    theme = data.get('theme', '茶文化')  # Default tea culture theme
    days = data.get('days', 1)  # Default 1 day itinerary
    energy = data.get('energy', '中等')  # Default medium energy level
    
    print(f"Route request: theme={theme}, days={days}, energy={energy}")
    
    conn = get_db_connection()
    
    # Get theme-related POIs
    cursor = conn.execute('''
        SELECT p.*, t.tag, t.weight
        FROM pois p
        JOIN cultural_tags t ON p.id = t.poi_id
        WHERE t.tag LIKE ?
        ORDER BY t.weight DESC, p.rating DESC
    ''', (f'%{theme}%',))
    
    theme_pois = cursor.fetchall()
    
    print(f"Found {len(theme_pois)} POIs related to theme '{theme}'")
    
    # If no POIs found for the theme, try a more general search
    if not theme_pois:
        cursor = conn.execute('''
            SELECT p.*, NULL as tag, 1.0 as weight
            FROM pois p
            ORDER BY p.rating DESC
            LIMIT 10
        ''')
        theme_pois = cursor.fetchall()
        print(f"Using fallback: retrieved {len(theme_pois)} general POIs")
    
    # Get comment data for route planning reference
    cursor = conn.execute('''
        SELECT c.*
        FROM comments c
        JOIN pois p ON c.poi_id = p.id
        WHERE p.id IN (SELECT DISTINCT poi_id FROM cultural_tags WHERE tag LIKE ?)
    ''', (f'%{theme}%',))
    
    comments = cursor.fetchall()
    conn.close()
    
    # Simple route planning algorithm
    selected_pois = []
    total_time = 0
    max_time_per_day = 8 * 60  # 8 hours (minutes)
    
    if energy == '高':
        max_time_per_day = 10 * 60  # 10 hours (minutes)
    elif energy == '低':
        max_time_per_day = 6 * 60  # 6 hours (minutes)
    
    max_total_time = days * max_time_per_day
    
    theme_pois_dict = {}
    for poi in theme_pois:
        poi_id = poi['id']
        if poi_id not in theme_pois_dict:
            theme_pois_dict[poi_id] = {
                'poi': dict(poi),
                'weight': poi['weight']
            }
        else:
            theme_pois_dict[poi_id]['weight'] += poi['weight']
    
    # Sort by weight
    sorted_pois = sorted(theme_pois_dict.values(), key=lambda x: x['weight'], reverse=True)
    
    print(f"Sorted POIs by weight: {len(sorted_pois)} unique POIs")
    
    # Greedy algorithm to select POIs
    for poi_data in sorted_pois:
        poi = poi_data['poi']
        visit_time = poi['visit_time']
        
        # Consider travel time (simplified, assume 30 minutes between each POI)
        if selected_pois:
            visit_time += 30
        
        if total_time + visit_time <= max_total_time:
            selected_pois.append(dict(poi))
            total_time += visit_time
    
    print(f"Selected {len(selected_pois)} POIs for the route")
    
    # Ensure we have at least one POI per day
    if len(selected_pois) < days:
        print(f"Warning: Not enough POIs selected ({len(selected_pois)}) for {days} days")
        # If no POIs were selected, use fallback to include at least some points
        if not selected_pois:
            conn = get_db_connection()
            fallback_pois = conn.execute('SELECT * FROM pois LIMIT ?', (days,)).fetchall()
            conn.close()
            selected_pois = [dict(poi) for poi in fallback_pois]
            print(f"Using fallback: added {len(selected_pois)} POIs")
    
    # Group routes by day
    routes = []
    current_day = []
    current_day_time = 0
    
    for poi in selected_pois:
        visit_time = poi['visit_time']
        transport_time = 30 if current_day else 0
        
        if current_day_time + visit_time + transport_time <= max_time_per_day:
            current_day.append(poi)
            current_day_time += visit_time + transport_time
        else:
            routes.append(current_day)
            current_day = [poi]
            current_day_time = poi['visit_time']
    
    if current_day:
        routes.append(current_day)
    
    # Ensure we have enough days
    while len(routes) < days:
        # Copy some POIs from the first day if necessary
        if routes:
            new_day = routes[0][:min(2, len(routes[0]))]  # Take up to 2 POIs from day 1
            routes.append(new_day)
        else:
            # This should never happen, but as a fallback
            conn = get_db_connection()
            fallback_poi = conn.execute('SELECT * FROM pois LIMIT 1').fetchone()
            conn.close()
            if fallback_poi:
                routes.append([dict(fallback_poi)])
    
    # Generate cultural descriptions (in a real application this would call LLM API)
    for day_index, day_route in enumerate(routes):
        for poi_index, poi in enumerate(day_route):
            poi['cultural_description'] = generate_cultural_description(poi)
    
    result = {
        'theme': theme,
        'days': days,
        'energy': energy,
        'routes': routes
    }
    
    print(f"Generated route with {len(routes)} days, {sum(len(day) for day in routes)} total POIs")
    
    return jsonify(result)

#地图可视化
# 生成地图可视化
@app.route('/api/map', methods=['POST'])
def generate_map():
    data = request.json
    routes = data.get('routes', [])
    
    # Add better debug logging
    print(f"Received routes data: {routes}")
    
    # Better validation
    if not routes:
        print("Routes data is empty.")
        return jsonify({"error": "Routes data is empty.", "map_url": ""})
    
    # Check if each route contains the required fields
    for day_index, day_route in enumerate(routes):
        for poi_index, poi in enumerate(day_route):
            if 'latitude' not in poi or 'longitude' not in poi or 'name' not in poi:
                error_msg = f"POI at day {day_index+1}, index {poi_index} is missing required fields."
                print(error_msg)
                return jsonify({"error": error_msg, "map_url": ""})

    try:
        # Create the map, but don't specify the tile layer
        m = folium.Map(
            location=[30.2500, 120.1500], 
            zoom_start=13,
            tiles=None  # Disable default tile layer
        )
        
        # Add Amap tile layer (normal map)
        amap_url = 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
        
        # Add Amap layer
        folium.TileLayer(
            tiles=amap_url,
            attr='&copy; <a href="https://www.amap.com/">高德地图</a>',
            name='高德地图',
            overlay=False,
            control=True
        ).add_to(m)

        # Optional: Add Amap satellite layer
        amap_satellite_url = 'https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}'
        folium.TileLayer(
            tiles=amap_satellite_url,
            attr='&copy; <a href="https://www.amap.com/">高德卫星图</a>',
            name='高德卫星图',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add layer controller, allowing users to switch layers
        folium.LayerControl().add_to(m)
        
        colors = ['red', 'blue', 'green', 'purple', 'orange']
        
        for day_index, day_route in enumerate(routes):
            color = colors[day_index % len(colors)]
            
            # Add POI markers
            for poi_index, poi in enumerate(day_route):
                popup_content = f"<b>{poi['name']}</b><br>{poi.get('description', '')}"
                tooltip_content = f"第{day_index+1}天 - 景点{poi_index+1}: {poi['name']}"
                
                folium.Marker(
                    [poi['latitude'], poi['longitude']],
                    popup=popup_content,
                    tooltip=tooltip_content,
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(m)
                
                # Connect routes
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
        
        # Make sure static directory exists
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        
        # Save map to static directory
        map_file = f'route_map_{int(time.time())}.html'  # Add timestamp to prevent caching
        map_path = os.path.join(static_dir, map_file)
        m.save(map_path)
        
        # Get map HTML content to return directly
        map_html = m._repr_html_()
        
        # Return relative URL path to static and HTML content
        return jsonify({
            "map_url": f"/static/{map_file}",
            "map_html": map_html
        })
        
    except Exception as e:
        error_msg = f"Error generating map: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())  # Print the full traceback for debugging
        return jsonify({"error": error_msg, "map_url": ""})
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
    conn = get_db_connection()
    comments = conn.execute('SELECT * FROM comments').fetchall()
    conn.close()
    
    # 提取所有关键词
    all_keywords = []
    for comment in comments:
        if comment['keywords']:
            all_keywords.extend(comment['keywords'].split(','))
    
    # 统计关键词频率
    keyword_counter = Counter(all_keywords)
    top_keywords = keyword_counter.most_common(10)
    
    return jsonify({
        "keywords": [{"keyword": k, "count": c} for k, c in top_keywords]
    })

# ====================== 知识图谱API ======================

# 读取POI数据
def load_pois_for_graph():
    # 基础POI数据
    pois = [
        {
            "id": 1,
            "name": "西湖",
            "category": "自然景观",
            "description": "中国著名的淡水湖，被誉为人间天堂，拥有十景、新十景等众多景点",
            "rating": 4.8,
            "reviews": 8765,
            "popularity": 95,
            "address": "浙江省杭州市西湖区龙井路1号",
            "opening_hours": "全天开放",
            "ticket_price": "免费，部分景点需购票",
            "best_season": "四季皆宜，春季看花，夏季看荷，秋季赏月，冬季观雪",
            "historical_significance": "拥有两千多年历史，是中国首批国家重点风景名胜区，1985年被评为中国十大风景名胜之一，2011年被列入世界文化遗产名录",
            "transportation": "公交：K7、K4、Y2、Y9等；地铁：1号线龙翔桥站、2号线龙翔桥站",
            "tips": "建议准备一天时间游览，可租借自行车环湖，断桥残雪、平湖秋月、雷峰夕照是必看景点",
            "image": "static/images/west-lake.jpg",
            "year": 2011
        },
        {
            "id": 2,
            "name": "灵隐寺",
            "category": "历史古迹",
            "description": "中国佛教禅宗十大古刹之一，始建于东晋咸和元年（326年）",
            "rating": 4.6,
            "reviews": 5432,
            "popularity": 85,
            "address": "浙江省杭州市西湖区灵隐路法云弄1号",
            "opening_hours": "夏季(4月-10月) 07:30-18:00；冬季(11月-次年3月) 07:30-17:30",
            "ticket_price": "门票45元，飞来峰景区35元，联票45+35=80元",
            "best_season": "春秋两季，尤其是春季杜鹃花开时节",
            "historical_significance": "始建于东晋年间，是杭州最古老的刹院，千百年香火不断。曾名'云林寺'，唐代改今名，意为'灵气所隐'",
            "transportation": "公交：Y1、Y2、Y7、324路等；地铁：暂无直达地铁",
            "tips": "参观寺庙需着装得体，避免穿短裤短裙。香火旺盛，节假日游客较多，建议避开高峰",
            "image": "static/images/lingyin-temple.jpg",
            "year": 2008
        },
        {
            "id": 3,
            "name": "断桥残雪",
            "category": "自然景观",
            "description": "西湖十景之一，因《白蛇传》故事而闻名，是西湖标志性景点",
            "rating": 4.6,
            "reviews": 3241,
            "popularity": 82,
            "address": "浙江省杭州市西湖区白堤路北端",
            "opening_hours": "全天开放",
            "ticket_price": "免费",
            "best_season": "四季皆宜，冬季下雪时观赏'断桥残雪'景观最佳",
            "historical_significance": "断桥历史悠久，始建于五代后晋开运年间（944年），因《白蛇传》中许仙与白娘子的邂逅地而更加出名",
            "transportation": "公交：Y1路、Y9路、K7路等；地铁：1号线龙翔桥站",
            "tips": "此处游客众多，建议早晨或傍晚前往。冬季初雪时，桥上积雪融化，形成'半黑半白'的奇景，故称'断桥残雪'",
            "image": "static/images/broken-bridge.jpg",
            "year": 2010
        }
    ]
    
    # 增加额外数据，包括分类信息
    categories = [
        {"name": "自然景观", "color": "#2c7bb6", "icon": "tree"},
        {"name": "历史古迹", "color": "#d7191c", "icon": "landmark"},
        {"name": "文化场所", "color": "#fdae61", "icon": "museum"},
        {"name": "购物区域", "color": "#abd9e9", "icon": "shopping-bag"},
        {"name": "美食街区", "color": "#66bd63", "icon": "utensils"}
    ]
    
    return pois, categories

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
        prompt = data.get('prompt', '')
    else:  # GET 方法
        prompt = request.args.get('prompt', '')
    
    messages = [{"role": "user", "content": prompt}]
    
    try:
        response = client.chat.completions.create(
            model="deepseek-r1-distill-qwen-32b-250120",
            messages=messages,
            stream=True,
        )
        
        is_reasoning = True
        
        def generate():
            nonlocal is_reasoning
            for chunk in response:
                if not chunk.choices:
                    continue
                    
                if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                    # 处理特殊字符
                    content = chunk.choices[0].delta.reasoning_content
                    content = escape_for_json(content)
                    yield f"data: {{\"type\": \"reasoning\", \"content\": \"{content}\"}}\n\n"
                elif hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    if is_reasoning:
                        yield "data: {\"type\": \"separator\"}\n\n"
                        is_reasoning = False
                    # 处理特殊字符
                    content = chunk.choices[0].delta.content
                    content = escape_for_json(content)
                    yield f"data: {{\"type\": \"content\", \"content\": \"{content}\"}}\n\n"
        
        return app.response_class(generate(), mimetype='text/event-stream')
    except Exception as e:
        print(f"Chat API error: {e}")
        # 返回错误信息
        return jsonify({"error": "处理请求时出错，请稍后重试"}), 500

# 静态文件路由
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)