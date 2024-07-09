% set simulation constants 
c_innerwalls=500;
m_innerwalls=9.6;
A_innerwalls=1.12; % heating area of inner walls of the oven
c_gas=1005; % specific heat capacity of gas
m_gas=0.0735; % weight of gas
A_gas=A_innerwalls; % Gas heating area is approximated as the sum of the areas of the oven's inner walls
epsilon_food=0.9; % emissivity factor of food
epsilon_innerWalls=0.6;
sigma=5.67e-8; % Steffan-Boltzmann constant
h_innerwalls=20; % heat transfer coefficient of innerwalls
radiation_loss_coefficient=0.18;
convection_loss_coefficient=0.07;


% load,update and start simulink model
modelName = 'OvenSim'; 
load_system(modelName);
set_param(modelName, 'SimulationCommand', 'update');

% % python part=============================================
% % set oven temperatures
% set_param('OvenSim/oven_temp1', 'Value', '200');
% set_param('OvenSim/oven_temp2', 'Value', '200');
% 
% set_param('OvenSim/InnerWallsofOven', 'T', '200');
% set_param('OvenSim/Dynamic_Thermal_Mass', 'T', '200');
% % set oven fan speed
% set_param('OvenSim/fan_speed', 'Value', '2500');
% 
% % set food initial state
% set_param('OvenSim/foodstuff', 'sp_heat', '3000');
% set_param('OvenSim/foodstuff', 'mass', '1.3');
% set_param('OvenSim/foodstuff', 'T', '7');
% set_param('OvenSim/A_food', 'Gain', '0.2');
% set_param('OvenSim/Convective_Heat_Transfer1', 'Area', '0.2');
% set_param('OvenSim/initial_water_content', 'Value', '75');
% 
% % start simulation
% set_param('OvenSim', 'StartTime', '0', 'StopTime', '3200')  
% set_param(modelName,"SimulationCommand","start");
% 
% 
% while true
% 
%     simTime = get_param(modelName,"SimulationTime");
% 
%     % check simulation time
%     if simTime >= 1200
% 
%         fprintf('Current simulation time: %.2f seconds\n', simTime);
% 
%         % set oven target temperature
%         set_param('OvenSim/oven_temp1', 'Value', '160');
%         set_param('OvenSim/oven_temp2', 'Value', '160');
% 
%         set_param('OvenSim/fan_speed', 'Value', '1500');
% 
%         fprintf('constant modified!\n');
% 
%         break;
%     end
% 
%     % a short pause to prevent high system usage
%     pause(0.1)
% end
