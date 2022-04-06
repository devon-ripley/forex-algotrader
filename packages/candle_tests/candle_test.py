import pandas as pd
from packages.candle_tests import plot_candle

prices = pd.DataFrame({'open': [90],
                       'close': [80],
                       'high': [100],
                       'low': [40]})
open_point = prices['open'][0]
close_point = prices['close'][0]
high_point = prices['high'][0]
low_point = prices['low'][0]
box = abs(open_point - close_point)
box_points = [open_point, close_point]
handle_start = min(box_points)
handle = handle_start - low_point
whole_length = high_point - low_point
top_length = abs(open_point - high_point)
bottom_length = abs(open_point - low_point)
#ratios
top_stick_ratio = top_length / whole_length
print('top_stick_ratio', top_stick_ratio)
box_whole_ratio = box / whole_length
print('box_whole_ratio', box_whole_ratio)
bottom_stick_ratio = handle / whole_length
print('bottom_stick_ratio', bottom_stick_ratio)
# body_location
middle_box = open_point - (box / 2)
location_mult = 100 / whole_length
middle_box_location = location_mult * (middle_box - low_point)
# box location
print('middle_box_location', middle_box_location)
plot_candle.plot(prices)