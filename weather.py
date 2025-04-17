import requests
from datetime import datetime

def get_comprehensive_weather(api_key, location, days=3):
    """
    获取全面的天气信息
    
    参数:
    - api_key: WeatherAPI.com的API密钥
    - location: 城市名、经纬度、邮编等
    - days: 预报天数（1-14之间）
    """
    # API基础URL
    base_url = "http://api.weatherapi.com/v1"
    
    # 请求参数
    params = {
        'key': api_key,
        'q': location,
        'days': days,
        'aqi': 'yes',  # 空气质量
        'alerts': 'yes'  # 天气预警
    }
    
    try:
        # 发起综合天气信息请求
        response = requests.get(f"{base_url}/forecast.json", params=params)
        response.raise_for_status()
        
        # 解析JSON响应
        weather_data = response.json()
        
        # 位置信息
        location_info = weather_data['location']
        print("=" * 50)
        print(f"📍 位置详情:")
        print(f"城市: {location_info['name']}")
        print(f"地区: {location_info['region']}")
        print(f"国家: {location_info['country']}")
        print(f"经纬度: {location_info['lat']}, {location_info['lon']}")
        print(f"时区: {location_info['tz_id']}")
        print(f"本地时间: {location_info['localtime']}")
        
        # 当前天气
        current = weather_data['current']
        print("\n" + "=" * 50)
        print("🌡️ 当前天气:")
        print(f"温度: {current['temp_c']}°C / {current['temp_f']}°F")
        print(f"体感温度: {current['feelslike_c']}°C / {current['feelslike_f']}°F")
        print(f"天气状况: {current['condition']['text']}")
        print(f"湿度: {current['humidity']}%")
        print(f"风速: {current['wind_kph']}公里/小时 ({current['wind_dir']})")
        print(f"阵风: {current['gust_kph']}公里/小时")
        print(f"气压: {current['pressure_mb']}百帕")
        print(f"能见度: {current['vis_km']}公里")
        print(f"云量: {current['cloud']}%")
        print(f"UV指数: {current['uv']}")
        
        # 空气质量
        if 'air_quality' in current:
            aqi = current['air_quality']
            print("\n" + "=" * 50)
            print("🌬️ 空气质量:")
            print(f"PM2.5: {aqi['pm2_5']} µg/m³")
            print(f"PM10: {aqi['pm10']} µg/m³")
            print(f"一氧化碳 (CO): {aqi['co']} µg/m³")
            print(f"二氧化氮 (NO2): {aqi['no2']} µg/m³")
            print(f"臭氧 (O3): {aqi['o3']} µg/m³")
            print(f"二氧化硫 (SO2): {aqi['so2']} µg/m³")
            print(f"US EPA空气质量指数: {aqi['us-epa-index']}")
        
        # 未来天气预报
        forecasts = weather_data['forecast']['forecastday']
        print("\n" + "=" * 50)
        print("🔮 未来天气预报:")
        for day in forecasts:
            print(f"\n日期: {day['date']}")
            print(f"最高温度: {day['day']['maxtemp_c']}°C")
            print(f"最低温度: {day['day']['mintemp_c']}°C")
            print(f"平均温度: {day['day']['avgtemp_c']}°C")
            print(f"天气状况: {day['day']['condition']['text']}")
            print(f"降水概率: 下雨{day['day']['daily_chance_of_rain']}% / 下雪{day['day']['daily_chance_of_snow']}%")
            print(f"总降水量: {day['day']['totalprecip_mm']}毫米")
            print(f"最大风速: {day['day']['maxwind_kph']}公里/小时")
            
            # 天文数据
            astro = day['astro']
            print("\n天文数据:")
            print(f"日出时间: {astro['sunrise']}")
            print(f"日落时间: {astro['sunset']}")
            print(f"月出时间: {astro['moonrise']}")
            print(f"月落时间: {astro['moonset']}")
            print(f"月相: {astro['moon_phase']}")
        
        # 天气预警
        if 'alerts' in weather_data and weather_data['alerts']['alert']:
            print("\n" + "=" * 50)
            print("⚠️ 天气预警:")
            for alert in weather_data['alerts']['alert']:
                print(f"标题: {alert['headline']}")
                print(f"严重程度: {alert['severity']}")
                print(f"事件: {alert['event']}")
    
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
    except KeyError as e:
        print(f"解析数据时发生错误: {e}")

# 使用示例
API_KEY = 'fa2a12d01c2245c8a9880339251004'
get_comprehensive_weather(API_KEY, 'hangzhou', days=3)