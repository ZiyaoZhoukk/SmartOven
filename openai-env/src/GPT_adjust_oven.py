import ovenControll
import call_GPT_for_text_analysis
import re
import json

def get_reference_data(eng,model_name,GPT_pic_recog_result_text):
    """use this parameter configuration to run the simulation and get a sequence of time-temperature text"""
    #跑完整的simulation，拿到对照曲线（理论只调用一次)
    time_temp,time_temp_list=ovenControll.reference_simulate(eng,model_name,GPT_pic_recog_result_text)
    return time_temp,time_temp_list

def combine_real_food_params_and_LLM_generated_grill_process(GPT_pic_recog_result_text,real_food_property_list):
    #生成烘烤字典：把GPT生成的烘烤过程保留，加上实际鸡的properties。real_param_text里面是"'3000','2','80','20','0.2'"
    param_dict=ovenControll.create_param_dict_from_LLM_answer(GPT_pic_recog_result_text)
    referenced_param_dict=param_dict
    keys=list(param_dict.keys())
    for i in range(1, 6):
        param_dict[keys[i]] = real_food_property_list[i - 1]
    return param_dict,referenced_param_dict

def apply_operation_to_state(control_data_dict,state_dict):#operation是字典，只有"fan_speed"和"heat_resistor_temp"
    state_dict["heat_resistor_temp"]=control_data_dict["heat_resistor_temp"]
    state_dict["fan_speed"]=control_data_dict["fan_speed"]
    return state_dict

def real_grill_process_one_minute(eng,model_name,state_dict):
    """run one minute sim with given state, record the end state, get the time-temp data"""
    #只跑一分钟（用来模拟真实烤制情形），记录状态，保存数据
    state_after_sim=ovenControll.real_simulate_one_minute(eng,model_name,state_dict)
    return state_after_sim

