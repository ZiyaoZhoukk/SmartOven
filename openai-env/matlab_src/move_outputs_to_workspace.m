time_points = round(out.scope_data.time);  % 提取数据
values=round(out.scope_data.signals.values);
water_content = round(out.water_content(end));
humidity = round(out.humidity(end));
wall_temp=round(out.wall_temp(end));
air_temp=round(out.air_temp(end));
food_temp=round(out.food_temp(end));
% display(water_content);
% display(humidity);