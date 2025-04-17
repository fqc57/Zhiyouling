from flask import Flask, render_template, request, jsonify, Response
import os
import time
#import sys
#sys.path.append('C:\\Users\\13620\\.conda\\envs\\youling\\lib\\site-packages')
from volcenginesdkarkruntime import Ark
from dotenv import load_dotenv
import json

app = Flask(__name__)
load_dotenv()

# 初始化Ark客户端
client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key="0c2d99af-ab7d-4925-8b3d-6d645015c443",
)

def print_with_delay(text, delay=0.03):
    """
    逐字打印文本，模拟打字效果
    """
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)

def escape_for_json(text):
    """
    处理文本中的特殊字符，使其在JSON中安全
    """
    # 对文本进行JSON编码并移除首尾的引号
    return json.dumps(text)[1:-1]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    def generate():
        # 首先进行深度思考
        stream = client.chat.completions.create(
            model="deepseek-r1-distill-qwen-32b-250120",
            messages=[
                {"role": "system", "content": "你是一个AI助手，请先进行深度思考，然后再给出最终答案。"},
                {"role": "user", "content": user_message},
            ],
            stream=True,
        )
        
        thinking_content = ""
        final_content = ""
        is_thinking = True
        
        for chunk in stream:
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content or ""
            
            if is_thinking:
                thinking_content += content
                if "最终答案" in thinking_content or "总结" in thinking_content:
                    is_thinking = False
                    yield f"data: {{'type': 'thinking', 'content': '{thinking_content}'}}\n\n"
                    continue
                yield f"data: {{'type': 'thinking', 'content': '{content}'}}\n\n"
            else:
                final_content += content
                yield f"data: {{'type': 'final', 'content': '{content}'}}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/chat', methods=['GET', 'POST'])
def chat_api():
    if request.method == 'POST':
        data = request.json
        prompt = data.get('prompt', '')
    else:  # GET 方法
        prompt = request.args.get('prompt', '')
    
    messages = [{"role": "user", "content": prompt}]
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

if __name__ == '__main__':
    app.run(debug=True) 