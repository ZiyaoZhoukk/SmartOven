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
    
    
prompt = (
    """You are an AI designed to monitor and optimise the baking process in an oven. 
    Your task is to evaluate whether the current oven settings—temperature and fan speed—
    are appropriate for the type of food being baked. You need to consider that the default 
    assumptions about the food's properties (initial temperature, weight, heat capacity, surface area, 
    water content) might not be accurate and adjustments might be necessary during the baking process.

    Here are the key parameters for your assessment:
    1. Type of Food: """ + text_food_type + """
    2. Referenced Data: This is a time-temperature sequence representing the common temperature progression 
    of the food being baked:\n""" + text_referenced_data + """
    Note: The data is recorded every 60 seconds. Time units are in seconds, temperature units are in degrees Celsius. 
    Pay attention to the rate of temperature rise, this may imply that the best way to cook this food is to let its 
    temperature rise in this rate. 

    3. Referenced Oven Setting:\n""" + text_referenced_oven_setting + """
    Note: Time units are in seconds. Temperature is in degrees Celsius. Fan speed is in rotations per minute (r/min).

    4. Current Temperature Sequence During Baking: This sequence represents the food's temperature at each minute 
    of baking so far.(The initial temperature is """ + text_inital_temp + """, now the baking process has been 
    """ + text_baking_time + """ min.)\n""" + text_time_temp + """
    Note: The sequence is incomplete as the baking process is still ongoing. 

    5. Current Oven Settings:\n""" + text_current_oven_setting + """
    Decision Required: Based on the comparison between the current temperature sequence and the referenced data, 
    and considering the current oven settings, determine whether the current settings are appropriate.
    Provide your final decision in the following format:
    {yes} if the current settings are acceptable and no adjustments are needed.
    {no} if the current settings are not acceptable and adjustments are necessary.

    Additionally, if your decision was no, specify which of the food properties (initial temperature, weight, heat capacity, 
    surface area, water content) were incorrectly estimated to cause the discrepancy. Provide them in the following format:
    [REASON]your answer here[/REASON]
    If your decision was yes, even if you think some food properties were estimated incorrectly, do not give the "reason" 
    or mention anything.
    Limit your output to FIVE LINES."""
)

print(f"\nThis is the combined prompt:\n{prompt}\n=========\n")
response = call_GPT_for_text_analysis.call(prompt)
