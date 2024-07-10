from IPython.display import Image, display
import base64
import os
from openai import OpenAI 
import re


# Open the image file and encode it as a base64 string
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def get_response(MODEL,client,role_system,instruction,image):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": role_system},
            {"role": "user", "content": [
                {"type": "text", "text": instruction},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image}",
                    "detail": "high"
                    }
                }
            ]}
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content

# 提取JSON内容
def extract_json_content(message_content):
    json_match = re.search(r'(\{(?:[^\{\}]*\n){8,}[^\{\}]*\})', message_content)
    if not json_match:
        raise ValueError("No JSON content found in the response")
    return json_match.group(1)



def main():
    ## Set the API key and model name
    MODEL="gpt-4o"
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    IMAGE_PATH = "/Users/zhouziyao/Desktop/LLM_Smart_Oven_Controll/openai-env/data/chicken.jpeg"
    base64_image = encode_image(IMAGE_PATH)
    # 提示词
    role_system="You are an AI trained to be responsible for planning a food roasting process in an oven (3.5 kW, 60L)."
    prompt = """
    Your task is to first identify through a picture of the food its properties. Then you should use these informations to figure out a roasting plan in form of JSON file. It should sequentially include the food’s heat capacity, weight, water content, initial temperature, heat surface area and roasting plan — first time period, first time period temperature, first time period fan speed, second time period…(if there is any)
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
    response=get_response(MODEL,client,role_system,prompt,base64_image)
    print("\n==========Original Response============\n")
    print(response)
    json=extract_json_content(response)
    print("\n==========Generated Roasting Plan JSON============\n")
    print(json)

if __name__ == "__main__":
    main()