def call_GPT_for_assistance(current_temperature_list,reference_temperature_list,referenced_param_dict,state_dict,reference_delete_index):
    # 查找当前时间和最大时间
    max_time=len(reference_temperature_list)
    current_time=len(current_temperature_list)
    current_time_in_seconds=(current_time+reference_delete_index+1)*60
    # 特殊情况，不生成control，延续上一分钟的烤箱设置
    stable_control_dict=json.loads("""{"oven_temperature": "NO CHANGE","fan_speed": "NO CHANGE"}""")#匹配错误就返回这个
    if max_time<current_time:
        temperature_deviation_exist=False
    else:
        temperature_deviation_exist=True
        
    if temperature_deviation_exist==True:
        # get food type
        text_food_type=str(referenced_param_dict["type of food"])
        # get temp deviation
        current_temperature=float(current_temperature_list[-1])
        reference_temperature=reference_temperature_list[len(current_temperature_list)-1]
        temperature_deviation=str(round(current_temperature-reference_temperature,1))
        if current_temperature-reference_temperature>0.01:
            temperature_deviation="+"+temperature_deviation
        # get last minute temperature deviation
        current_temperature_last_minute=float(current_temperature_list[-1])
        reference_temperature_last_minute=reference_temperature_list[len(current_temperature_list)-2]
        temperature_deviation_last_minute=str(round(current_temperature_last_minute-reference_temperature_last_minute,1))
        if current_temperature_last_minute-reference_temperature_last_minute>0.01:
            temperature_deviation_last_minute="+"+temperature_deviation_last_minute
        # oven setting old
        if 0 <= current_time_in_seconds <= int(referenced_param_dict['first_period']):
            period = "first_period"
            period_temp = referenced_param_dict['first_period_temp']
            period_fan_speed = referenced_param_dict['first_period_fan_speed']
        elif int(referenced_param_dict['first_period']) < current_time_in_seconds <= int(referenced_param_dict['first_period']) + int(referenced_param_dict['second_period']):
            period = "second_period"
            period_temp = referenced_param_dict['second_period_temp']
            period_fan_speed = referenced_param_dict['second_period_fan_speed']
        else:
            period = None
            period_temp = None
            period_fan_speed = None   
        #oven setting new
        oven_temperature=str(state_dict["heat_resistor_temp"])
        fan_speed=str(state_dict["fan_speed"]) 
        print(f"---AFTER minute baking, using current oven settings---{oven_temperature}, {fan_speed}")
        prompt=f"""You are an AI designed to monitor and optimise the baking process in an oven. Your task is to generate the most suitable oven settings (oven temperature and fan speed) for the moment by referring to the standard curve. You need to follow the information that I provide and follow the steps that I lay out for you step by step to complete the task.

    Information:
    1. The type of food is: {text_food_type}

    2. Difference between the current food temperature curve and the standard curve:
    Current Temperature Deviation: {temperature_deviation} degrees Celsius
    Last Minute Temperature Deviation: {temperature_deviation_last_minute} degrees Celsius
    Note: Negative deviation represents that the current food temperature is lower than standard, Positive deviation represents that the current food temperature is higher than standard.

    3. Standard Curve Oven Settings:
    Temperature: {period_temp} degrees Celsius
    fan_speed: {period_fan_speed} r/min

    4. Current Oven Settings:
    Temperature: {oven_temperature} degrees Celsius
    fan_speed: {fan_speed} r/min


    Steps:
    1. Food Type Consideration:
    Pay attention to the type of food. Does this type of food often exhibit individual differences (such as size, water content, specific heat capacity)? If significant individual differences are possible, the temperature deviation may be influenced by both the individual differences and the oven settings.

    2. Evaluate Current Temperature Deviation:
    Evaluate the current temperature difference. Is the current temperature difference large or small for baking this type of food? If it is large, improper oven settings are likely the cause, and significant adjustments to the oven parameters are necessary. If the difference is small, it may be due to the food's inherent characteristics, but small adjustments to the oven parameters can still eliminate the deviation. 
    Additionally, if the temperature difference shows that the current temperature is higher than the standard, it is advisable to lower the oven temperature, and vice versa.

    3. Observe Deviation Trend:
    To observe the deviation trend, compare the current temperature deviation and the last minute temperature deviation. If the deviation is decreasing, it indicates that the current oven settings are adequate, and only minor adjustments are needed. If the deviation is increasing, more substantial adjustments to the oven settings are required. If the deviation is decreasing then increasing (for example from -1 to +1), that suggests that the last change of oven setting is too much.

    4. Compare Oven Settings to Standard Curve:
    Compare the current oven settings to the standard curve (considering whether you previously determined to raise or lower the temperature). If the current temperature setting is higher than the standard temperature setting but you intended to continue increasing the temperature, you might only raise the temperature slightly to avoid significant impacts.

    5. Specify New Oven Settings:
    Specify the new values for oven temperature and fan speed. If no changes are needed, indicate NO CHANGE. 
    Format your output as a JSON file with the [CONTROL][/CONTROL] tags with the following requirements:
    1. All keys and values must be enclosed in double quotes.
    2. Do not include any comments, additional explanations, or extra content.
    3. Produce only the pure JSON data structure.
    Example:
    [CONTROL]
    {{
    "oven_temperature": "<new_temperature_or_NO_CHANGE>",
    "fan_speed": "<new_fan_speed_or_NO_CHANGE>"
    }}
    [/CONTROL]
    """
        prompt=["You are an AI designed to monitor and optimise the baking process in an oven.",prompt]
        print(f"\nThis is the combined prompt:\n{prompt[1]}\n========\n")
        response=call_GPT_for_text_analysis.call(prompt)
        print("\n---------Asking GPT for asistence to optimise the baking process----------")
        print(f"This is the raw response: \n======\n{response}\n========\n")

        pattern = r'\[CONTROL\](.*?)\[/CONTROL\]'#匹配control标签中间的内容（不包括标签本身）
        match = re.search(pattern, response,re.DOTALL)
        if match:
            control_data = match.group(1)
            print(f"first match: {control_data}")
            json_match=re.search(r'\{.*?\}', control_data, re.DOTALL)
            if json_match:
                control_json=json_match.group(0)
                control_dict=json.loads(control_json)
                print(f"second match successful, control_json: {control_json}")
            else:
                print("ERROR OCURRED: FAILED TO 2. MATCH CONTROL IN RESPONSE.")
                control_dict=stable_control_dict
        else:
            control_dict=stable_control_dict
            print("ERROR OCURRED: FAILED TO 1. MATCH CONTROL IN RESPONSE.")
        return control_dict
    else:
        return stable_control_dict

