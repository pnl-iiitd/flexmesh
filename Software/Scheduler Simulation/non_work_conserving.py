import csv
import numpy as np

def find_packet_latency_poly(poly_func, val):
    return poly_func(val)

def get_interpolated_function(latencies, algo ):
    algo1_latency = np.array([v[algo] for v in latencies.values()])
    packet_sizes = np.array(list(latencies.keys()))
    coeffs = np.polyfit(packet_sizes, algo1_latency, 3)
    poly_func_1 = np.poly1d(coeffs)
    return poly_func_1

    
def check_holb(central_queue, packet_threshold, fullQueue, central_idx, t1, t2, blocking_timestamp_in):
    blocking_timestamp = blocking_timestamp_in
    if(fillQueue == 1):
        curr_timestamp = t2
    else:
        curr_timestamp = t1
         
    for i in range(central_idx+1, len(central_queue)):
        if(central_queue[i][1] > curr_timestamp): # checking if the packet has arrived or not 
            break
        if(fullQueue == 1):
            if(central_queue[i][0] > packet_threshold and central_queue[i][1] <= t2):
                central_queue[central_idx][4] = 1
                if(blocking_timestamp != 0):
                    print("WRONG SHOULD BE ZERO FOR QUEUE 1 AS HOLB")
                blocking_timestamp = t1
                break
        else:
            if(central_queue[i][0] <= packet_threshold and central_queue[i][1] <= t1):
                if(blocking_timestamp != 0):
                    print("WRONG SHOULD BE ZERO FOR QUEUE 2 AS HOLB")
                central_queue[central_idx][4] = 1

                blocking_timestamp = t2
                break

    return blocking_timestamp


def fillQueue(central_queue, working_queue1, working_queue2, t1, t2, idx1, idx2, working_queue1_total_holb, working_queue2_total_holb, blocking_timestamp_in):
    central_idx = 0  
    working_queue1_count = len(working_queue1) - idx1  
    working_queue2_count = len(working_queue2) - idx2  
    max_time = max(t1, t2)
    blocking_timestamp = blocking_timestamp_in
    for packet in central_queue:
        if packet[1] > max_time:  # checking if the packet has arrived or not 
            break

        if packet[0] <= packet_threshold: # packet goes to less resource intensive hardware
            if(packet[1] > t1):
                if(working_queue1_count == 0):
                    t1 = packet[1]
                break

            # if ((working_queue1_count == max_queue_size1) ): # check holb as queue1 is full and central queue first packet is classifier for queue1 
            #     if(working_queue2_count == 0 and blocking_timestamp == 0):
            #         pass
                    # blocking_timestamp = check_holb(central_queue, packet_threshold, 1, central_idx, t1 , t2, blocking_timestamp)
                # break

            working_queue1.append(packet) # add packet to working queue
            if(packet[4] == 1):
                working_queue1_total_holb.append((t1 - blocking_timestamp))
                blocking_timestamp = 0
            working_queue1_count += 1

        else:  # packet goes to more resource intensive hardware
            if(packet[1] > t2):
                if(working_queue2_count == 0):
                    t2 = packet[1]
                break

            # if (working_queue2_count == max_queue_size2 ):  
                # if(working_queue1_count == 0 and blocking_timestamp == 0):
                    # pass
                    # blocking_timestamp = check_holb(central_queue, packet_threshold, 2, central_idx, t1, t2,  blocking_timestamp)
                # break

            working_queue2.append(packet)
            if(packet[4] == 1):
                working_queue2_total_holb.append((t2 - blocking_timestamp))
                blocking_timestamp = 0
            working_queue2_count += 1

        central_idx += 1


    del central_queue[:central_idx]

    return t1, t2, blocking_timestamp


def process_both_queue(working_queue1, working_queue2, idx1, idx2, t1, t2, order_queue, poly_func1, poly_func2):
    working_queue1_len = len(working_queue1)
    working_queue2_len = len(working_queue2)

    while(idx1 < working_queue1_len and idx2 < working_queue2_len):
        latency1 = poly_func1(working_queue1[idx1][0])
        latency2 = poly_func2( working_queue2[idx2][0])

        if t1 == t2:
            t1 += latency1
            t2 += latency2
            if latency1 <= latency2:
                order_queue.append([working_queue1[idx1], t1])
                order_queue.append([working_queue2[idx2], t2])
            else:
                order_queue.append([working_queue2[idx2], t2])
                order_queue.append([working_queue1[idx1], t1])
            idx1 += 1
            idx2 += 1
        elif t1 < t2:
            t1 += latency1
            order_queue.append([working_queue1[idx1], t1])  # t2 is already greater
            idx1 += 1
        else:
            t2 += latency2
            order_queue.append([working_queue2[idx2], t2])  # t1 is already greater
            idx2 += 1

    return idx1, idx2, t1, t2  # Only return necessary values

def process_single_queue(queue, idx, t, algo, order_queue, poly_func):
    packet = queue[idx]
    latency = poly_func(packet[0])
    t += latency
    order_queue.append([packet, t])
    idx += 1

    return idx, t


