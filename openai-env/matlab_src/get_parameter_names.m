% 打开或加载Simulink模型
load_system('OvenSim');

% 启动模型
set_param('OvenSim', 'SimulationCommand', 'start');


% 获取显示部件的句柄
block_handle = get_param('OvenSim/humidity_display', 'Handle');

% 获取运行时对象
try
    rt = get_param(block_handle, 'RuntimeObject');

    % 检查是否获取到运行时对象
    if ~isempty(rt)
        % 获取输入端口的数据
        input_data = rt.InputPort(1).Data;
        disp(['输入端口 1 的值: ', num2str(input_data)]);
    else
        disp('运行时对象不可用。请确保模型正在运行。');
    end
catch ME
    disp(['发生错误: ', ME.message]);
end