def call_LLM_generate_controll_instruction(reason_text,current_time_temp_list,text_referenced_data,referenced_param_dict,state_dict,preference):
    #只需要知道下一分钟是什么参数烤,还要返回可能造成的影响（时间上）
    # 【prompt里面要约定用控制符[CONTROL]...[/CONTROL]以及json的格式来表示操作,用[CONSEQUENSE]...[CONSEQUENCE]来表示预测的
    text_food_type=str(referenced_param_dict["type of food"])
    
    items=list(referenced_param_dict.items())
    sub_items = items[6:]
    text_referenced_oven_setting = str({key: str(value) for key, value in sub_items})
    
    text_inital_temp=str(state_dict["initial_temp"])
    
    text_baking_time=str(len(current_time_temp_list)-1)
    
    time = 0
    result_list = []
    for temp in current_time_temp_list:
        result_list.append(f"[{time}]:[{temp}]")
        time += 60
    text_time_temp = ', '.join(result_list)
    
    if len(state_dict)>9:
        text_current_oven_setting='Temperature: '+str(state_dict["first_period_temp"])+' degrees Celsius\nFan Speed: '+str(state_dict["first_period_fan_speed"])+' r/min'
    else:
        text_current_oven_setting='Temperature: '+str(state_dict["heat_resistor_temp"])+' degrees Celsius\nFan Speed: '+str(state_dict["fan_speed"])+' r/min'
    
    prompt_second_part=f"""You are an AI assistant designed to optimize the baking process of an oven by adjusting the current oven temperature and fan speed. Your task is to make changes based on the following context:

Context:
1. Background:
Some of the properties of the food being baked were incorrectly estimated. Therefore, it is crucial to adjust the oven settings to achieve better baking results. Here are the information about the wrong properties: {reason_text} 

2. Type of Food: {text_food_type}

3. Referenced Data:
{text_referenced_data}
Note: This is a time-temperature sequence representing the common temperature progression of the food being baked. The data is recorded every 60 seconds. Time units are in seconds, temperature units are in degrees Celsius. Pay attention to the rate of temperature rise, this may imply that the best way to cook this food is to let its temperature rise at this rate.

4. Oven Setting of the Referenced Data: 
{text_referenced_oven_setting}
Note: Time units are in seconds. Temperature is in degrees Celsius. Fan speed is in rotations per minute (r/min).

5. Current Temperature Sequence During Baking:
{text_time_temp}
Note: This sequence represents the food's temperature at each minute of baking so far. The initial temperature is {text_inital_temp}, now the baking process has been {text_baking_time} min. The sequence is incomplete as the baking process is still ongoing.

6. Current Oven Settings:
{text_current_oven_setting}

7. User Preference:
{preference}

Your Task:
Based on the above data, determine the new oven temperature and fan speed settings to better align with the optimal baking conditions.
Present the new settings in JSON format within the [CONTROL][/CONTROL] tags.
Clearly state the consequences of the adjustments within the [CONSEQUENCE][/CONSEQUENCE] tags.(For example, the consequence can be that the adjustment may change the time of the whole baking time.)
Estimate the time to finish baking in minutes between the curly brackets within the [TIMETOFINISH][/TIMETOFINISH] tags. 

Output Format (Do not output anything other than the following):
[CONTROL]
{{
  "oven_temp": <new_temperature>,
  "fan_speed": <new_fan_speed>
}}
[/CONTROL]

[CONSEQUENCE]
<what you think will happen>
[/CONSEQUENCE]

[TIMETOFINISH]
<estimated time to finish baking in minutes>
[/TIMETOFINISH]

"""
    prompt=('You are an AI trained to adjust the oven temperature and fan speed to make the baking process better!',prompt_second_part)
    print(f"\n---------------gernerating control data and potential consequences---------------\n")
    response=call_GPT_for_text_analysis.call(prompt)
    print(f"This is the raw response about the operation and consequences: \n=======\n{response}\n=======\n")

    # 提取 CONTROL 内容【json,温度=xx，风扇=xx】
    control_pattern = r'\[CONTROL\](.*?)\[/CONTROL\]'
    match = re.search(control_pattern, response, re.DOTALL)  
    if match:
        control_content = match.group(1)
        control_data = json.loads(control_content)
    else:
        print("ERROR OCCURED: FAILED TO MATCH CONTROL INFOS")
        control_data = {}
        control_data={["oven_temp"]:"220",["fan_speed"]:"1500"}
            
    
    # 提取 CONSEQUENCE 内容
    consequence_pattern = r'\[CONSEQUENCE\](.*?)\[/CONSEQUENCE\]'        
    match = re.search(consequence_pattern, response,re.DOTALL)
    if match:
        consequence_content = match.group(1)   
    else:
        print("ERROR OCCURED: FAILED TO MATCH CONSEQUENCES INFOS")
        consequence_content='NO CONSEQUENCE'       
        
    # 提取 TIMETOFINISH 内容
    time_pattern = r'\[TIMETOFINISH\](.*?)\[/TIMETOFINISH\]'        
    match = re.search(time_pattern, response,re.DOTALL)
    if match:
        time_content = match.group(1)   
    else:
        print("ERROR OCCURED: FAILED TO MATCH ESTIMATED TIME INFOS")
        time_content='NaaN'     
    return control_data,consequence_content,time_content

