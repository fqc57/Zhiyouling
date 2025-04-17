import pandas as pd
import sqlite3
import json
import re
import os
# Add the import of the chardet module
import chardet
import jieba.analyse
import random

filter_csv_path = 'extracted_core_content.csv'
db_path = 'travel_db.sqlite'

# Read the filter.csv file
def read_filter_csv(file_path):
    # Detect the file encoding
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    
    # Read the CSV file
    # Replace error_bad_lines with on_bad_lines
    df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='warn')
    return df

# 提取关键词作为文化标签
def extract_cultural_tags(text, topK=3):
    if pd.isna(text) or text.strip() == '':
        return []
    tags = jieba.analyse.extract_tags(text, topK=topK)
    return tags

# 提取评论内容和关键词
def extract_comments(text):
    if pd.isna(text) or text.strip() == '':
        return None, []
    # 提取评论内容
    content = text
    # 提取关键词
    keywords = jieba.analyse.extract_tags(text, topK=5)
    return content, keywords

# 生成POI数据
def generate_pois(df):
    pois = []
    for idx, row in df.iterrows():
        name = row.get('name', f'景点_{idx}')
        latitude = row.get('latitude', 30.0 + idx * 0.01)
        longitude = row.get('longitude', 120.0 + idx * 0.01)
        description = row.get('提取内容', f'{name}是一个著名景点')
        category = '景点'
        rating = 4.5
        ticket_price = 0
        visit_time = 60
        
        pois.append((
            idx + 1, name, latitude, longitude, description,
            category, rating, ticket_price, visit_time
        ))
    return pois

# 生成文化标签数据
def generate_cultural_tags(df):
    tags = []
    tag_id = 1
    for idx, row in df.iterrows():
        poi_id = idx + 1
        text = row.get('提取内容', '')
        cultural_tags = extract_cultural_tags(text)
        for tag in cultural_tags:
            tags.append((tag_id, poi_id, tag, 1.0))
            tag_id += 1
    return tags

# 生成用户评论数据
def generate_comments(df):
    comments = []
    comment_id = 1
    for idx, row in df.iterrows():
        poi_id = idx + 1
        text = row.get('提取内容', '')
        content, keywords = extract_comments(text)
        if content:
            sentiment = round(random.uniform(0.5, 0.9), 1)
            keywords_str = ','.join(keywords)
            comments.append((comment_id, poi_id, content, keywords_str, sentiment))
            comment_id += 1
    return comments

# 插入数据到数据库
def insert_data_to_db(pois, cultural_tags, comments):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the sqlite_sequence table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
    result = cursor.fetchone()
    
    # Clear existing data
    cursor.execute("DELETE FROM comments")
    cursor.execute("DELETE FROM cultural_tags")
    cursor.execute("DELETE FROM pois")
    
    # Reset the auto - increment ID
    if result:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='pois'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='cultural_tags'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='comments'")
    
    # Insert POI data
    cursor.executemany(
        "INSERT INTO pois (id, name, latitude, longitude, description, category, rating, ticket_price, visit_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        pois
    )
    
    # Insert cultural tag data
    if cultural_tags:
        cursor.executemany(
            "INSERT INTO cultural_tags (id, poi_id, tag, weight) VALUES (?, ?, ?, ?)",
            cultural_tags
        )
    
    # Insert comment data
    if comments:
        cursor.executemany(
            "INSERT INTO comments (id, poi_id, content, keywords, sentiment) VALUES (?, ?, ?, ?, ?)",
            comments
        )
    
    conn.commit()
    conn.close()

# 主函数
def main():
    # 读取filter.csv
    df = read_filter_csv(filter_csv_path)
    
    # 生成数据
    pois = generate_pois(df)
    cultural_tags = generate_cultural_tags(df)
    comments = generate_comments(df)
    
    # 插入数据库
    insert_data_to_db(pois, cultural_tags, comments)
    
    print(f"成功插入 {len(pois)} 个POI，{len(cultural_tags)} 个文化标签，{len(comments)} 条评论")

if __name__ == '__main__':
    main()