from prep import preprocessing, loader  
from sim import simulation, metrics, plt
from itertools import product
import time

# Parameters setting
num_of_cells = 2
num_of_CUEs = {2, 3, 4}
num_of_D2Ds = {2, 3, 4}
rate_proportion = 0.2
CA_list_time = [7.086, 8.188, 9.997, 8.253, 9.758, 14.038, 13.51, 16.457, 22.59]

# Get the image data format which Keras follows
image_data_format = loader.get_image_data_format()

# Get the input data and target data
input_data_list = [loader.load_input_data(num_of_cells, i, j, {2000, 8000, 10000}, image_data_format) for i in num_of_CUEs for j in num_of_D2Ds]
target_data_list = [loader.load_target_data(num_of_cells, i, j, {2000, 8000, 10000}) for i in num_of_CUEs for j in num_of_D2Ds]

# Reshape the input data
FCN_input_data_list, CNN_input_data_list, CNN_SPP_input_data_list = [[None] * len(input_data_list) for _ in range(3)]

for index, input_data in enumerate(input_data_list):
    rows, cols, channels = preprocessing.get_input_shape(input_data)
    FCN_input_data_list[index] = preprocessing.reshape_input_data_1D(input_data)
    CNN_input_data_list[index] = preprocessing.reshape_input_data_3D(input_data, image_data_format, rows, cols * channels, 1)
    CNN_SPP_input_data_list[index] = preprocessing.reshape_input_data_3D(input_data, image_data_format, rows, cols * channels, 1)

# Split the datadset into the training set and testing set
FCN_x_test_list, CNN_x_test_list, CNN_SPP_x_test_list, y_test_list = [[None] * len(input_data_list) for _ in range(4)]

for index, (FCN_input_data, CNN_input_data, CNN_SPP_input_data, target_data) in enumerate(zip(FCN_input_data_list, CNN_input_data_list, CNN_SPP_input_data_list, target_data_list)):
    (_, _), (FCN_x_test_list[index], y_test_list[index]) = preprocessing.split_dataset(FCN_input_data, target_data, proportion = 0.8, shuffle = False)
    (_, _), (CNN_x_test_list[index], y_test_list[index]) = preprocessing.split_dataset(CNN_input_data, target_data, proportion = 0.8, shuffle = False)
    (_, _), (CNN_SPP_x_test_list[index], y_test_list[index]) = preprocessing.split_dataset(CNN_SPP_input_data, target_data, proportion = 0.8, shuffle = False)

# Declare multiple empty lists
CA_list_sum_rate, FCN_list_sum_rate, CNN_list_sum_rate, CNN_SPP_list_sum_rate = [[] for _ in range(4)]
CA_list_power_consumption, FCN_list_power_consumption, CNN_list_power_consumption, CNN_SPP_list_power_consumption = [[] for _ in range(4)] 
CA_list_EE, FCN_list_EE, CNN_list_EE, CNN_SPP_list_EE = [[] for _ in range(4)]
CA_list_UIR, FCN_list_UIR, CNN_list_UIR, CNN_SPP_list_UIR = [[] for _ in range(4)] 
CA_list_RIR, FCN_list_RIR, CNN_list_RIR, CNN_SPP_list_RIR = [[] for _ in range(4)]
FCN_list_time, CNN_list_time, CNN_SPP_list_time = [[] for _ in range(3)]  

