import csv
import numpy as np
import pandas as pd
df = pd.read_csv("packet_latencies.txt")


def find_packet_latency_poly(poly_func, val):
    return poly_func(val)


# Make a data strucutre to store the packet latencies for it.
def get_latency(packet_size: int, column_index: int) -> float:
    """
    Get latency for a given packet size and column index.
    :param packet_size: The 'Size' value to look up (row).
    :param column_index: The column index (0=Size, 1=aes11, 2=aes12, etc.)
    :return: Latency value as float
    """
    if packet_size not in df["Size"].values:
        raise ValueError(f"Packet size {packet_size} not found in file.")

    if column_index < 0 or column_index >= len(df.columns):
        raise ValueError(f"Invalid column index {column_index}, must be 0-{len(df.columns)-1}.")

    row = df.loc[df["Size"] == packet_size]
    col_name = df.columns[column_index]
    return float(row[col_name].values[0])

def fillQueue(central_queue, working_queue1, working_queue2, t1, t2, idx1, idx2):
    # central queue  == datalist.
    # Packet[0] = length, packet[1] = relative_time, packet[2] = id, packet[3] = flow_id
    central_idx = 0
    working_queue1_count = len(working_queue1) - idx1
    working_queue2_count = len(working_queue2) - idx2
    max_time = max(t1 , t2)

    for packet in central_queue:
        if(packet[1] > max_time): # checking if the packet has arrived or not 
            break
        
        # packet[1] = time
        # packet[2] = packet id
        if(packet[2] % 2 == 0): # packet goes to less resource intensive hardware

            if(packet[1] > t1):
                if(working_queue1_count == 0):
                    t1 = packet[1]
                else:
                    break

            if(working_queue1_count == max_queue_size1): # return if working_queue1 is full  ( using len(working_queue1) - idx1 as idx1-1 is index till which packets have been processed)
                if(working_queue2_count == 0): #if working_queue2 is empty and working_queue1 is full then send the packet to  working_queue2
                    working_queue2.append(packet)
                    working_queue2_count+=1
                    central_idx+=1
                    if(t2 < packet[1]):
                        t2 = packet[1]

                break
            else:
                working_queue1.append(packet)
                working_queue1_count+=1


        else: # packet goes into more resource intensive hardware
            if(packet[1] > t2):
                if(working_queue2_count == 0):
                    t2 = packet[1]
                else:
                    break

            if(working_queue2_count == max_queue_size2): # return if working_queue2 is full
                if(working_queue1_count == 0):
                    working_queue1.append(packet)
                    central_idx+=1
                    working_queue1_count+=1
                    if(t1 < packet[1]):
                        t1 = packet[1]
                break
            else:
                working_queue2.append(packet)
                working_queue2_count+=1

        central_idx+=1

    del central_queue[:central_idx] # removing packets from central queue that have been scheduled

    return t1, t2


# correct
def process_both_queue(working_queue1, working_queue2, idx1, idx2, t1, t2, order_queue, algo1, algo2):
    working_queue1_len = len(working_queue1)
    working_queue2_len = len(working_queue2)

    while(idx1 < working_queue1_len and idx2 < working_queue2_len):    
        num_full_chunks = working_queue1[idx1][0] // 8000
        remaining = working_queue1[idx1][0] % 8000

        latency1 = num_full_chunks * get_latency(8000, algo1)
        if remaining > 0:
            latency1 += get_latency(remaining, algo1)

        num_full_chunks2 = working_queue2[idx2][0] // 8000
        remaining2 = working_queue2[idx2][0] % 8000

        latency2 = num_full_chunks2 * get_latency(8000, algo2)
        if remaining2 > 0:
            latency2 += get_latency(remaining2, algo2)
        
        if(latency2 < 0 or latency1 < 0):
            print("WRONG LATENCY")
        if t1 == t2:
            t1 += latency1
            t2 += latency2
            if latency1 <= latency2:
                order_queue.append([working_queue1[idx1], t1, algo1])
                order_queue.append([working_queue2[idx2], t2, algo2])
            else:
                order_queue.append([working_queue2[idx2], t2, algo2])
                order_queue.append([working_queue1[idx1], t1, algo1])
            idx1 += 1
            idx2 += 1
        elif t1 < t2:
            t1 += latency1
            order_queue.append([working_queue1[idx1], t1, algo1])  # t2 is already greater
            idx1 += 1
        else:
            t2 += latency2
            order_queue.append([working_queue2[idx2], t2, algo2])  # t1 is already greater
            idx2 += 1
    return idx1, idx2, t1, t2 

def process_single_hw_queue(working_queue , idx , t, order_queue, algo):
    packet = working_queue[idx]
    # latency = poly_func(packet[0])
    num_full_chunks = packet[0] // 8000
    remaining = packet[0] % 8000

    latency = num_full_chunks * get_latency(8000, algo)
    if remaining > 0:
        latency += get_latency(remaining, algo)

    idx+=1
    t+=latency
    order_queue.append([packet, t, algo])
    return idx , t


