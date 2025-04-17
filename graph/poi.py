from flask import Flask, render_template, jsonify
import json
import random
import math

app = Flask(__name__)

# 读取POI数据
def load_pois():
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
        "name": "河坊街",
        "category": "文化场所",
        "description": "杭州历史最为悠久的街区之一，保存着明清时期特色的建筑风格",
        "rating": 4.5,
        "reviews": 4321,
        "popularity": 80,
        "address": "浙江省杭州市上城区河坊街",
        "opening_hours": "全天开放，店铺一般9:00-21:00",
        "ticket_price": "免费",
        "best_season": "四季皆宜",
        "historical_significance": "始建于南宋，曾是杭州的政治、经济、文化中心，是杭州城市发展的缩影",
        "transportation": "公交：8路、K4路、Y6路等；地铁：1号线定安路站",
        "tips": "这里有许多传统手工艺和特色小吃，是购买伴手礼的好地方。知味观、奎元馆都有百年历史",
        "image": "static/images/hefang-street.jpg",
        "year": 2009
    },
    {
        "id": 4,
        "name": "西溪湿地",
        "category": "自然景观",
        "description": "中国首个国家湿地公园，拥有'一曲溪流绕桑田'的自然风光",
        "rating": 4.4,
        "reviews": 3256,
        "popularity": 75,
        "address": "浙江省杭州市西湖区天目山路518号",
        "opening_hours": "08:00-17:30（16:30停止入园）",
        "ticket_price": "80元（主入口），周边其他入口票价不同",
        "best_season": "春秋两季，尤其是春季花开和秋季芦苇飘摇时",
        "historical_significance": "拥有2000多年历史的农耕文明，是城市中罕见的集农业遗产、文化遗产和湿地生态于一体的湿地类型",
        "transportation": "公交：B支4、B支5、286路等；地铁：暂无直达地铁",
        "tips": "建议乘坐园内摇橹船游览，可深入湿地腹地。春季可观赏梅花，秋季可观芦苇和候鸟",
        "image": "static/images/xixi-wetland.jpg",
        "year": 2012
    },
    {
        "id": 5,
        "name": "雷峰塔",
        "category": "历史古迹",
        "description": "位于西湖南岸夕照山的宝塔，与白堤、断桥、孤山共同构成西湖美景",
        "rating": 4.5,
        "reviews": 2987,
        "popularity": 80,
        "address": "浙江省杭州市西湖区南山路15号",
        "opening_hours": "08:00-21:30（20:30停止入场）",
        "ticket_price": "40元",
        "best_season": "四季皆宜，傍晚时分欣赏'雷峰夕照'最佳",
        "historical_significance": "始建于北宋太平兴国年间（977年），为吴越王钱弘俶为庆祝黄妃得子而建。与《白蛇传》故事紧密相连",
        "transportation": "公交：4路、7路、K4路、游1路等；地铁：1号线龙翔桥站",
        "tips": "登塔可俯瞰西湖全景，塔内有白蛇传说的文物展示，现在的塔是2002年重建的",
        "image": "static/images/leifeng-pagoda.jpg",
        "year": 2010
    },
    {
        "id": 6,
        "name": "吴山广场",
        "category": "购物区域",
        "description": "杭州市中心的大型综合广场，周边商业繁华，是购物娱乐的热门地点",
        "rating": 4.2,
        "reviews": 1876,
        "popularity": 72,
        "address": "浙江省杭州市上城区延安路与中山中路交叉口",
        "opening_hours": "全天开放，商场一般10:00-22:00",
        "ticket_price": "免费",
        "best_season": "四季皆宜",
        "historical_significance": "吴山又名城北山，是杭州城的发祥地，历来是兵家必争之地，也是历代文人墨客吟咏的胜地",
        "transportation": "公交：游B1、K4路、K207路等；地铁：1号线定安路站",
        "tips": "登吴山可俯瞰杭城全景，广场周边有许多特色小吃和购物场所，晚上夜景很美",
        "image": "static/images/wushan-square.jpg",
        "year": 2015
    },
    {
        "id": 7,
        "name": "龙井茶园",
        "category": "自然景观",
        "description": "中国十大名茶之首龙井茶的原产地，风景优美的茶文化体验胜地",
        "rating": 4.7,
        "reviews": 3421,
        "popularity": 83,
        "address": "浙江省杭州市西湖区龙井路1号",
        "opening_hours": "08:30-17:00",
        "ticket_price": "免费（部分茶园或茶室有消费)",
        "best_season": "春季（3-5月）是采茶季节，景色最美",
        "historical_significance": "龙井茶有1200多年历史，清乾隆皇帝游览西湖时，曾赐予狮峰山下胡公庙前的十八棵茶树'御茶'称号",
        "transportation": "公交：27路、87路、游览车Y1路、Y2路等",
        "tips": "可以体验采茶和制茶过程，品尝正宗龙井茶。明前龙井茶品质最佳但价格较高",
        "image": "static/images/longjing-tea.jpg",
        "year": 2007
    },
    {
        "id": 8,
        "name": "京杭大运河",
        "category": "历史古迹",
        "description": "世界上里程最长、工程最大的古代运河，贯通北京和杭州",
        "rating": 4.3,
        "reviews": 2345,
        "popularity": 75,
        "address": "浙江省杭州市拱墅区大关路",
        "opening_hours": "全天开放，夜游船需购票",
        "ticket_price": "免费参观，游船80-120元不等",
        "best_season": "春秋两季，夏季夜游也很美",
        "historical_significance": "始建于春秋时期，完成于隋唐时期，已有2500多年历史。是中国古代劳动人民创造的一项伟大工程，2014年被列入世界文化遗产名录",
        "transportation": "公交：62路、402路等；地铁：1号线打铁关站",
        "tips": "可以乘坐运河游船体验水上风光，沿岸的桥西历史街区有许多老建筑和文创店铺",
        "image": "static/images/grand-canal.jpg",
        "year": 2014
    },
    {
        "id": 9,
        "name": "中国丝绸博物馆",
        "category": "文化场所",
        "description": "全球规模最大的丝绸专题博物馆，展示了中国丝绸的发展历史",
        "rating": 4.4,
        "reviews": 1765,
        "popularity": 68,
        "address": "浙江省杭州市西湖区玉皇山路73-1号",
        "opening_hours": "09:00-17:00，周一闭馆（法定节假日除外）",
        "ticket_price": "免费（需提前预约）",
        "best_season": "四季皆宜",
        "historical_significance": "杭州是中国著名的丝绸之府，有'丝绸之路'起点和'丝绸之府'的美誉",
        "transportation": "公交：K808路、K504路、308路等；地铁：暂无直达地铁",
        "tips": "博物馆内有丝绸织造演示，可以了解从蚕到丝的完整过程。周边有购买正宗丝绸制品的商店",
        "image": "static/images/silk-museum.jpg",
        "year": 2013
    },
    {
        "id": 10,
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
    },
    {
        "id": 11,
        "name": "清河坊古街",
        "category": "美食街区",
        "description": "保存着明清时期建筑风格的古街，汇集众多杭州特色美食和手工艺品",
        "rating": 4.5,
        "reviews": 4567,
        "popularity": 88,
        "address": "浙江省杭州市上城区中河中路",
        "opening_hours": "全天开放，店铺一般9:00-22:00",
        "ticket_price": "免费",
        "best_season": "四季皆宜",
        "historical_significance": "始建于南宋，是杭州最古老的商业街之一，曾是南宋都城临安的皇城根脚，也是明清时期杭州城内最繁华的街区",
        "transportation": "公交：8路、K4路、Y6路等；地铁：1号线定安路站",
        "tips": "这里有知味观、奎元馆等百年老店，可以品尝杭州特色菜点如西湖醋鱼、东坡肉、龙井虾仁等。街上还有各种传统手工艺品商店",
        "image": "static/images/qinghefang.jpg",
        "year": 2008
    },
    {
        "id": 12,
        "name": "宋城景区",
        "category": "文化场所",
        "description": "以宋代文化为主题的大型综合性主题公园，《宋城千古情》是必看演出",
        "rating": 4.3,
        "reviews": 3987,
        "popularity": 78,
        "address": "浙江省杭州市西湖区之江路148号",
        "opening_hours": "09:00-22:00",
        "ticket_price": "宋城景区门票+《宋城千古情》演出票套票290元",
        "best_season": "四季皆宜",
        "historical_significance": "宋城是以宋代文化为主题的仿古建筑群，再现了南宋时期临安城的繁华景象",
        "transportation": "公交：324路、4路、K4路、Y10路等；地铁：暂无直达地铁",
        "tips": "一定要观看《宋城千古情》演出，提前预订位置。景区内机动游戏和特色美食众多，可安排一整天时间游玩",
        "image": "static/images/songcheng.jpg",
        "year": 2016
    },
    {
        "id": 13,
        "name": "六和塔",
        "category": "历史古迹",
        "description": "位于钱塘江畔的古塔，是杭州的标志性建筑之一",
        "rating": 4.4,
        "reviews": 2134,
        "popularity": 76,
        "address": "浙江省杭州市西湖区之江路16号",
        "opening_hours": "07:00-17:30（17:00停止入场）",
        "ticket_price": "门票20元，登塔另收费10元",
        "best_season": "四季皆宜",
        "historical_significance": "始建于北宋开宝三年（970年），因'和合僧徒'、'协调佛法'、'调停江潮'而得名，是中国早期木构多角楼阁式砖塔的杰出代表",
        "transportation": "公交：334路、287路、308路等；地铁：暂无直达地铁",
        "tips": "登塔可远眺钱塘江和杭州市区风光。秋季可在此观潮，是观赏钱塘江大潮的绝佳位置",
        "image": "static/images/six-harmonies.jpg",
        "year": 2011
    },
    {
        "id": 14,
        "name": "阿里巴巴总部",
        "category": "文化场所",
        "description": "中国最大电商公司的总部园区，展示了杭州互联网经济发展成就",
        "rating": 4.1,
        "reviews": 1243,
        "popularity": 65,
        "address": "浙江省杭州市余杭区文一西路969号",
        "opening_hours": "工作日09:00-17:00（需提前预约）",
        "ticket_price": "免费参观（需提前申请）",
        "best_season": "四季皆宜",
        "historical_significance": "阿里巴巴是中国最大的电子商务公司，由马云于1999年在杭州创立，象征着中国互联网经济崛起",
        "transportation": "公交：356路、周家村专线等；地铁：暂无直达地铁",
        "tips": "参观需提前申请并获得批准，一般只接待团体参观。园区内有阿里巴巴发展历史展示",
        "image": "static/images/alibaba.jpg",
        "year": 2018
    },
    {
        "id": 15,
        "name": "武林广场",
        "category": "购物区域",
        "description": "杭州市中心的现代化广场，周边是高端商业区和购物中心",
        "rating": 4.2,
        "reviews": 1876,
        "popularity": 70,
        "address": "浙江省杭州市下城区延安路武林广场",
        "opening_hours": "全天开放，商场一般10:00-22:00",
        "ticket_price": "免费",
        "best_season": "四季皆宜",
        "historical_significance": "武林广场始建于1998年，是杭州现代城市建设的象征，广场地下建有大型商业中心",
        "transportation": "公交：多条线路经过；地铁：1号线武林广场站",
        "tips": "这里是杭州的商业中心，周边有银泰百货、杭州大厦等大型购物中心。每晚有音乐喷泉表演",
        "image": "static/images/wulin-square.jpg",
        "year": 2015
    },
    {
        "id": 16,
        "name": "中山公园",
        "category": "自然景观",
        "description": "杭州市区内的综合性公园，环境优美，设施齐全",
        "rating": 4.3,
        "reviews": 1654,
        "popularity": 72,
        "address": "浙江省杭州市上城区孝友路1号",
        "opening_hours": "06:00-21:00",
        "ticket_price": "免费",
        "best_season": "春季花开时节最美",
        "historical_significance": "前身为清代的'督憲第花园'，民国时期改名为中山公园，是为纪念孙中山先生而建",
        "transportation": "公交：K7路、K818路、186路等；地铁：1号线凤起路站",
        "tips": "公园内设有健身设施、茶室和儿童游乐区，是市民休闲的好去处。春季樱花和牡丹盛开时很美",
        "image": "static/images/zhongshan-park.jpg",
        "year": 2012
    },
    {
        "id": 17,
        "name": "杭州菜博物馆",
        "category": "美食街区",
        "description": "展示杭帮菜历史文化的专题博物馆，可品尝正宗杭帮菜",
        "rating": 4.4,
        "reviews": 1456,
        "popularity": 68,
        "address": "浙江省杭州市西湖区玉皇山路221号",
        "opening_hours": "09:00-17:00，周一闭馆（法定节假日除外）",
        "ticket_price": "免费参观，餐厅消费另计",
        "best_season": "四季皆宜",
        "historical_significance": "杭帮菜是中国八大菜系之一，以西湖本地食材和精细刀工著称，历史可追溯到南宋时期",
        "transportation": "公交：Y9路、游3路、308路等；地铁：暂无直达地铁",
        "tips": "博物馆内有杭帮菜馆，可以品尝正宗的西湖醋鱼、龙井虾仁、叫花鸡等特色菜肴",
        "image": "static/images/cuisine-museum.jpg",
        "year": 2017
    },
    {
        "id": 18,
        "name": "胡雪岩故居",
        "category": "历史古迹",
        "description": "清代著名商人胡雪岩的豪宅，展示了晚清时期江南富商的生活方式",
        "rating": 4.5,
        "reviews": 1876,
        "popularity": 75,
        "address": "浙江省杭州市上城区元宝街18号",
        "opening_hours": "08:30-17:00",
        "ticket_price": "成人票50元",
        "best_season": "四季皆宜",
        "historical_significance": "胡雪岩（1823-1885）是清代著名红顶商人，其故居'义和庄'建于清同治年间，是中国近代建筑史上的杰作",
        "transportation": "公交：7路、K186路、K506路等；地铁：1号线凤起路站",
        "tips": "故居分为官厅、家厅、财厅三部分，可以看到精美的清代园林建筑和室内陈设。参观时注意保护文物",
        "image": "static/images/huxueyan.jpg",
        "year": 2009
    },
    {
        "id": 19,
        "name": "吴山夜市",
        "category": "美食街区",
        "description": "位于吴山广场附近的夜市，汇集了杭州各种特色小吃和美食",
        "rating": 4.6,
        "reviews": 3456,
        "popularity": 85,
        "address": "浙江省杭州市上城区高银街、吴山路一带",
        "opening_hours": "17:00-24:00",
        "ticket_price": "免费",
        "best_season": "四季皆宜，夏秋季节尤佳",
        "historical_significance": "吴山夜市形成于20世纪90年代，逐渐发展成为杭州最著名的美食夜市之一",
        "transportation": "公交：游B1、K4路、K207路等；地铁：1号线定安路站",
        "tips": "这里可以品尝到杭州各种特色小吃，如片儿川、臭豆腐、糯米蒸肉、荷叶粉蒸肉、面线糊等。夜市人流量大，注意看管好随身物品",
        "image": "static/images/wushan-night.jpg",
        "year": 2013
    },
    {
        "id": 20,
        "name": "杭州湾湿地公园",
        "category": "自然景观",
        "description": "杭州湾滨海区域的大型生态湿地，是候鸟栖息地和生态保护区",
        "rating": 4.2,
        "reviews": 1243,
        "popularity": 70,
        "address": "浙江省杭州市萧山区义桥镇",
        "opening_hours": "08:30-17:00",
        "ticket_price": "60元",
        "best_season": "春秋两季，每年10-11月是观鸟最佳时节",
        "historical_significance": "杭州湾湿地是中国东部沿海重要的候鸟迁徙驿站，也是长江三角洲地区重要的生态屏障",
        "transportation": "公交：萧山K215路、K216路等；自驾更为方便",
        "tips": "建议携带望远镜观鸟，秋季可以看到大批候鸟迁徙。园内有木栈道和观鸟塔，适合生态旅游和摄影",
        "image": "static/images/bay-wetland.jpg",
        "year": 2014
    },
    # 额外增加的10个景点
    {
        "id": 21,
        "name": "杭州植物园",
        "category": "自然景观",
        "description": "位于西湖风景区内的综合性植物园，拥有丰富的植物种类和园林景观",
        "rating": 4.4,
        "reviews": 2876,
        "popularity": 73,
        "address": "浙江省杭州市西湖区玉泉街739号",
        "opening_hours": "07:30-17:30（17:00停止入园）",
        "ticket_price": "15元",
        "best_season": "春季赏花，秋季观叶",
        "historical_significance": "始建于1956年，是浙江省规模最大的植物园，也是全国重点植物园之一",
        "transportation": "公交：Y2路、Y5路、K4路等；地铁：暂无直达地铁",
        "tips": "园内有多个专类园，如桃园、牡丹园、兰花园等，春季可观赏樱花和郁金香",
        "image": "static/images/botanic-garden.jpg",
        "year": 2006
    },
    {
        "id": 22,
        "name": "小河直街",
        "category": "文化场所",
        "description": "贯穿杭州城东的历史文化街区，沿河而建，保存着传统水乡风貌",
        "rating": 4.3,
        "reviews": 1987,
        "popularity": 74,
        "address": "浙江省杭州市上城区小河直街",
        "opening_hours": "全天开放，店铺一般9:00-21:00",
        "ticket_price": "免费",
        "best_season": "四季皆宜",
        "historical_significance": "始建于明清时期，是杭州城内保存较为完好的历史街区之一，展示了传统江南水乡的生活风貌",
        "transportation": "公交：592路、K216路等；地铁：4号线小河站",
        "tips": "街区有许多传统手工艺店铺和特色小吃，非常适合漫步体验老杭州的市井生活",
        "image": "static/images/xiaohe-street.jpg",
        "year": 2010
    },
    {
        "id": 23,
        "name": "钱江新城",
        "category": "购物区域",
        "description": "杭州城市新区和商业中心，拥有标志性的城市天际线和现代建筑群",
        "rating": 4.5,
        "reviews": 2765,
        "popularity": 78,
        "address": "浙江省杭州市江干区钱江新城",
        "opening_hours": "全天开放，商场一般10:00-22:00",
        "ticket_price": "免费",
        "best_season": "四季皆宜，夜景尤佳",
        "historical_significance": "钱江新城是杭州在21世纪初开发的现代化城市新区，象征着杭州的城市转型与经济发展",
        "transportation": "公交：多条线路；地铁：1号线钱江路站、2号线钱江世纪城站",
        "tips": "建议晚上前往，观赏杭州最美的城市夜景。钱江新城CBD有杭州最高的建筑和著名的'城市阳台'",
        "image": "static/images/qianjiang-new-city.jpg",
        "year": 2016
    },
    {
        "id": 24,
        "name": "梅家坞",
        "category": "自然景观",
        "description": "西湖周边著名的茶文化村落，以茶园风光和乡村风情闻名",
        "rating": 4.6,
        "reviews": 2143,
        "popularity": 76,
        "address": "浙江省杭州市西湖区梅灵南路",
        "opening_hours": "全天开放，茶室一般8:00-18:00",
        "ticket_price": "免费",
        "best_season": "春季采茶季最佳",
        "historical_significance": "梅家坞有着悠久的茶文化历史，是西湖龙井茶核心产区之一，自宋代以来就以产茶著称",
        "transportation": "公交：Y2路、K304路等；地铁：暂无直达地铁",
        "tips": "可以参观茶园，品尝正宗西湖龙井茶，体验采茶乐趣。山间有多条徒步路线，景色宜人",
        "image": "static/images/meijia-wu.jpg",
        "year": 2008
    },
    {
        "id": 25,
        "name": "杭州奥体中心",
        "category": "文化场所",
        "description": "2022年杭州亚运会主场馆，集体育、商业、休闲于一体的现代化综合体",
        "rating": 4.7,
        "reviews": 3254,
        "popularity": 85,
        "address": "浙江省杭州市萧山区钱塘江南岸",
        "opening_hours": "09:00-21:00（根据活动安排可能调整）",
        "ticket_price": "免费参观，活动期间需购票",
        "best_season": "四季皆宜",
        "historical_significance": "为2022年杭州亚运会修建的标志性建筑，是杭州城市发展的新地标",
        "transportation": "公交：B4路、B6路等；地铁：暂无直达地铁",
        "tips": "建筑外形独特，被称为'大莲花'，值得一看。周边有大型商业综合体和休闲设施",
        "image": "static/images/olympic-center.jpg",
        "year": 2021
    },
    {
        "id": 26,
        "name": "九溪烟树",
        "category": "自然景观",
        "description": "西湖十景之一，清幽的山谷溪流和自然风光",
        "rating": 4.5,
        "reviews": 1865,
        "popularity": 77,
        "address": "浙江省杭州市西湖区九溪路",
        "opening_hours": "全天开放",
        "ticket_price": "免费",
        "best_season": "春秋两季最佳",
        "historical_significance": "九溪烟树是西湖新十景之一，自古以来就是文人墨客游览的胜地，因'溪水九曲十八弯'而得名",
        "transportation": "公交：Y2路、游览线路；地铁：暂无直达地铁",
        "tips": "九溪是徒步爱好者的天堂，有多条登山路线。雨后或清晨有薄雾时景色最美，可一路徒步至钱塘江",
        "image": "static/images/jiuxi.jpg",
        "year": 2007
    },
    {
        "id": 27,
        "name": "杭州历史博物馆",
        "category": "文化场所",
        "description": "展示杭州悠久历史文化的专题博物馆，收藏了大量珍贵文物",
        "rating": 4.4,
        "reviews": 1765,
        "popularity": 72,
        "address": "浙江省杭州市上城区南山路25号",
        "opening_hours": "09:00-17:00，周一闭馆（法定节假日除外）",
        "ticket_price": "免费（需提前预约）",
        "best_season": "四季皆宜",
        "historical_significance": "博物馆建于原南宋行宫遗址上，见证了杭州作为南宋都城'临安'的辉煌历史",
        "transportation": "公交：K4路、K207路等；地铁：1号线定安路站",
        "tips": "馆内有关于杭州丝绸、茶叶、南宋文化的专题展览，值得历史爱好者参观",
        "image": "static/images/history-museum.jpg",
        "year": 2009
    },
    {
        "id": 28,
        "name": "湘湖景区",
        "category": "自然景观",
        "description": "位于杭州萧山区的国家级风景名胜区，融合了自然风光和人文景观",
        "rating": 4.3,
        "reviews": 2354,
        "popularity": 75,
        "address": "浙江省杭州市萧山区湘湖旅游度假区",
        "opening_hours": "08:00-17:30",
        "ticket_price": "80元",
        "best_season": "春秋两季最佳",
        "historical_significance": "湘湖历史悠久，公元前2200年左右就有人类活动，是著名的'跨湖桥文化'遗址所在地",
        "transportation": "公交：萧山309路、游1路等；地铁：暂无直达地铁",
        "tips": "景区内有古镇、湿地公园和水上活动项目，可乘坐游船欣赏湖光山色",
        "image": "static/images/xianghu-lake.jpg",
        "year": 2013
    },
    {
        "id": 29,
        "name": "杭州野生动物世界",
        "category": "文化场所",
        "description": "浙江省规模最大的野生动物园，拥有多种珍稀动物和互动体验项目",
        "rating": 4.2,
        "reviews": 3876,
        "popularity": 83,
        "address": "浙江省杭州市富阳区杭富路九龙大道1号",
        "opening_hours": "08:30-17:00（16:00停止入园）",
        "ticket_price": "成人票220元",
        "best_season": "春秋两季最佳，避开酷暑和严寒",
        "historical_significance": "建立于2000年，是华东地区重要的野生动物保护和科普教育基地",
        "transportation": "公交：富阳公交专线；自驾更为方便",
        "tips": "园区分为步行区和车行区，建议准备一整天时间游玩。喂食表演和动物巡游很受欢迎",
        "image": "static/images/wildlife-park.jpg",
        "year": 2015
    },
    {
        "id": 30,
        "name": "千岛湖",
        "category": "自然景观",
        "description": "中国国家级风景名胜区，以湖泊众多的岛屿和清澈的湖水闻名",
        "rating": 4.8,
        "reviews": 5678,
        "popularity": 92,
        "address": "浙江省杭州市淳安县千岛湖镇",
        "opening_hours": "全天开放，景区8:00-17:00",
        "ticket_price": "中心湖区联票230元",
        "best_season": "四季皆宜，夏季避暑胜地",
        "historical_significance": "千岛湖是新安江水库蓄水后形成的人工湖，因湖中有1078个岛屿而得名，是华东地区最大的淡水湖",
        "transportation": "公交：杭州汽车东站有直达班车；自驾沿杭千高速",
        "tips": "可乘坐游船环湖游览，品尝正宗的千岛湖有机鱼头。景区很大，建议安排2-3天时间游玩",
        "image": "static/images/qiandao-lake.jpg",
        "year": 2005
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
    popular_pois = [poi for poi in pois if poi["popularity"] > 80]
    for poi in popular_pois:
        for target_poi in [p for p in pois if p["id"] != poi["id"] and p["popularity"] > 75]:
            if not any(link["source"] == poi["id"] and link["target"] == target_poi["id"] for link in links) and not any(link["source"] == target_poi["id"] and link["target"] == poi["id"] for link in links):
                links.append({
                    "source": poi["id"],
                    "target": target_poi["id"],
                    "strength": 0.5,
                    "type": "popular-connection"
                })
    
    return links

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    pois, categories = load_pois()
    links = generate_links(pois, categories)
    
    return jsonify({
        "nodes": pois,
        "links": links,
        "categories": categories
    })

# 提供静态文件
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)