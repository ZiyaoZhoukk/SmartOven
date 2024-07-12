import ovenControll
import call_GPT_for_text_analysis
import re
import json

def get_reference_data(eng,model_name,LLM_generated_text):
    """use this parameter configuration to run the simulation and get a sequence of time-temperature text"""
    #跑完整的simulation，拿到对照曲线（理论只调用一次)
    time_temp=ovenControll.reference_simulate(eng,model_name,LLM_generated_text)
    return time_temp

def combine_real_food_params_and_LLM_generated_grill_process(LLM_generated_text,real_param_list):
    #生成烘烤字典：把GPT生成的烘烤过程保留，加上实际鸡的properties。real_param_text里面是"'3000','2','80','20','0.2'"
    param_dict=ovenControll.create_param_dict_from_LLM_answer(LLM_generated_text)
    referenced_param_dict=param_dict
    keys=list(param_dict.keys())
    for i in range(1, 6):
        param_dict[keys[i]] = real_param_list[i - 1]
    return param_dict,referenced_param_dict

def combine_operation_with_state(operation,state):#operation是字典，只有"fan_speed"和"heat_resistor_temp"
    state["heat_resistor_temp"]=operation["heat_resistor_temp"]
    state["fan_speed"]=operation["fan_speed"]
    return state

def real_grill_process_one_minute(eng,model_name,state_param):
    """run one minute sim with given state, record the end state, get the time-temp data"""
    #只跑一分钟（用来模拟真实烤制情形），记录状态，保存数据
    state_after_sim=ovenControll.real_simulate_one_minute(eng,model_name,state_param)
    return state_after_sim

def call_LLM_is_negligible_error_and_give_reason(time_temp_data,text_referenced_data,referenced_grill_param,current_grill_param):
    # 【Prompt里面要约定用{}来表明yes or no】
    text_food_type=str(referenced_grill_param["type of food"])
    
    items=list(referenced_grill_param.items())
    sub_items = items[6:]
    text_referenced_oven_setting = str({key: str(value) for key, value in sub_items})
    
    text_inital_temp=str(current_grill_param["initial_temp"])
    
    text_baking_time=str(len(time_temp_data)-1)
    
    time = 0
    result_list = []
    for temp in time_temp_data:
        result_list.append(f"[{time}]:[{temp}]")
        time += 60
    text_time_temp = ', '.join(result_list)
    
    if len(current_grill_param)>9:
        text_current_oven_setting='Temperature: '+str(current_grill_param["first_period_temp"])+' degrees Celsius\nFan Speed: '+str(current_grill_param["first_period_fan_speed"])+' r/min'
    else:
        text_current_oven_setting='Temperature: '+str(current_grill_param["heat_resistor_temp"])+' degrees Celsius\nFan Speed: '+str(current_grill_param["fan_speed"])+' r/min'
    
    prompt_second_part = """You are an AI designed to monitor and optimise the baking process in an oven. Your task is to evaluate whether the current oven settings—temperature and fan speed—are appropriate for the type of food being baked. You need to consider that the default assumptions about the food's properties (initial temperature, weight, heat capacity, surface area, water content) might not be accurate and adjustments might be necessary during the baking process.
Here are the key parameters for your assessment:
1.Type of Food: """+text_food_type+"""\n\n2.Referenced Data: This is a time-temperature sequence representing the common temperature progression of the food being baked:\n"""+text_referenced_data+"""\nNote: The data is recorded every 60 seconds. Time units are in seconds, temperature units are in degrees Celsius. Pay attention to the rate of temperature rise, this may imply that the best way to cook this food is to let its temperature rise in this rate. 

3. Oven Setting of the Referenced Data: \n"""+text_referenced_oven_setting+"""\nNote: Time units are in seconds. Temperature is in degrees Celsius. Fan speed is in rotations per minute (r/min).

4. Current Temperature Sequence During Baking: This sequence represents the food's temperature at each minute of baking so far.(The initial temperature is """+text_inital_temp+""", now the baking process has been """+text_baking_time+""" min.)\n"""+text_time_temp+"""\nNote: The sequence is incomplete as the baking process is still ongoing. 

5. Current Oven Settings:\n"""+text_current_oven_setting+"""\nDecision Required: Based on the comparison between the current temperature sequence and the referenced data, and considering the current oven settings, determine whether the current settings are appropriate.
Provide your final decision in the following format:
{yes} if the current settings are acceptable and no adjustments are needed.
{no} if the current settings are not acceptable and adjustments are necessary.

Additionally, if your decision was no, specify which of the food properties (initial temperature, weight, heat capacity, surface area, water content) were incorrectly estimated to cause the discrepancy. Provide them in the following format:
[REASON]your answer here[/REASON]
If your decision was yes, even if you think some food properties were estimated incorrectly, do not give the "reason" or mention anything.
Limit your output to FIVE LINES."""
    prompt=("You are an AI designed to monitor and optimise the baking process in an oven.",prompt_second_part)
    print(f"\nThis is the combined prompt:\n{prompt[1]}\n========\n")
    response=call_GPT_for_text_analysis.call(prompt)
    print("\n---------error check...----------")
    print(f"This is the raw response about if the error is negligible: ======\n{response}'\n")
    #在response(格式就是字符串)中匹配yes or no并输出
    match = re.search(r'\{(yes|no)\}', response)  
    if match:
        result = match.group(1)
        if result == 'yes':
            print(f"No need to change temperature or fan speed")
            yesORno=True
        else: 
            yesORno=False
            print("!!!Need a change of temperature or fan speed")
            pattern = r'\[REASON\](.*?)\[/REASON\]'
            match = re.search(pattern, response)
            if match:
                reason = match.group(1)     
    print("\n")
    return yesORno,reason

