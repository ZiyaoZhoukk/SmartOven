import os
import base64
import requests
import re

# 从环境变量中读取API密钥
def get_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key not found in environment variables. Please set OPENAI_API_KEY.")
    return api_key

# 编码图像
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 构建请求头
def build_headers(api_key):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

# 构建请求负载
def build_payload(prompt, base64_image):
    return {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 400
    }

# 发送请求并获取响应
def get_response(payload, headers):
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}: {response.text}")
    return response.json()

# 提取JSON内容
# def extract_json_content(response_data):
#     message_content = response_data['choices'][0]['message']['content']
#     json_match = re.search(r'(\{(?:.*\n){8,}.*\})', message_content, re.DOTALL)
#     if not json_match:
#         raise ValueError("No JSON content found in the response")
#     return json_match.group(1)
def extract_json_content(response_data):
    message_content = response_data['choices'][0]['message']['content']
    # 匹配最外层的 JSON 大括号，并且至少包含九行
    json_match = re.search(r'(\{(?:[^\{\}]*\n){8,}[^\{\}]*\})', message_content)
    if not json_match:
        raise ValueError("No JSON content found in the response")
    return json_match.group(1)


# 主函数
def main():
    api_key = get_api_key()
    image_path = "/Users/zhouziyao/Desktop/LLM_Smart_Oven_Controll/openai-env/data/chicken.jpeg"
    base64_image = encode_image(image_path)
    
    prompt = """
    You are an AI trained to be responsible for planning a food roasting process in an oven (3.5 kW, 60L). Your task is to first identify through a picture of the food its properties. Then you should use these informations to figure out a roasting plan in form of JSON file. It should sequentially include the food’s heat capacity, weight, water content, initial temperature, heat surface area and roasting plan — first time period, first time period temperature, first time period fan speed, second time period…(if there is any)
    The generated JSON file should be key-value pairs, and the keys should look exactly like this:
    {
      "type of food": "one pair of chicken wing",
      "heat_capacity": "1000",
      "m": "0.2",
      "water_content": "60",
      "initial_temp": "30", 
      "A": "0.02",
      "first_period": "1200",
      "first_period_temp": "226",
      "first_period_fan_speed": "2500",
      "second_period": "300",
      "second_period_temp": "190",
      "second_period_fan_speed": "1800"
    }
    Important Hints:
    Remember to take a close look at the picture to try not to wrongly estimate the properties.
    Remember to use your knowledge to plan the roasting process to avoid overcook.
    """
    
    headers = build_headers(api_key)
    payload = build_payload(prompt, base64_image)
    response_data = get_response(payload, headers)
    
    print("\n=======original response========\n")
    print(response_data)
    
    json_content = extract_json_content(response_data)
    
    print("\n==========Generated Roasting Plan JSON============\n")
    print(json_content)

if __name__ == "__main__":
    main()