def apply_control_data_to_state(control_data_dict,state_dict):
    control_data_dict["oven_temperature"] = str(control_data_dict["oven_temperature"])
    control_data_dict["fan_speed"]=str(control_data_dict["fan_speed"])
    
    if (control_data_dict["oven_temperature"]).isdigit():
        state_dict["heat_resistor_temp"]=str(control_data_dict["oven_temperature"])
    if (control_data_dict["fan_speed"]).isdigit():
        state_dict["fan_speed"]=str(control_data_dict["fan_speed"])
    new_state_dict=state_dict
    return new_state_dict

def oven_setting_is_modified(state_dict,control_data_list):#old setting & new setting
    if state_dict["heat_resistor_temp"]==control_data_list["oven_temp"] and state_dict["fan_speed"]==control_data_list["fan_speed"]:
        return False
    else:
        return True

def send_consequences(consequences,state_dict,control_data_list):
    if oven_setting_is_modified(state_dict,control_data_list):
        print(f"\nAttention: the grill process will be affected as following:\n{consequences}\n")
        
def is_finished(current_time_temp_list,referenced_data,time):
    #判断是否已经完成
    current_temp=float(current_time_temp_list[-1])    
    match = re.findall(r'\[(\d+\.?\d*)\]', referenced_data)
    target_temp = float(match[-1]) if match else 0
    if current_temp-target_temp>-0.4:
        isFinished=True
        print(f"Grill Process is finished. Total time: ----\"{time}\"---- minutes.")
    else:
        isFinished=False
        print(f"Grill process should still go on. Current time: ----{time}---- minutes.")
    return isFinished

def collect_data(data_list,state,real_param_dict):
    if data_list==[]:
        data_list.append(real_param_dict["initial_temp"])
    data_list.append(state["food_temp"])
    return data_list

