from packages.output import market_csv
import numpy as np
import matplotlib.pyplot as plt
from packages.tech.trade_check import all_indicators


def minmax(data):
    local_min = (np.diff(np.sign(np.diff(data))) > 0).nonzero()[0] + 1  # local min
    local_max = (np.diff(np.sign(np.diff(data))) < 0).nonzero()[0] + 1  # local max
    return local_min, local_max


# local min, max
periods = 100
# smooth data
data = market_csv.csv_read_recent('USD_JPY', 'H1', periods)
indicators = all_indicators('USD_JPY', 'H1', data)['indicators']
close = data['close']
open_data = data['open']
x_axis = np.array([x for x in range(periods)])
# min max
# average data minmax
avr_data = (close + open_data) / 2
avr_data = indicators['rsi']
print(len(avr_data))
b, c = minmax(avr_data)
price_point_min = []
for point in b:
    price_point_min.append(avr_data[point])
# normalize y-axis(price)
low_min = min(price_point_min)
high_min = max(price_point_min)
norm_pp = []
for x in price_point_min:
    norm_pp.append((x-low_min)/(high_min - low_min) * periods)

pp_min = np.array(norm_pp)
combined_min_norm = np.vstack((b, pp_min)).T
# get slopes
for x in range(len(pp_min) - 1):
    print((combined_min_norm[x][1]-combined_min_norm[x + 1][1]) / (combined_min_norm[x][0] - combined_min_norm[x + 1][0]))

price_point_max = []
for point in c:
    price_point_max.append(avr_data[point])
# normalize y-axis(price)
low_max = min(price_point_max)
high_max = max(price_point_max)
norm_pp = []
for x in price_point_max:
    norm_pp.append((x-low_max)/(high_max - low_max) * periods)
pp_max = np.array(norm_pp)
combined_max_norm = np.vstack((c, pp_max)).T
for x in range(len(pp_min) - 1):
    print((combined_max_norm[x][1]-combined_max_norm[x + 1][1]) / (combined_max_norm[x][0] - combined_max_norm[x + 1][0]))


# find support and resistance levels
# support
combined_min = np.vstack((b, price_point_min)).T
overall_sup = min(price_point_min)
overall_sup_loc = b[price_point_min.index(overall_sup)]
#print(combined_min)
#print('overal sup', overall_sup)
#print('overall_sup_loc', overall_sup_loc)
# print basic graph
plt.plot(x_axis, avr_data)
b, c = minmax(avr_data)
plt.figure(1)
plt.plot(x_axis[b], avr_data[b], 'o', color='r')
plt.plot(x_axis[c], avr_data[c], 'o', color='b')
plt.title('Average')
plt.show()
