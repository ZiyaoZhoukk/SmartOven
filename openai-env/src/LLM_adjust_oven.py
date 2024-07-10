import ovenControll

def get_reference_data(eng,model_name,LLM_generated_text):
    """use this parameter configuration to run the simulation and get a sequence of time-temperature text"""
    #跑完整的simulation，拿到对照曲线（理论只调用一次)
    time_temp=ovenControll.reference_simulate(eng,model_name,LLM_generated_text)
    return time_temp

def combine_real_food_params_and_LLM_generated_grill_process(LLM_generated_text,real_param_list):#记得要修改create方法的内容，参考LLM识图
    #生成烘烤字典：把GPT生成的烘烤过程保留，加上实际鸡的properties。real_param_text里面是"'3000','2','80','20','0.2'"
    param_dict=ovenControll.create_param_dict_from_LLM_answer(LLM_generated_text)
    keys=list(param_dict.keys())
    for i in range(1, 6):
        param_dict[keys[i]] = real_param_list[i - 1]
    return param_dict

def real_grill_process_one_minute(eng,model_name,state_param):
    """run one minute sim with given state, record the end state, get the time-temp data"""
    #只跑一分钟（用来模拟真实烤制情形），记录状态，保存数据
    state_after_sim=ovenControll.real_simulate_one_minute(eng,model_name,state_param)
    return state_after_sim


def call_LLM_is_negligible_error(prompt):
    #函数名可以叫是否出现偏移/是否和预想不一样/是否需要进行操作？
    yesORno=''
    return yesORno

def call_LLM_find_reason(prompt):
    #比热容，质量，含水量，初始温度，表面积：其中的某几个出了问题
    reason=''
    return reason

def call_LLM_generate_controll_instruction(prompt):
    #只需要知道下一分钟是什么参数烤,还要返回可能造成的影响（时间上）
    state=''
    return state







def main():
    model_name = 'OvenSim'
    matlab_file = 'ovenSimConfig.m'
    text = """
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
    real_param_dict=combine_real_food_params_and_LLM_generated_grill_process(text,real_food_properties)
    print (real_param_dict)
    eng=ovenControll.matlab_initialization(model_name,matlab_file)
    state=real_grill_process_one_minute(eng,model_name,real_param_dict)
    print(state)
    state=real_grill_process_one_minute(eng,model_name,state)
    print(state)
    state=real_grill_process_one_minute(eng,model_name,state)
    print(state)
    ovenControll.quit_matlab_engine(eng)


if __name__ == "__main__":
    main()

