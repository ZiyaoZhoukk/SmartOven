import matlab.engine
import re
import json
import time

def create_param_dict_from_LLM_answer(GPT_pic_recog_result_text):
    """从文本中提取并解析JSON部分"""
    # 使用正则表达式提取JSON部分
    json_match = re.search(r'(\{(?:[^\{\}]*\n){8,}[^\{\}]*\})', GPT_pic_recog_result_text)

    if json_match:
        json_str = json_match.group(0)
        # 将JSON字符串转换为Python字典
        param_dict = json.loads(json_str)
        print('\n======= Param dict created =======\n')
        print(param_dict)  
        print('\n')
        return param_dict
    else:
        print("Failed to find JSON part...")
        return None
    
def start_matlab_engine():
    """启动MATLAB引擎并加载所需路径"""
    print("\n===== Starting MATLAB engine... =====")
    eng = matlab.engine.start_matlab()
    print("===== MATLAB engine started =====\n")
    eng.addpath('/Users/zhouziyao/Desktop/LLM_Smart_Oven_Controll/openai-env/matlab_src')
    return eng

def load_simulink_model(eng, model_name):
    """加载Simulink模型"""
    print("\n===== Loading simulation... =====")
    eng.load_system(model_name)
    print("===== Simulation successfully loaded =====\n")

def run_matlab_file(eng, matlab_file):
    """运行MATLAB文件以配置基本参数"""
    print("======= Running MATLAB file to configure basic parameters... =======\n")
    eng.run(matlab_file, nargout=0)

def matlab_initialization(model_name,matlab_file):
    eng=start_matlab_engine()
    load_simulink_model(eng,model_name)
    run_matlab_file(eng,matlab_file)
    return eng

def set_complete_parameters(eng, model_name, referenced_param_dict):
    """设置模型参数"""
    print("======= Setting parameters from JSON... =======\n")
    # 设置烤箱温度
    eng.set_param(f"{model_name}/oven_temp1", 'Value', referenced_param_dict["first_period_temp"], nargout=0)
    eng.set_param(f"{model_name}/oven_temp2", 'Value', referenced_param_dict["first_period_temp"], nargout=0)
    eng.set_param(f"{model_name}/InnerWallsofOven", 'T', referenced_param_dict["first_period_temp"], nargout=0)
    eng.set_param(f"{model_name}/Dynamic_Thermal_Mass", 'T', referenced_param_dict["first_period_temp"], nargout=0)
    
    # 设置烤箱风扇速度
    eng.set_param(f"{model_name}/fan_speed", 'Value', referenced_param_dict["first_period_fan_speed"], nargout=0)
    
    # 设置食物初始状态
    eng.set_param(f"{model_name}/foodstuff", 'sp_heat', referenced_param_dict["heat_capacity"], nargout=0)
    eng.set_param(f"{model_name}/foodstuff", 'mass', referenced_param_dict["m"], nargout=0)
    eng.set_param(f"{model_name}/foodstuff", 'T', referenced_param_dict["initial_temp"], nargout=0)
    eng.set_param(f"{model_name}/A_food", 'Gain', referenced_param_dict["A"], nargout=0)
    eng.set_param(f"{model_name}/Convective_Heat_Transfer1", 'Area', referenced_param_dict["A"], nargout=0)
    eng.set_param(f"{model_name}/initial_water_content", 'Value', referenced_param_dict["water_content"], nargout=0)

def run_model_to_get_reference(eng, model_name, referenced_param_dict):
    """运行仿真并根据时间点修改参数"""
    change_time = float(referenced_param_dict["first_period"])
    stop_time = str(float(referenced_param_dict["first_period"]) + float(referenced_param_dict["second_period"]))
    print(f"\nStop time is: {stop_time}\n")

    # 启动仿真
    eng.set_param(model_name, 'StartTime', '0', 'StopTime', stop_time, nargout=0)
    eng.set_param(model_name, 'SimulationCommand', 'start', nargout=0)
    print("\n===== Simulation running... =====\n")

    while True:
        # 获取仿真时间
        sim_time = eng.get_param(model_name, 'SimulationTime')

        # 检查仿真时间
        if sim_time >= change_time:
            print(f'The simulation should be changed at {change_time:.2f}')
            print(f'Current simulation time: {sim_time:.2f} seconds, parameter has been modified.')

            # 设置烤箱目标温度
            eng.set_param(f"{model_name}/oven_temp1", 'Value', referenced_param_dict["second_period_temp"], nargout=0)
            eng.set_param(f"{model_name}/oven_temp2", 'Value', referenced_param_dict["second_period_temp"], nargout=0)
            eng.set_param(f"{model_name}/fan_speed", 'Value', referenced_param_dict["second_period_fan_speed"], nargout=0)

            print('\n=========== Parameters for roasting have been modified! ===========\n')
            break

        # 短暂暂停以防止系统高使用率
        time.sleep(0.05)

