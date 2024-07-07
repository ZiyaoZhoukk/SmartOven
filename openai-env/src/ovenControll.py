import matlab.engine
import re
import json
import time

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

def set_parameters(eng, model_name, param_dict):
    """设置模型参数"""
    print("======= Setting parameters from JSON... =======\n")
    # 设置烤箱温度
    eng.set_param(f"{model_name}/oven_temp1", 'Value', param_dict["first_period_temp"], nargout=0)
    eng.set_param(f"{model_name}/oven_temp2", 'Value', param_dict["first_period_temp"], nargout=0)
    eng.set_param(f"{model_name}/InnerWallsofOven", 'T', param_dict["first_period_temp"], nargout=0)
    eng.set_param(f"{model_name}/Dynamic_Thermal_Mass", 'T', param_dict["first_period_temp"], nargout=0)
    
    # 设置烤箱风扇速度
    eng.set_param(f"{model_name}/fan_speed", 'Value', param_dict["first_period_fan_speed"], nargout=0)
    
    # 设置食物初始状态
    eng.set_param(f"{model_name}/foodstuff", 'sp_heat', param_dict["heat_capacity"], nargout=0)
    eng.set_param(f"{model_name}/foodstuff", 'mass', param_dict["m"], nargout=0)
    eng.set_param(f"{model_name}/foodstuff", 'T', param_dict["initial_temp"], nargout=0)
    eng.set_param(f"{model_name}/A_food", 'Gain', param_dict["A"], nargout=0)
    eng.set_param(f"{model_name}/Convective_Heat_Transfer1", 'Area', param_dict["A"], nargout=0)
    eng.set_param(f"{model_name}/initial_water_content", 'Value', param_dict["water_content"], nargout=0)

def run_simulation(eng, model_name, param_dict):
    """运行仿真并根据时间点修改参数"""
    change_time = float(param_dict["first_period"])
    stop_time = str(float(param_dict["first_period"]) + float(param_dict["second_period"]))
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
            eng.set_param(f"{model_name}/oven_temp1", 'Value', param_dict["second_period_temp"], nargout=0)
            eng.set_param(f"{model_name}/oven_temp2", 'Value', param_dict["second_period_temp"], nargout=0)
            eng.set_param(f"{model_name}/fan_speed", 'Value', param_dict["second_period_fan_speed"], nargout=0)

            print('\n=========== Parameters for roasting have been modified! ===========\n')
            break

        # 短暂暂停以防止系统高使用率
        time.sleep(0.1)

def stop_simulation(eng, model_name):
    """停止仿真并关闭MATLAB引擎"""

    # 等待仿真停止
    while True:
        status = eng.get_param(model_name, 'SimulationStatus')
        if status == 'stopped':           
            break
        time.sleep(1)  # 等待 1 秒后再次检查
    eng.run('move_outputs_to_workspace.m',nargout=0)
    time_points=eng.workspace['time_points']
    values=eng.workspace['values']
    reduced_time_points = time_points[::60]
    reduced_values = values[::60]
    # 5. 将数组转换为长字符串
    combined_str = ', '.join(f"{tp}:{val}" for tp, val in zip(reduced_time_points, reduced_values))
    print(combined_str)


    input("Press Enter to end the simulation and close MATLAB...")
    eng.quit()

def create_param_dict_from_LLM_answer(text):
    """从文本中提取并解析JSON部分"""
    # 使用正则表达式提取JSON部分
    json_match = re.search(r'{[\s\S]*}', text)

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
    "type of food": "whole chicken",
    "heat_capacity": "2500",
    "m": "1.5",
    "water_content": "70",
    "initial_temp": "4",
    "A": "0.1",
    "first_period": "1200",
    "first_period_temp": "220",
    "first_period_fan_speed": "2500",
    "second_period": "2700",
    "second_period_temp": "180",
    "second_period_fan_speed": "1500"
    }
    This plan ensures that the chicken is cooked thoroughly with a crispy skin and juicy interior. Adjustments can be made based on specific oven performance and preferences.
    """

    param_dict = create_param_dict_from_LLM_answer(text)
    if param_dict:
        eng = start_matlab_engine()
        load_simulink_model(eng, model_name)
        run_matlab_file(eng, matlab_file)
        set_parameters(eng, model_name, param_dict)
        run_simulation(eng, model_name, param_dict)
        stop_simulation(eng, model_name)

if __name__ == "__main__":
    main()
