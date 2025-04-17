import pandas as pd
import requests
import os
import time

# 配置通义千问API（硅基流动平台）
GUIJI_API_KEY = "sk-qircmatuqnhkurgdzzjcorkmttxnbisgecvzajjigsbeervq"
GUIJI_API_URL = "https://api.siliconflow.cn/v1/chat/completions"

def extract_core_content(text):
    """
    调用通义千问API提取文本的核心内容
    """
    try:
        # 构建提示语
        prompt = f"""
        请提取以下文本的核心内容：
        {text}
        要求：
        1. 简洁明了，突出关键信息。
        2. 不超过100字。
        """
        
        # 通过硅基流动平台API调用通义千问
        headers = {
            "Authorization": f"Bearer {GUIJI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "Qwen/Qwen2.5-72B-Instruct",  # 替换为平台支持的模型名称
            "messages": [
                {"role": "system", "content": "你是一位专业的信息提取专家，能够准确提取文本的核心内容。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        response = requests.post(GUIJI_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # 检查请求是否成功
        
        result = response.json()
        
        # 提取生成的内容（根据实际API返回格式调整）
        if "choices" in result and len(result["choices"]) > 0:
            core_content = result["choices"][0]["message"]["content"].strip()
            return core_content
        else:
            return text[:100]  # 如果未正确获取内容，返回前100个字符
        
    except Exception as e:
        print(f"通义千问API调用失败: {e}")
        return text[:100]  # 返回前100个字符作为备选

def process_csv(file_path):
    """
    读取CSV文件，提取核心内容并保存为新的CSV文件
    """
    # 读取CSV文件
    df = pd.read_csv(file_path)
    
    # 初始化提取内容列
    df['提取内容'] = ''
    
    # 遍历每一行
    for index, row in df.iterrows():
        # 合并description和有内容的Unnamed字段
        text = str(row['description'])
        unnamed_columns = [col for col in df.columns if col.startswith('Unnamed')]
        for col in unnamed_columns:
            if pd.notna(row[col]):
                text += f" {str(row[col])}"
        
        # 提取核心内容
        core_content = extract_core_content(text)
        
        # 更新提取内容列
        df.at[index, '提取内容'] = core_content
    
    # 选择需要的列
    result_df = df[['name', 'latitude', 'longitude', '提取内容']]
    
    # 保存为新的CSV文件
    output_file = 'extracted_core_content.csv'
    result_df.to_csv(output_file, index=False)
    
    print(f"核心内容提取完成，结果保存为 {output_file}")

# 使用示例
process_csv('new_data.csv')


import requests

# 定义指数退避算法的最大重试次数和初始等待时间
MAX_RETRIES = 5
INITIAL_BACKOFF = 1

def call_api_with_retry(url, headers, data):
    retries = 0
    backoff = INITIAL_BACKOFF

    while retries < MAX_RETRIES:
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # 检查响应状态码
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 429:
                print(f"请求频率过高，等待 {backoff} 秒后重试...")
                time.sleep(backoff)
                backoff *= 2  # 指数退避，每次等待时间翻倍
                retries += 1
            else:
                print(f"API 调用失败: {http_err}")
                break
        except Exception as err:
            print(f"发生未知错误: {err}")
            break

    print("达到最大重试次数，API 调用失败。")
    return None

# 示例调用
url = "https://api.siliconflow.cn/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}
data = {
    "prompt": "你的请求数据",
    "max_tokens": 100
}

result = call_api_with_retry(url, headers, data)
if result:
    print(result)