def run_model_for_one_minute(eng, model_name, real_param_or_state_dict):
    #1.应用状态并改烘烤操作（设置温度和风扇）
    if len(real_param_or_state_dict)<8:
        #应用状态
        eng.set_param(f"{model_name}/InnerWallsofOven", 'T', real_param_or_state_dict["oven_wall_temp"], nargout=0)
        eng.set_param(f"{model_name}/Dynamic_Thermal_Mass", 'T', real_param_or_state_dict["oven_air_temp"], nargout=0)
        eng.set_param(f"{model_name}/foodstuff", 'T', real_param_or_state_dict["food_temp"], nargout=0)
        eng.set_param(f"{model_name}/initial_water_content", 'Value', real_param_or_state_dict["water_content"], nargout=0)
        eng.set_param(f"{model_name}/initial_humidity", 'Value', real_param_or_state_dict["humidity"], nargout=0)
        #更改烘烤操作
        eng.set_param(f"{model_name}/fan_speed", 'Value', real_param_or_state_dict["fan_speed"], nargout=0)
        eng.set_param(f"{model_name}/oven_temp1", 'Value', real_param_or_state_dict["heat_resistor_temp"], nargout=0)
        eng.set_param(f"{model_name}/oven_temp2", 'Value', real_param_or_state_dict["heat_resistor_temp"], nargout=0)
    if len(real_param_or_state_dict)>=8:#第一次一分钟
        set_complete_parameters(eng,model_name,real_param_or_state_dict)   
    #2.跑一分钟
    eng.set_param(model_name, 'StartTime', '0', 'StopTime', "60", nargout=0)
    eng.set_param(model_name, 'SimulationCommand', 'start', nargout=0)
    eng.run('move_outputs_to_workspace.m',nargout=0)#从workspace取出仿真输出
    #3.记录状态为字典
    record_state={}
    record_state["oven_wall_temp"] = str(eng.workspace['wall_temp'])
    record_state["oven_air_temp"] = str(eng.workspace['air_temp'])
    record_state["food_temp"] = str(eng.workspace['food_temp'])
    record_state["water_content"] = str(eng.workspace['water_content'])
    record_state["humidity"] = str(eng.workspace['humidity'])
    record_state["fan_speed"] = eng.get_param(f"{model_name}/fan_speed", 'Value')
    record_state["heat_resistor_temp"] = eng.get_param(f"{model_name}/oven_temp1", 'Value')
    
    return record_state

def simulation_is_finished(eng,model_name):
    #判断仿真是否结束
    while True:
            status = eng.get_param(model_name, 'SimulationStatus')
            if status == 'stopped': 
                isFinished=True          
                break
            isFinished=False
            time.sleep(1) 
    return isFinished 

def get_reference_data(eng,model_name):
    if simulation_is_finished(eng,model_name):
        eng.run('move_outputs_to_workspace.m',nargout=0)#从workspace取出仿真输出
        time_points=eng.workspace['time_points']
        values=eng.workspace['values']
        #每60秒取样一次
        reduced_time_points = time_points[::60]
        reduced_values = values[::60]
        #将数组转换为长字符串for LLM
        time_temp_str = ', '.join(f"{tp}:{val}" for tp, val in zip(reduced_time_points, reduced_values))
    return time_temp_str

def quit_matlab_engine(eng):
    eng.quit()

#================================================================================下面是几个总函数
def reference_simulate(eng,model_name,GTP_pic_recog_result_text):
    #根据GPT生成方案，跑一遍仿真并记录曲线
    param_dict = create_param_dict_from_LLM_answer(GTP_pic_recog_result_text)
    if param_dict:
        set_complete_parameters(eng, model_name, param_dict)
        run_model_to_get_reference(eng, model_name, param_dict)
        return get_reference_data(eng,model_name)
    
def real_simulate_one_minute(eng,model_name,real_param_or_state_dict):
    #跑一分钟仿真，用来模拟真实情形
    state_param=run_model_for_one_minute(eng,model_name,real_param_or_state_dict)
    return state_param
        
def main():
    #理论上不调用
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
    eng=matlab_initialization(model_name,matlab_file)
    print(reference_simulate(eng,model_name,text))
    quit_matlab_engine(eng)

if __name__ == "__main__":
    main()