def min_time_to_complete(central_queue, algo1, algo2, packet_threshold, max_queue_size1, max_queue_size2, order_queue):
    # central queue , working_queue1, working_queue2 format = [  [packet size , arrival time stamp] , ........ ]
    idle_time1, idle_time2, t1, t2, idx1, idx2 = 0, 0, 0, 0, 0, 0
    working_queue1, working_queue2 = [], []
    # poly_func1 = get_interpolated_function(latencies, algo1)
    # poly_func2 = get_interpolated_function(latencies, algo2)
    
    # initially filling the queue
    t1, t2 = fillQueue(central_queue, working_queue1, working_queue2, t1, t2 , idx1, idx2)

    while(len(central_queue) != 0 or idx1 != len(working_queue1) or idx2 != len(working_queue2)):
        # print("Current length Wroking queue :",len(working_queue1)-idx1, len(working_queue2)-idx2, len(central_queue))
        idx1 , idx2 , t1, t2 = process_both_queue(working_queue1, working_queue2, idx1, idx2, t1, t2, order_queue,algo1, algo2)
        t1, t2 = fillQueue(central_queue, working_queue1, working_queue2, t1, t2 , idx1, idx2)

        #case 3 when all packets processed
        if(idx1 == len(working_queue1) and idx2 == len(working_queue2)):
            if(len(central_queue) == 0):
                break
            if(central_queue[0][1] > max(t1 , t2)):
                idle_time1 = t1 - central_queue[0][1]
                idle_time2 = t2 - central_queue[0][1]
                t1 = central_queue[0][1]
                t2 = central_queue[0][1]

            t1, t2 = fillQueue(central_queue, working_queue1, working_queue2, t1, t2 , idx1, idx2)


        elif(idx1 == len(working_queue1) or idx2 == len(working_queue2)):
            if(idx2 == len(working_queue2)): # working_queue2 is empty 
                idx1 , t1 = process_single_hw_queue(working_queue1, idx1, t1, order_queue, algo1)
            elif(idx1 == len(working_queue1)): # working_queue1 is empty
                idx2 , t2 = process_single_hw_queue(working_queue2 , idx2, t2, order_queue, algo2)
            t1, t2 = fillQueue(central_queue, working_queue1, working_queue2, t1, t2 , idx1, idx2)
            
    return [ working_queue1 , working_queue2 , t1 , t2 , t1-idle_time1, t2-idle_time2, order_queue]


packet_threshold = 256  # thresholds need to be set for variable size crypto hardwares.
algo1 = 4   # 1x
algo2 = 6   # 6x
max_queue_size1 = 1
max_queue_size2 = 1

data_list = []
with open('dataset.csv', 'r') as file:
    csv_reader = csv.DictReader(file)
    position_index = 0
    for i, row in enumerate(csv_reader):

        relative_time = float(row['Time']) * 1e6
        length = int(row['Length'])
        flow_id = int(row['Flow ID'])
        data_list.append([length, relative_time, i+1, flow_id, position_index])
        position_index+=1
        # Packet[0] = length, packet[1] = relative_time, packet[2] = id, packet[3] = flow_id


# assigning index to packets
for i in range(len(data_list)):
    if(i != 0):
        if(data_list[i][1] != data_list[i-1][1]):
            data_list[i][2] = i+1
        else:
            data_list[i][2] = data_list[i-1][2]

order_queue = []
data_len = len(data_list)
working_queue1 , working_queue2 , t1, t2, processingTime1, processingTime2, order_queue = min_time_to_complete(data_list, algo1, algo2, packet_threshold, max_queue_size1, max_queue_size2, order_queue)

# print("----------------- Final result ------------------")
print("t1 : " , t1 , "t2 :", t2)
print("processingTime1 : " , processingTime1 , "processingTime2 :", processingTime2)
print("len queue 1 : " , len(working_queue1) , "len queue 2 :", len(working_queue2))
# [ [ length, relative_time, packet id , flow_id ] , processing time ]

order_queue_csv = "order_queue.csv"
w1_csv = "working_queue1.csv"
w2_csv = "working_queue2.csv"

def wirte_list(csv_filename, data, hasProcessing_time):
    print(hasProcessing_time)
    with open(csv_filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        if(hasProcessing_time == False):
            writer.writerow(["Length", "Relative Time", "Packet ID", "Flow ID"])
            for element in data:
                vlaue = [element[0], element[1] , element[2], element[3]]
                writer.writerow(vlaue)
        else:
            writer.writerow(["Length","Position Index", "Relative Time", "Packet ID", "Flow ID", "Processing Time", "Hardware"])
            for packet_info, processing_time, hardware in data:
                vlaue = [packet_info[0],  packet_info[4], packet_info[1] , packet_info[2], packet_info[3]]
                writer.writerow(vlaue + [processing_time] + [hardware])

    print(f"Data saved to {csv_filename}")

wirte_list(order_queue_csv, order_queue, True)
wirte_list(w1_csv, working_queue1, False)
wirte_list(w2_csv, working_queue2, False)