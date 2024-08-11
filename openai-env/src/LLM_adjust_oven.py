import ovenControll
import call_GPT_for_text_analysis
import re
import json

def get_reference_data(eng,model_name,GPT_pic_recog_result_text):
    """use this parameter configuration to run the simulation and get a sequence of time-temperature text"""
    #跑完整的simulation，拿到对照曲线（理论只调用一次)
    time_temp=ovenControll.reference_simulate(eng,model_name,GPT_pic_recog_result_text)
    return time_temp

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

def call_LLM_is_negligible_error_and_give_reason(current_time_temp_list,text_referenced_data,referenced_param_dict,state_dict,preference):
    # 【Prompt里面要约定用{}来表明yes or no】
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
    
    prompt_second_part = """You are an AI designed to monitor and optimise the baking process in an oven. Your task is to evaluate whether the current oven settings—temperature and fan speed—are appropriate for the type of food being baked. You need to consider that the default assumptions about the food's properties (initial temperature, weight, heat capacity, surface area, water content) might not be accurate and adjustments might be necessary during the baking process.
Here are the key parameters for your assessment:
1.Type of Food: """+text_food_type+"""\n\n2.Referenced Data: This is a time-temperature sequence representing the common temperature progression of the food being baked:\n"""+text_referenced_data+"""\nNote: The data is recorded every 60 seconds. Time units are in seconds, temperature units are in degrees Celsius. Pay attention to the rate of temperature rise, this may imply that the best way to cook this food is to let its temperature rise in this rate. 

3. Oven Setting of the Referenced Data: \n"""+text_referenced_oven_setting+"""\nNote: Time units are in seconds. Temperature is in degrees Celsius. Fan speed is in rotations per minute (r/min).

4. Current Temperature Sequence During Baking: This sequence represents the food's temperature at each minute of baking so far.(The initial temperature is """+text_inital_temp+""", now the baking process has been """+text_baking_time+""" min.)\n"""+text_time_temp+"""\nNote: The sequence is incomplete as the baking process is still ongoing. 

5. Current Oven Settings:\n"""+text_current_oven_setting+"""\nDecision Required: Based on the comparison between the current temperature sequence and the referenced data, and considering the current oven settings, determine whether the current settings are appropriate.

6. User preference:\n"""+preference+"""\n
Provide your final decision in the following format:

Your Task:
1. Based on the comparison between the current temperature sequence and the referenced data, and considering the current oven settings, determine whether the current settings are appropriate.
Provide your final decision in the following format:
{yes} if the current settings are acceptable and no adjustments are needed.
{no} if the current settings are not acceptable and adjustments are necessary.

2. If your decision was no, specify which of the food properties (initial temperature, weight, heat capacity, surface area, water content) were incorrectly estimated to cause the discrepancy. Provide them within the [REASON][/REASON] tags.

Output Format (Do not output anything other than the following):
[DECISION]
<your decision>
[/DECISION]

[REASON]
<which of the food properties that you think are incorrectly estimated>
[/REASON]
"""

    prompt=("You are an AI designed to monitor and optimise the baking process in an oven.",prompt_second_part)
    # print(f"\nThis is the combined prompt:\n{prompt[1]}\n========\n")
    response=call_GPT_for_text_analysis.call(prompt)
    print("\n---------error check----------")
    print(f"This is the raw response about if the error is negligible: \n======\n{response}\n========\n")
    #在response(格式就是字符串)中匹配yes or no并输出
    match = re.search(r'\[DECISION\].*?\b(yes|no)\b.*?\[/DECISION\]', response, re.IGNORECASE | re.DOTALL) 
    if match:
        result = match.group(1).strip()
    else:
        result='yes'
        print("ERROR OCURRED: FAILED TO MATCH YES OR NO IN RESPONSE.")
    if result == 'yes':
        yesORno=True
        print(f"CHECK RESULT: No need to change temperature or fan speed")
        reason=''
    else: 
        yesORno=False
        print("CHECK RESULT: !!!Need a change of temperature or fan speed")
        pattern = r'\[REASON\](.*?)\[/REASON\]'
        match = re.search(pattern, response,re.DOTALL)
        if match:
            reason = match.group(1)
        else:
            reason=''
            print("ERROR OCURRED: FAILED TO MATCH REASON IN RESPONSE.")
    return yesORno,reason

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
    state_dict["heat_resistor_temp"]=str(control_data_dict["oven_temp"])
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
            is_negligible,reason=call_LLM_is_negligible_error_and_give_reason(data,referenced_data,referenced_param_dict,real_param_dict,preference)
        else:
            is_negligible,reason=call_LLM_is_negligible_error_and_give_reason(data,referenced_data,referenced_param_dict,state,preference)
        if not is_finished(data,referenced_data):
            if not is_negligible:
                control_data,consequences=call_LLM_generate_controll_instruction(reason,state,referenced_data,preference)
                send_consequences(consequences)     
                state=apply_operation_to_state(control_data,state)
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
    ##版本有些过时，generate control data应该返回了第三个值AKA time left
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
    current_time_temp_list=[]
    preference=""
    real_param_dict,referenced_param_dict=combine_real_food_params_and_LLM_generated_grill_process(Exm_reference_grill_instruction,real_food_properties_list)
    print (f"This is the param_dict combining REAL food properties and GPT_generated grill setting:\n{real_param_dict}\n")
    
    #初始化模型
    eng=ovenControll.matlab_initialization(model_name,matlab_file)
    #拿到参考温度曲线
    referenced_data=get_reference_data(eng,model_name,Exm_reference_grill_instruction)
    #开始真实烘烤（第一分钟）
    state_dict=real_grill_process_one_minute(eng,model_name,real_param_dict)
    time+=1
    #收集数据
    current_time_temp_list=collect_data(current_time_temp_list,state_dict,real_param_dict)
    #从第二分钟开始循环烤制过程
    while True:
        if not is_finished(current_time_temp_list, referenced_data,time):
            is_negligible,reason=call_LLM_is_negligible_error_and_give_reason(current_time_temp_list,referenced_data,referenced_param_dict,real_param_dict,preference)
            if not is_negligible:
                #发生偏移，生成操作和后果
                control_data_dict,consequences=call_LLM_generate_controll_instruction(reason,current_time_temp_list,referenced_data,referenced_param_dict,real_param_dict,preference)
                send_consequences(consequences,state_dict,control_data_dict)    
                state_dict=apply_control_data_to_state(control_data_dict,state_dict)
                print(f"new state: {state_dict}")
                #继续烤制，记录数据
                state_dict=real_grill_process_one_minute(eng,model_name,state_dict)
                current_time_temp_list=collect_data(current_time_temp_list,state_dict,real_param_dict)
                print(f"$$$$$$$$$$$ Temperature data up to now: $$$$$$$$$$\n{current_time_temp_list}\n")
                time+=1
            else:
                #没有偏移，继续烤制，记录数据
                state_dict=real_grill_process_one_minute(eng,model_name,state_dict)
                time+=1
                current_time_temp_list=collect_data(current_time_temp_list,state_dict,real_param_dict)
                print(f"$$$$$$$$$$$ Temperature data up to now: $$$$$$$$$$\n{current_time_temp_list}\n")
        else:
            #烤制过程结束，打印结果，关闭引擎
            print(f"This is the final temperature data: \n{current_time_temp_list}")
            ovenControll.quit_matlab_engine(eng)
            break
            
    