def min_time_to_complete(central_queue, latencies, algo1, algo2, packet_threshold, max_queue_size1, max_queue_size2, working_queue1_total_holb, working_queue2_total_holb, order_queue):
    # central queue , working_queue1, working_queue2 format = [  [packet size , arrival time stamp] , ........ ]
    idle_time1, idle_time2, t1, t2, idx1 , idx2 = 0, 0, 0, 0, 0, 0
    working_queue1 = []
    working_queue2 = []
    poly_func1 = get_interpolated_function(latencies, algo1)
    poly_func2 = get_interpolated_function(latencies, algo2)
    blocking_timestamp = 0


    # initially filling the queue
    t1, t2, blocking_timestamp = fillQueue(central_queue, working_queue1, working_queue2, t1, t2 , idx1, idx2, working_queue1_total_holb, working_queue2_total_holb, blocking_timestamp)

    while(len(central_queue) != 0 or idx1 != len(working_queue1) or idx2 != len(working_queue2)):
        # print(len(working_queue1)-idx1, len(working_queue2)-idx2, len(central_queue))
        idx1 , idx2 , t1, t2 = process_both_queue(working_queue1, working_queue2, idx1 , idx2, t1, t2, order_queue, poly_func1, poly_func2)
        t1, t2, blocking_timestamp = fillQueue(central_queue, working_queue1, working_queue2, t1, t2, idx1, idx2, working_queue1_total_holb, working_queue2_total_holb, blocking_timestamp)

        #case 3 when all packets processed
        if(idx1 == len(working_queue1) and idx2 == len(working_queue2)):
            if(len(central_queue) == 0):
                break
            if(central_queue[0][1] > max(t1 , t2)):
                idle_time1 = t1 - central_queue[0][1]
                idle_time2 = t2 - central_queue[0][1]
                t1 = central_queue[0][1]
                t2 = central_queue[0][1]

            t1, t2, blocking_timestamp = fillQueue(central_queue, working_queue1, working_queue2, t1, t2, idx1, idx2, working_queue1_total_holb, working_queue2_total_holb, blocking_timestamp)

    
        elif(idx1 == len(working_queue1) or idx2 == len(working_queue2)):
            if(idx2 == len(working_queue2)): # working_queue2 is empty 
                idx1 , t1 = process_single_queue(working_queue1, idx1, t1, algo1, order_queue, poly_func1)
            elif(idx1 == len(working_queue1)): # working_queue1 is empty
                idx2 , t2 = process_single_queue(working_queue2 , idx2, t2, algo2, order_queue, poly_func2)
        
            t1, t2, blocking_timestamp = fillQueue(central_queue, working_queue1, working_queue2, t1, t2, idx1, idx2, working_queue1_total_holb, working_queue2_total_holb, blocking_timestamp)

    return [ working_queue1 , working_queue2 , t1 , t2 , t1-idle_time1, t2-idle_time2,  working_queue1_total_holb, working_queue2_total_holb, order_queue]






algo_dict = {"1_1" : 0, "1_3" : 1, "1_6" : 2}


packet_threshold = 256
algo1 = 0   # 1x
algo2 = 2   # 6x
max_queue_size1 = 1
max_queue_size2 = 1

data_list = []
with open('Dataset.csv', 'r') as file:

    csv_reader = csv.DictReader(file)
    for i, row in enumerate(csv_reader):
        # if(i>=1600000):
            # break
        relative_time = float(row['Relative Time']) * 1e6
        length = int(row['Length (Bytes)'])
        flow_id = int(row['Flow ID'])
        data_list.append([length, relative_time, i+1, flow_id , 0])



# assigning index to packets
for i in range(len(data_list)):
    if(i != 0):
        if(data_list[i][1] != data_list[i-1][1]):
            data_list[i][2] = i+1
        else:
            data_list[i][2] = data_list[i-1][2]


order_queue = []
working_queue1_total_holb = []
working_queue2_total_holb = []
working_queue1 , working_queue2 , t1, t2, processingTime1, processingTime2,  working_queue1_total_holb, working_queue2_total_holb, order_queue = min_time_to_complete(data_list, latencies_rocca, algo1, algo2, packet_threshold, max_queue_size1, max_queue_size2, working_queue1_total_holb, working_queue2_total_holb, order_queue)
print("----------------- Final result ------------------")
print("processingTime1 : " , processingTime1 , "processingTime2 :", processingTime2)
print("len queue 1 : " , len(working_queue1) , "len queue 2 :", len(working_queue2))
# print("working_queue1_total_holb : " , working_queue1_total_holb , "working_queue2_total_holb :", working_queue2_total_holb)
# [ [ length, relative_time, packet id , flow_id ] , processing time ]

def write_list_to_file(data_list, filename):
    with open(filename, 'w') as file:
        for item in data_list:
            file.write(str(item) + '\n')  


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
            writer.writerow(["Length", "Relative Time", "Packet ID", "Flow ID", "Processing Time"])
            for packet_info, processing_time in data:
                vlaue = [packet_info[0], packet_info[1] , packet_info[2], packet_info[3]]
                writer.writerow(vlaue + [processing_time])


    print(f"Data saved to {csv_filename}")

wirte_list(order_queue_csv, order_queue, True)
wirte_list(w1_csv, working_queue1, False)
wirte_list(w2_csv, working_queue2, False)
write_list_to_file(working_queue1_total_holb, "holb1_delays.txt")
write_list_to_file(working_queue2_total_holb, "holb2_delays.txt")