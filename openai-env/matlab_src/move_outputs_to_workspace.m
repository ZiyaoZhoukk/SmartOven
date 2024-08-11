time_points = round(out.scope_data.time);  % 提取数据
values=round(out.scope_data.signals.values,1);
water_content = round(out.water_content(end),1);
humidity = round(out.humidity(end),1);
wall_temp=round(out.wall_temp(end),1);
air_temp=round(out.air_temp(end),1);
food_temp=round(out.food_temp(end),1);
% display(water_content);
% display(humidity);