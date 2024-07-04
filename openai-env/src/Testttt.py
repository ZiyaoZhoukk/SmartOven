import re

response = {'id': 'chatcmpl-9hFlMEkoDqyedoDh4acnOcuq0CR1u', 'object': 'chat.completion', 'created': 1720095724, 'model': 'gpt-4o-2024-05-13', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'Based on the picture provided, it appears to be a whole raw chicken. Here is a likely estimation of the relevant properties based on average values for a raw chicken and the desired roasting plan in JSON format:\n\n```json\n{\n  "type of food": "whole chicken",\n  "heat_capacity": "2720",\n  "m": "1.5",\n  "water_content": "70",\n  "initial_temp": "4",\n  "A": "0.15",\n  "first_period": "1800",\n  "first_period_temp": "220",\n  "first_period_fan_speed": "2000",\n  "second_period": "1800",\n  "second_period_temp": "190",\n  "second_period_fan_speed": "1500"\n}\n```\n\n### Property Estimations:\n- "type of food": "whole chicken" (from the provided image)\n- "heat_capacity": 2720 J/(kg·°C) (approximate specific heat capacity of chicken meat)\n- "m": 1.5 kg (an average whole chicken weight)\n- "water_content": 70% (common in raw chicken meat)\n- "initial_temp": 4°C (average refrigerator temperature)\n- "A": 0.15 m² (estimated surface area of an average whole chicken)\n\n### Roasting Plan:\n1. **First Period**: 1800 seconds (30 minutes) at 220°C with a fan speed of 2000 RPM.\n    - This period will allow the chicken to start cooking and browning the skin.\n\n2. **Second Period**: 1800 seconds (30 minutes) at 190°C with a fan speed of 1500 RPM.\n    - This period will allow the chicken to cook through without drying out, maintaining moisture and ensuring it is cooked evenly.\n\nThis roasting plan is designed to ensure that the chicken is fully cooked while also achieving a golden-brown, crispy skin. Avoiding temperatures that are too high or roasting too long will help to prevent overcooking and drying out the chicken. Make sure to check the internal temperature of the chicken to ensure it has reached a safe level (at least 75°C) before consumption.'}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 1065, 'completion_tokens': 452, 'total_tokens': 1517}, 'system_fingerprint': 'fp_4008e3b719'}



if response.status_code == 200:
    response_data = response
    message_content = response_data['choices'][0]['message']['content']
    
    # 提取JSON内容
    json_start = message_content.find("{")
    json_end = message_content.rfind("}") + 1
    json_content = message_content[json_start:json_end]
    
    print("\n==========Generated Roasting Plan JSON============\n")
    print(json_content)
else:
    print(f"Request failed with status code {response.status_code}: {response.text}")