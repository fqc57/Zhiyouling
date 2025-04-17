import requests
import json

def test_tongyi_api():
    """
    测试通义千问API连接和响应
    可以在命令行单独运行此函数测试API配置是否正确
    """
    print("开始测试通义千问API...")

    try:
        # API配置
        api_key = "sk-qircmatuqnhkurgdzzjcorkmttxnbisgecvzajjigsbeervq"  # 替换为您的API密钥
        api_url = "https://api.siliconflow.cn/v1/chat/completions"  # 确保URL正确

        # 构建简单测试请求
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "Qwen/Qwen2.5-72B-Instruct",  # 替换为平台支持的模型名称
            "messages": [
                {"role": "system", "content": "你是一位文化旅游专家。"},
                {"role": "user", "content": "请简短介绍一下西湖龙井茶的文化背景，100字以内。"}
            ],
            "temperature": 0.7,
            "max_tokens": 200
        }

        # 发送请求
        print("发送API请求...")
        response = requests.post(api_url, headers=headers, json=payload)

        # 检查响应
        if response.status_code == 200:
            result = response.json()
            print("API响应成功!")
            print("生成的内容:")
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(content)
            else:
                print("未找到生成内容，API返回格式可能有变化。")
                print("完整响应:", json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"API请求失败，状态码: {response.status_code}")
            print("错误信息:", response.text)

    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")

    print("API测试完成。")

# 如果需要单独测试API，可以取消下面注释
if __name__ == "__main__":
    test_tongyi_api()