def curve_panning(current_temp_list,reference_data_list):#平移reference data，让他和current曲线初始温度相同
    last_value = current_temp_list[-1]
    # 找到第二个列表中与last_value相等的值的位置（相减<0.01）
    index = None
    for i, value in enumerate(reference_data_list):
        if abs(round(value) - round(float(last_value))) < 0.01:
            index = i
            break
        else: index=0
    # 如果找到了匹配的值，将其之前的数据清除
    if index is not None:
        reference_data_list = reference_data_list[index:]
        return True, reference_data_list, index
    else:
        return False, reference_data_list, index


def main():
    model_name = 'OvenSim'
    matlab_file = 'ovenSimConfig.m'
    time=0 #To get the time that the baking process has started
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
    real_food_properties_list='3000','2','80','20','0.2'#假设真实烤鸡的properties是这样
    current_temperature_list=[]
    real_param_dict,referenced_param_dict=combine_real_food_params_and_LLM_generated_grill_process(Exm_reference_grill_instruction,real_food_properties_list)
    print (f"This is the param_dict combining REAL food properties and GPT_generated grill setting:\n{real_param_dict}\n")
    
    #初始化模型
    eng=ovenControll.matlab_initialization(model_name,matlab_file)
    #拿到参考温度曲线
    referenced_data,referenced_data_list=get_reference_data(eng,model_name,Exm_reference_grill_instruction)
    print(f"This is the referenced data: {referenced_data_list}")
    #开始真实烘烤（第一分钟）
    state_dict=real_grill_process_one_minute(eng,model_name,real_param_dict)
    time+=1
    #收集数据
    current_temperature_list=collect_data(current_temperature_list,state_dict,real_param_dict)
    print(f"The current temperature list until {time} minutes: {current_temperature_list}")
    # curve panning
    panning_suceessful,referenced_data_list, delete_index=curve_panning(current_temperature_list,referenced_data_list)
    print(f"This is the panning curve: {referenced_data_list}")
    while panning_suceessful==False:
        state_dict=real_grill_process_one_minute(eng,model_name,real_param_dict)
        time+=1
        #收集数据
        current_temperature_list=collect_data(current_temperature_list,state_dict,real_param_dict)
        panning_suceessful,referenced_data_list, delete_index=curve_panning(current_temperature_list,referenced_data_list)
    # 从第二分钟开始循环烤制过程
    while True:
        if not is_finished(current_temperature_list, referenced_data,time):
            control_data=call_GPT_for_assistance(current_temperature_list,referenced_data_list,referenced_param_dict,state_dict,delete_index)
            print(f"changes generated by GPT: {control_data}")
            state_dict=apply_control_data_to_state(control_data,state_dict)
            print(f"state after applying changes: {state_dict}")
            state_dict=real_grill_process_one_minute(eng,model_name,state_dict)
            time+=1
            #收集数据
            current_temperature_list=collect_data(current_temperature_list,state_dict,real_param_dict)
            print(f"current temperature list: {current_temperature_list}")
        else:
            #烤制过程结束，打印结果，关闭引擎
            print(f"This is the final temperature data: \n{current_temperature_list}")
            ovenControll.quit_matlab_engine(eng)
            break
        

if __name__ == "__main__":
    main()
    
#     control_dict="""
# {
#   "oven_temperature": "NO CHANGE",
#   "fan_speed": "NO CHANGE"
# }
# """
#     state_dict={"heat_resistor_temp":"220","fan_speed":"1400"}
#     state_dict=apply_control_data_to_state(control_dict,state_dict)
#     print(state_dict)

#     control_data="""{
#     "oven_temperature": 222, 
#     "fan_speed": "NO_CHANGE"
# }"""
#     json_match=re.search(r'\{.*?\}', control_data, re.DOTALL)
#     if json_match:
#         control_json=json_match.group(0)
#         control_dict=json.loads(control_json)
#         print(f"second match successful, control_json: {control_json}")
            
    