# def call_LLM_find_reason(state,referenced_data):
#     #比热容，质量，含水量，初始温度，表面积：其中的某几个出了问题
#     #【prompt里面要约定用{}来表示原因】
#     prompt=''
#     response=call_GPT_for_text_analysis(prompt)
#     print(f"\This is the raw response about the reason: '{response}'\n")
#     #匹配原因并输出
#     pattern = r'\{(.*?)\}'
#     match = re.search(pattern, response)
#     if match:
#         reason = match.group(1)       
#     else:
#         print("The response does not contain any reason.")
#     print(f"\nThis is the extraced reason: '{reason}'\n")
#     return reason

def call_LLM_generate_controll_instruction(reason,state,referenced_data):
    #只需要知道下一分钟是什么参数烤,还要返回可能造成的影响（时间上）
    # 【prompt里面要约定用控制符[CONTROL]...[/CONTROL]以及json的格式来表示操作,用[CONSEQUENSE]...[CONSEQUENCE]来表示预测的
    prompt=reason
    response=call_GPT_for_text_analysis(prompt)
    print(f"\This is the raw response about the reason: '{response}'\n")

    # 提取 CONTROL 内容【json,温度=xx，风扇=xx】
    control_pattern = r'\[CONTROL\](.*?)\[/CONTROL\]'
    control_matches = re.findall(control_pattern, response, re.DOTALL)
    
    for control_content in control_matches:
        try:
            control_data = json.loads(control_content)
            # 在这里执行你需要的操作
            print("Processing CONTROL content:")
            print(control_data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            
    
    # 提取 CONSEQUENCE 内容
    consequence_pattern = r'\[CONSEQUENCE\](.*?)\[/CONSEQUENCE\]'
    consequence_matches = re.findall(consequence_pattern,response, re.DOTALL)
    
    for consequence_content in consequence_matches:
        # 在这里执行你需要的操作
        print("Processing CONSEQUENCE content:")
        print(consequence_content)
        
    return control_data,consequence_content

def send_consequences(consequences):
    print(f"\nAttention: the grill process will be changed in folowing:\n{consequences}\n")
    return

def call_LLM_is_finished(time_temp_data,referenced_data):
    #判断是否已经完成
    #根据的数据：reference_data, 现在总共烤的time_temp, 烤的食物种类，用户的个人偏好
    #【需要在Prompt里面约定在{}里面放入yes or no】
    prompt=''
    response= call_GPT_for_text_analysis.call(prompt)
    print(f"\nThis is the raw response of telling if the food is ready: '{response}'\n")
    #匹配
    match = re.search(r'\{(yes|no)\}', response)  
    if match:
        result = match.group(1)
        if result == 'yes':
            isFinished=True
        else: 
            isFinished=False
    print(f"\n\This is the extracted answer from the response: '{result}'\n")
    return isFinished

def collect_data(temperature_data,state,real_param_dict):
    if temperature_data==[]:
        temperature_data.append(real_param_dict["initial_temp"])
    temperature_data.append(state["food_temp"])
    return temperature_data




def main():
    model_name = 'OvenSim'
    matlab_file = 'ovenSimConfig.m'
    time=0
    #省略识图，直接获得结果：
    Exm_reference_grill_instruction = """
    Based on the provided image, the food item appears to be a whole chicken. Here's the detailed analysis and a roasting plan.

    Food Properties Analysis
    Type of Food: Whole chicken
    Heat Capacity: The specific heat capacity of chicken is typically around 2.5 kJ/kg°C.
    Weight (m): Based on the image, an average whole chicken weighs about 1.5 kg.
    Water Content: Chicken generally has a water content of around 70%.
    Initial Temperature (initial_temp): Assuming the chicken has been refrigerated, the initial temperature is approximately 4°C.
    Heat Surface Area (A): The surface area for a whole chicken is around 0.1 m².
    Roasting Plan
    To achieve a well-cooked, juicy roast chicken, the roasting process should be divided into two periods: an initial high-heat period to crisp the skin followed by a lower heat period to cook the meat through without drying it out.

    First Period

    Duration: 20 minutes (1200 seconds)
    Temperature: 220°C
    Fan Speed: 2500 RPM (high speed for even heat distribution)
    Second Period

    Duration: 45 minutes (2700 seconds)
    Temperature: 180°C
    Fan Speed: 1500 RPM (moderate speed)
    JSON Roasting Plan
    Here is the JSON file for the roasting plan:

    json
    copy code
    {
    "type of food": "chicken",
    "heat_capacity": "2720",
    "m": "1.5",
    "water_content": "74",
    "initial_temp": "4",
    "A": "0.14",
    "first_period": "1800",
    "first_period_temp": "220",
    "first_period_fan_speed": "1200",
    "second_period": "3600",
    "second_period_temp": "180",
    "second_period_fan_speed": "1000"
    }
    This plan ensures that the chicken is cooked thoroughly with a crispy skin and juicy interior. Adjustments can be made based on specific oven performance and preferences.
    """
    real_food_properties='3000','2','80','20','0.2'
    food_temperature_data=[]
    data=[]
    referenced_param_dict,real_param_dict=combine_real_food_params_and_LLM_generated_grill_process(Exm_reference_grill_instruction,real_food_properties)
    print (f"This is the param_dict combining REAL food properties and GPT_generated grill setting:\n{real_param_dict}\n")
    
    eng=ovenControll.matlab_initialization(model_name,matlab_file)
    referenced_data=get_reference_data(eng,model_name,Exm_reference_grill_instruction)
    state=real_grill_process_one_minute(eng,model_name,real_param_dict)#第一分钟烘烤
    data=collect_data(food_temperature_data,state)
    #循环烘烤--------等Prompt全部写好，要重新写
    while True:
        if time<1:
            is_negligible,reason=call_LLM_is_negligible_error_and_give_reason(data,referenced_data,referenced_param_dict,real_param_dict)
        else:
            is_negligible,reason=call_LLM_is_negligible_error_and_give_reason(data,referenced_data,referenced_param_dict,state)
        if not call_LLM_is_finished(data,referenced_data):
            if not is_negligible:
                control_data,consequences=call_LLM_generate_controll_instruction(reason,state,referenced_data)
                send_consequences(consequences)     
                state=combine_operation_with_state(control_data,state)
                state=real_grill_process_one_minute(eng,model_name,state)
                data=collect_data(food_temperature_data,state)
            else:
                state=real_grill_process_one_minute(eng,model_name,state) 
                data=collect_data(food_temperature_data,state)
            time += 1
            print(f"\n---{time}minutes baking process has past---\n")
        else:
            ovenControll.quit_matlab_engine(eng)
            break
    print(f"This is the final data:\n=========={data}\n=======\n")
        
        


if __name__ == "__main__":
    #测试call_LLM_is_negligible_error_and_give_reason
    model_name = 'OvenSim'
    matlab_file = 'ovenSimConfig.m'
    time=0
    #省略识图，直接获得结果：
    Exm_reference_grill_instruction = """
    Based on the provided image, the food item appears to be a whole chicken. Here's the detailed analysis and a roasting plan.

    Food Properties Analysis
    Type of Food: Whole chicken
    Heat Capacity: The specific heat capacity of chicken is typically around 2.5 kJ/kg°C.
    Weight (m): Based on the image, an average whole chicken weighs about 1.5 kg.
    Water Content: Chicken generally has a water content of around 70%.
    Initial Temperature (initial_temp): Assuming the chicken has been refrigerated, the initial temperature is approximately 4°C.
    Heat Surface Area (A): The surface area for a whole chicken is around 0.1 m².
    Roasting Plan
    To achieve a well-cooked, juicy roast chicken, the roasting process should be divided into two periods: an initial high-heat period to crisp the skin followed by a lower heat period to cook the meat through without drying it out.

    First Period

    Duration: 20 minutes (1200 seconds)
    Temperature: 220°C
    Fan Speed: 2500 RPM (high speed for even heat distribution)
    Second Period

    Duration: 45 minutes (2700 seconds)
    Temperature: 180°C
    Fan Speed: 1500 RPM (moderate speed)
    JSON Roasting Plan
    Here is the JSON file for the roasting plan:

    json
    copy code
    {
    "type of food": "chicken",
    "heat_capacity": "2720",
    "m": "1.5",
    "water_content": "74",
    "initial_temp": "4",
    "A": "0.14",
    "first_period": "1800",
    "first_period_temp": "220",
    "first_period_fan_speed": "1200",
    "second_period": "3600",
    "second_period_temp": "180",
    "second_period_fan_speed": "1000"
    }
    This plan ensures that the chicken is cooked thoroughly with a crispy skin and juicy interior. Adjustments can be made based on specific oven performance and preferences.
    """
    real_food_properties='3000','2','80','20','0.2'
    food_temperature_data=[]
    data=[]
    referenced_param_dict,real_param_dict=combine_real_food_params_and_LLM_generated_grill_process(Exm_reference_grill_instruction,real_food_properties)
    print (f"This is the param_dict combining REAL food properties and GPT_generated grill setting:\n{real_param_dict}\n")
    
    eng=ovenControll.matlab_initialization(model_name,matlab_file)
    referenced_data=get_reference_data(eng,model_name,Exm_reference_grill_instruction)
    state=real_grill_process_one_minute(eng,model_name,real_param_dict)#第一分钟烘烤
    data=collect_data(food_temperature_data,state,real_param_dict)
    is_negligible,reason=call_LLM_is_negligible_error_and_give_reason(data,referenced_data,referenced_param_dict,real_param_dict)
    # if not is_negligible:
    #     control_data,consequences=call_LLM_generate_controll_instruction(reason,state,referenced_data)
    #     send_consequences(consequences)     
    #     state=combine_operation_with_state(control_data,state)
    #     state=real_grill_process_one_minute(eng,model_name,state)
    #     data=collect_data(food_temperature_data,state)
    # else:
    #     state=real_grill_process_one_minute(eng,model_name,state) 
    #     data=collect_data(food_temperature_data,state)
    # is_negligible,reason=call_LLM_is_negligible_error_and_give_reason(data,referenced_data,referenced_param_dict,state)
    # if not is_negligible:
    #     control_data,consequences=call_LLM_generate_controll_instruction(reason,state,referenced_data)
    #     send_consequences(consequences)     
    #     state=combine_operation_with_state(control_data,state)
    #     state=real_grill_process_one_minute(eng,model_name,state)
    #     data=collect_data(food_temperature_data,state)
    # else:
    #     state=real_grill_process_one_minute(eng,model_name,state) 
    #     data=collect_data(food_temperature_data,state)
    # ovenControll.quit_matlab_engine(eng)
    # print(f"This is the final data:\n=========={data}\n=======\n")
    