# Simulation
for FCN_x_test, CNN_x_test, CNN_SPP_x_test, y_test, (i, j) in zip(FCN_x_test_list, CNN_x_test_list, CNN_SPP_x_test_list, y_test_list, product(num_of_CUEs, num_of_D2Ds)):

    # Load the model
    FCN = loader.load_model('FCN', num_of_cells, i, j)
    CNN = loader.load_model('CNN', num_of_cells, i, j)
    CNN_SPP = loader.load_model('CNN-SPP', num_of_cells)

    channel_gain_matrix = simulation.get_channel_gain_matrix(FCN_x_test, num_of_cells, i, j)
    QoS_of_CUE = simulation.get_QoS_of_CUE(channel_gain_matrix, num_of_cells, i, rate_proportion)
    
    # Optimal resource allocation decisions generated by CA
    CA_CUE_power, CA_D2D_power = simulation.get_power_allocation(y_test, num_of_cells, i, j)
    CA_CUE_rate, CA_D2D_rate = simulation.get_data_rate(channel_gain_matrix, CA_CUE_power, CA_D2D_power)

    CA_system_sum_rate, CA_CUE_sum_rate, CA_D2D_sum_rate = metrics.get_sum_rate(CA_CUE_rate, CA_D2D_rate)
    CA_system_power_consumption, CA_CUE_power_consumption, CA_D2D_power_consumption = metrics.get_power_consumption(CA_CUE_power, CA_D2D_power)
    CA_system_EE, CA_CUE_EE, CA_D2D_EE = metrics.get_EE(CA_system_sum_rate, CA_CUE_sum_rate, CA_D2D_sum_rate, CA_system_power_consumption, CA_CUE_power_consumption, CA_D2D_power_consumption)
    CA_system_UIR, CA_CUE_UIR, CA_D2D_UIR = metrics.get_UIR(CA_CUE_rate, CA_D2D_rate, CA_CUE_power, CA_D2D_power, QoS_of_CUE)
    CA_system_RIR, CA_CUE_RIR, CA_D2D_RIR = metrics.get_RIR(CA_CUE_rate, CA_D2D_rate, CA_CUE_power, CA_D2D_power, QoS_of_CUE)

    CA_avg_system_sum_rate, CA_avg_CUE_sum_rate, CA_avg_D2D_sum_rate = metrics.get_avg_sum_rate(CA_system_sum_rate, CA_CUE_sum_rate, CA_D2D_sum_rate)
    CA_avg_system_power_consumption, CA_avg_CUE_power_consumption, CA_avg_D2D_power_consumption = metrics.get_avg_power_consumption(CA_system_power_consumption, CA_CUE_power_consumption, CA_D2D_power_consumption)
    CA_avg_system_EE, CA_avg_CUE_EE, CA_avg_D2D_EE = metrics.get_avg_EE(CA_system_EE, CA_CUE_EE, CA_D2D_EE)    
    CA_avg_system_UIR, CA_avg_CUE_UIR, CA_avg_D2D_UIR = metrics.get_avg_UIR(CA_system_UIR, CA_CUE_UIR, CA_D2D_UIR)
    CA_avg_system_RIR, CA_avg_CUE_RIR, CA_avg_D2D_RIR = metrics.get_avg_RIR(CA_system_RIR, CA_CUE_RIR, CA_D2D_RIR)

    # Performance of system
    CA_list_sum_rate.append(CA_avg_system_sum_rate)
    CA_list_power_consumption.append(CA_avg_system_power_consumption)
    CA_list_EE.append(CA_avg_system_EE)
    CA_list_UIR.append(CA_avg_system_UIR)
    CA_list_RIR.append(CA_avg_system_RIR)

    # Performance of CUE
    '''
    CA_list_sum_rate.append(CA_avg_CUE_sum_rate)
    CA_list_power_consumption.append(CA_avg_CUE_power_consumption)
    CA_list_EE.append(CA_avg_CUE_EE)
    CA_list_UIR.append(CA_avg_CUE_UIR)
    CA_list_RIR.append(CA_avg_CUE_RIR)
    '''

    # Performance of D2D pair
    '''
    CA_list_sum_rate.append(CA_avg_D2D_sum_rate)
    CA_list_power_consumption.append(CA_avg_D2D_power_consumption)
    CA_list_EE.append(CA_avg_D2D_EE)
    CA_list_UIR.append(CA_avg_D2D_UIR)
    CA_list_RIR.append(CA_avg_D2D_RIR)
    '''
    
    # Predicted resource allocation decisions generated by FCN
    start = time.clock()
    FCN_y_test = FCN.predict(FCN_x_test)
    end = time.clock()
    FCN_list_time.append((end - start) / len(FCN_x_test))

    FCN_CUE_power, FCN_D2D_power = simulation.get_power_allocation(FCN_y_test, num_of_cells, i, j)
    FCN_CUE_rate, FCN_D2D_rate = simulation.get_data_rate(channel_gain_matrix, FCN_CUE_power, FCN_D2D_power)

    FCN_system_sum_rate, FCN_CUE_sum_rate, FCN_D2D_sum_rate = metrics.get_sum_rate(FCN_CUE_rate, FCN_D2D_rate)
    FCN_system_power_consumption, FCN_CUE_power_consumption, FCN_D2D_power_consumption = metrics.get_power_consumption(FCN_CUE_power, FCN_D2D_power)
    FCN_system_EE, FCN_CUE_EE, FCN_D2D_EE = metrics.get_EE(FCN_system_sum_rate, FCN_CUE_sum_rate, FCN_D2D_sum_rate, FCN_system_power_consumption, FCN_CUE_power_consumption, FCN_D2D_power_consumption)
    FCN_system_UIR, FCN_CUE_UIR, FCN_D2D_UIR = metrics.get_UIR(FCN_CUE_rate, FCN_D2D_rate, FCN_CUE_power, FCN_D2D_power, QoS_of_CUE)
    FCN_system_RIR, FCN_CUE_RIR, FCN_D2D_RIR = metrics.get_RIR(FCN_CUE_rate, FCN_D2D_rate, FCN_CUE_power, FCN_D2D_power, QoS_of_CUE)

    FCN_avg_system_sum_rate, FCN_avg_CUE_sum_rate, FCN_avg_D2D_sum_rate = metrics.get_avg_sum_rate(FCN_system_sum_rate, FCN_CUE_sum_rate, FCN_D2D_sum_rate)
    FCN_avg_system_power_consumption, FCN_avg_CUE_power_consumption, FCN_avg_D2D_power_consumption = metrics.get_avg_power_consumption(FCN_system_power_consumption, FCN_CUE_power_consumption, FCN_D2D_power_consumption)
    FCN_avg_system_EE, FCN_avg_CUE_EE, FCN_avg_D2D_EE = metrics.get_avg_EE(FCN_system_EE, FCN_CUE_EE, FCN_D2D_EE)
    FCN_avg_system_UIR, FCN_avg_CUE_UIR, FCN_avg_D2D_UIR = metrics.get_avg_UIR(FCN_system_UIR, FCN_CUE_UIR, FCN_D2D_UIR)
    FCN_avg_system_RIR, FCN_avg_CUE_RIR, FCN_avg_D2D_RIR = metrics.get_avg_RIR(FCN_system_RIR, FCN_CUE_RIR, FCN_D2D_RIR)

    # Performance of system
    FCN_list_sum_rate.append(FCN_avg_system_sum_rate)
    FCN_list_power_consumption.append(FCN_avg_system_power_consumption)
    FCN_list_EE.append(FCN_avg_system_EE)
    FCN_list_RIR.append(FCN_avg_system_RIR)
    FCN_list_UIR.append(FCN_avg_system_UIR)

    # Performance of CUE
    '''
    FCN_list_sum_rate.append(FCN_avg_CUE_sum_rate)
    FCN_list_power_consumption.append(FCN_avg_CUE_power_consumption)
    FCN_list_EE.append(FCN_avg_CUE_EE)
    FCN_list_RIR.append(FCN_avg_CUE_RIR)
    FCN_list_UIR.append(FCN_avg_CUE_UIR)
    '''

    # Performance of D2D pair
    '''
    FCN_list_sum_rate.append(FCN_avg_D2D_sum_rate)
    FCN_list_power_consumption.append(FCN_avg_D2D_power_consumption)
    FCN_list_EE.append(FCN_avg_D2D_EE)
    FCN_list_RIR.append(FCN_avg_D2D_RIR)
    FCN_list_UIR.append(FCN_avg_D2D_UIR)
    '''

    # Predicted resourec allocation decisions generated by CNN
    start = time.clock()
    CNN_y_test = CNN.predict(CNN_x_test)
    end = time.clock()
    CNN_list_time.append((end - start) / len(CNN_x_test))

    CNN_CUE_power, CNN_D2D_power = simulation.get_power_allocation(CNN_y_test, num_of_cells, i, j)
    CNN_CUE_rate, CNN_D2D_rate = simulation.get_data_rate(channel_gain_matrix, CNN_CUE_power, CNN_D2D_power)

    CNN_system_sum_rate, CNN_CUE_sum_rate, CNN_D2D_sum_rate = metrics.get_sum_rate(CNN_CUE_rate, CNN_D2D_rate)
    CNN_system_power_consumption, CNN_CUE_power_consumption, CNN_D2D_power_consumption = metrics.get_power_consumption(CNN_CUE_power, CNN_D2D_power)
    CNN_system_EE, CNN_CUE_EE, CNN_D2D_EE = metrics.get_EE(CNN_system_sum_rate, CNN_CUE_sum_rate, CNN_D2D_sum_rate, CNN_system_power_consumption, CNN_CUE_power_consumption, CNN_D2D_power_consumption)
    CNN_system_UIR, CNN_CUE_UIR, CNN_D2D_UIR = metrics.get_UIR(CNN_CUE_rate, CNN_D2D_rate, CNN_CUE_power, CNN_D2D_power, QoS_of_CUE)
    CNN_system_RIR, CNN_CUE_RIR, CNN_D2D_RIR = metrics.get_RIR(CNN_CUE_rate, CNN_D2D_rate, CNN_CUE_power, CNN_D2D_power, QoS_of_CUE)

    CNN_avg_system_sum_rate, CNN_avg_CUE_sum_rate, CNN_avg_D2D_sum_rate = metrics.get_avg_sum_rate(CNN_system_sum_rate, CNN_CUE_sum_rate, CNN_D2D_sum_rate)
    CNN_avg_system_power_consumption, CNN_avg_CUE_power_consumption, CNN_avg_D2D_power_consumption = metrics.get_avg_power_consumption(CNN_system_power_consumption, CNN_CUE_power_consumption, CNN_D2D_power_consumption)
    CNN_avg_system_EE, CNN_avg_CUE_EE, CNN_avg_D2D_EE = metrics.get_avg_EE(CNN_system_EE, CNN_CUE_EE, CNN_D2D_EE)
    CNN_avg_system_UIR, CNN_avg_CUE_UIR, CNN_avg_D2D_UIR = metrics.get_avg_UIR(CNN_system_UIR, CNN_CUE_UIR, CNN_D2D_UIR)
    CNN_avg_system_RIR, CNN_avg_CUE_RIR, CNN_avg_D2D_RIR = metrics.get_avg_RIR(CNN_system_RIR, CNN_CUE_RIR, CNN_D2D_RIR)

    # Performance of system
    CNN_list_sum_rate.append(CNN_avg_system_sum_rate)
    CNN_list_power_consumption.append(CNN_avg_system_power_consumption)
    CNN_list_EE.append(CNN_avg_system_EE)
    CNN_list_UIR.append(CNN_avg_system_UIR)
    CNN_list_RIR.append(CNN_avg_system_RIR)

    # Performance of CUE
    '''
    CNN_list_sum_rate.append(CNN_avg_CUE_sum_rate)
    CNN_list_power_consumption.append(CNN_avg_CUE_power_consumption)
    CNN_list_EE.append(CNN_avg_CUE_EE)
    CNN_list_UIR.append(CNN_avg_CUE_UIR)
    CNN_list_RIR.append(CNN_avg_CUE_RIR)
    '''

    # Performance of D2D pair
    '''
    CNN_list_sum_rate.append(CNN_avg_D2D_sum_rate)
    CNN_list_power_consumption.append(CNN_avg_D2D_power_consumption)
    CNN_list_EE.append(CNN_avg_D2D_EE)
    CNN_list_UIR.append(CNN_avg_D2D_UIR)
    CNN_list_RIR.append(CNN_avg_D2D_RIR)
    '''

    # Predicted resourec allocation decisions generated by FCN
    start = time.clock()
    CNN_SPP_y_test = CNN_SPP.predict(CNN_SPP_x_test)
    end = time.clock()
    CNN_SPP_list_time.append((end - start) / len(CNN_SPP_x_test))
    CNN_SPP_y_test = preprocessing.remove_redundant_zeros(CNN_SPP_y_test, num_of_cells, i, j)

    CNN_SPP_CUE_power, CNN_SPP_D2D_power = simulation.get_power_allocation(CNN_SPP_y_test, num_of_cells, i, j)
    CNN_SPP_CUE_rate, CNN_SPP_D2D_rate = simulation.get_data_rate(channel_gain_matrix, CNN_SPP_CUE_power, CNN_SPP_D2D_power)

    CNN_SPP_system_sum_rate, CNN_SPP_CUE_sum_rate, CNN_SPP_D2D_sum_rate = metrics.get_sum_rate(CNN_SPP_CUE_rate, CNN_SPP_D2D_rate)
    CNN_SPP_system_power_consumption, CNN_SPP_CUE_power_consumption, CNN_SPP_D2D_power_consumption = metrics.get_power_consumption(CNN_SPP_CUE_power, CNN_SPP_D2D_power)
    CNN_SPP_system_EE, CNN_SPP_CUE_EE, CNN_SPP_D2D_EE = metrics.get_EE(CNN_SPP_system_sum_rate, CNN_SPP_CUE_sum_rate, CNN_SPP_D2D_sum_rate, CNN_SPP_system_power_consumption, CNN_SPP_CUE_power_consumption, CNN_SPP_D2D_power_consumption)
    CNN_SPP_system_UIR, CNN_SPP_CUE_UIR, CNN_SPP_D2D_UIR = metrics.get_UIR(CNN_SPP_CUE_rate, CNN_SPP_D2D_rate, CNN_SPP_CUE_power, CNN_SPP_D2D_power, QoS_of_CUE)
    CNN_SPP_system_RIR, CNN_SPP_CUE_RIR, CNN_SPP_D2D_RIR = metrics.get_RIR(CNN_SPP_CUE_rate, CNN_SPP_D2D_rate, CNN_SPP_CUE_power, CNN_SPP_D2D_power, QoS_of_CUE)

    CNN_SPP_avg_system_sum_rate, CNN_SPP_avg_CUE_sum_rate, CNN_SPP_avg_D2D_sum_rate = metrics.get_avg_sum_rate(CNN_SPP_system_sum_rate, CNN_SPP_CUE_sum_rate, CNN_SPP_D2D_sum_rate)
    CNN_SPP_avg_system_power_consumption, CNN_SPP_avg_CUE_power_consumption, CNN_SPP_avg_D2D_power_consumption = metrics.get_avg_power_consumption(CNN_SPP_system_power_consumption, CNN_SPP_CUE_power_consumption, CNN_SPP_D2D_power_consumption)
    CNN_SPP_avg_system_EE, CNN_SPP_avg_CUE_EE, CNN_SPP_avg_D2D_EE = metrics.get_avg_EE(CNN_SPP_system_EE, CNN_SPP_CUE_EE, CNN_SPP_D2D_EE)
    CNN_SPP_avg_system_UIR, CNN_SPP_avg_CUE_UIR, CNN_SPP_avg_D2D_UIR = metrics.get_avg_UIR(CNN_SPP_system_UIR, CNN_SPP_CUE_UIR, CNN_SPP_D2D_UIR)
    CNN_SPP_avg_system_RIR, CNN_SPP_avg_CUE_RIR, CNN_SPP_avg_D2D_RIR = metrics.get_avg_RIR(CNN_SPP_system_RIR, CNN_SPP_CUE_RIR, CNN_SPP_D2D_RIR)

    # Performance of system
    CNN_SPP_list_sum_rate.append(CNN_SPP_avg_system_sum_rate)
    CNN_SPP_list_power_consumption.append(CNN_SPP_avg_system_power_consumption)
    CNN_SPP_list_EE.append(CNN_SPP_avg_system_EE)
    CNN_SPP_list_UIR.append(CNN_SPP_avg_system_UIR)
    CNN_SPP_list_RIR.append(CNN_SPP_avg_system_RIR)

    # Performance of CUE
    '''
    CNN_SPP_list_sum_rate.append(CNN_SPP_avg_CUE_sum_rate)
    CNN_SPP_list_power_consumption.append(CNN_SPP_avg_CUE_power_consumption)
    CNN_SPP_list_EE.append(CNN_SPP_avg_CUE_EE)
    CNN_SPP_list_UIR.append(CNN_SPP_avg_CUE_UIR)
    CNN_SPP_list_RIR.append(CNN_SPP_avg_CUE_RIR)
    '''

    # Performance of D2D pair
    '''
    CNN_SPP_list_sum_rate.append(CNN_SPP_avg_D2D_sum_rate)
    CNN_SPP_list_power_consumption.append(CNN_SPP_avg_D2D_power_consumption)
    CNN_SPP_list_EE.append(CNN_SPP_avg_D2D_EE)
    CNN_SPP_list_UIR.append(CNN_SPP_avg_D2D_UIR)
    CNN_SPP_list_RIR.append(CNN_SPP_avg_D2D_RIR)
    '''

plt.plot_sum_rate('system', num_of_CUEs, num_of_D2Ds, CA_list_sum_rate, CNN_SPP_list_sum_rate, CNN_list_sum_rate, FCN_list_sum_rate)
plt.plot_power_consumption('system', num_of_CUEs, num_of_D2Ds, CA_list_power_consumption, CNN_SPP_list_power_consumption, CNN_list_power_consumption, FCN_list_power_consumption)
plt.plot_EE('system', num_of_CUEs, num_of_D2Ds, CA_list_EE, CNN_SPP_list_EE, CNN_list_EE, FCN_list_EE)
plt.plot_NN_computational_time(num_of_CUEs, num_of_D2Ds, CNN_SPP_list_time, CNN_list_time, FCN_list_time)
plt.plot_CA_computational_time(num_of_CUEs, num_of_D2Ds, CA_list_time)
#plt.plot_UIR('system', num_of_CUEs, num_of_D2Ds, CA_list_UIR, CNN_SPP_list_UIR, CNN_list_UIR, FCN_list_UIR)
#plt.plot_RIR('system', num_of_CUEs, num_of_D2Ds, CA_list_RIR, CNN_SPP_list_RIR, CNN_list_RIR, FCN_list_RIR)