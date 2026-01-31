import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import statistics
import csv
import os
import seaborn as sns
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.patheffects as path_effects

core_files = {

    # '3x_6x_FlexMeshp_256_1us' : '/home/iiitd/Aditya/Plot_RoccaS/Asymmetric_Cores/Mmtc_Dataset_updated_12G/rocca_3x_6x/amp_load_balancer/output_1us_256.csv',
    '3x_6x_FlexMesh_MMTC':'/home/iiitd/Aditya/Plot_RoccaS/Asymmetric_Cores/Mmtc_Dataset_updated_12G/rocca_3x_6x/classifier_scheduler_rocca_1x_6x/order_queue_classifier_scheduler_rocca_11_14.csv',
    # '3x_6x_classifier': '/home/iiitd/Aditya/Plot_RoccaS/Asymmetric_Cores/Mmtc_Dataset_updated_12G/rocca_3x_6x/classifier_rocca_1x_6x/order_queue_classifier_rocca_11_14.csv',
    # '3x_6x_rr':'/home/iiitd/Aditya/Plot_RoccaS/Asymmetric_Cores/Mmtc_Dataset_updated_12G/rocca_3x_6x/round_robin_rocca_1x_6x/order_queue_round_robin_rocca_11_12_old.csv',

    
}

max_packet_sizes = []
def compute_ooo_for_single_flow_across_buckets(arrival_order, processing_order, bucket, max_count_ooo_packets):

    # To append the ooo memory of each flow for first 500 ms bucket
    # Currently calculating the ooo memory for each time buckets
    prev_sum = []
    sum_of_packet_sizes_with_out_of_order = 0
    packet_size = []
    for pkt in bucket:
        packet_size.append(pkt[0])   # Append Packet Sizes
    
    out_of_order_count = 0

    count=0
    find_min = 0
    check = False
    for arrival_index,process_index in zip(arrival_order,processing_order):
        # print("Arrival index :",arrival_index,"Process index :",process_index)


        if (arrival_index == process_index and check == True): # To check even the arrival and processed packet are same order, but the previous minimum packet has not found yet, it will be stored in the buffer, before going to the application.
            out_of_order_count += 1
            sum_of_packet_sizes_with_out_of_order+=packet_size[count]
            # print("Out of order packet :",sum_of_packet_sizes_with_out_of_order, "Packet ID :",process_index)
        
        if (arrival_index != process_index):
            if check == False: # To check Has Out of Order packet
                find_min = arrival_index
                # print("First Out of order packet :",process_index)
                check = True  # Flag set to true
            if find_min !=process_index:
                out_of_order_count += 1

                # print("Out of order packet ID :",process_index)
                sum_of_packet_sizes_with_out_of_order+=packet_size[count] 
                # print("Out of order packet :",sum_of_packet_sizes_with_out_of_order, "Packet ID :",process_index)
        
        if find_min == process_index:
            if(sum_of_packet_sizes_with_out_of_order!=0):
                prev_sum.append(sum_of_packet_sizes_with_out_of_order)
                if(max_count_ooo_packets[0]<out_of_order_count):
                    max_count_ooo_packets[0]=out_of_order_count
                    # print("Max OOO Packets updated :",max_count_ooo_packets)
                # print("Prev sum append :",prev_sum)
                # print("Break, Now packets are in order")
            else:
                prev_sum.append(0)
            sum_of_packet_sizes_with_out_of_order=0
            out_of_order_count = 0  # Reset the out of order count when in order packet found
            check = False
        
        count+=1


    total_packets = len(arrival_order)
    # max_packet_sizes.append(max(prev_sum))
    # print("Max OOO Packets updated :",max_count_ooo_packets)
    
    # return (out_of_order_count / total_packets) * 
    # return the list of if it has ooo memory or not across time buckets

    return max(prev_sum) if prev_sum else 0# Return the maximum bucket sum of out of order packets for that flow id


def out_of_order_percentage(packets,max_count_ooo_packets, relative_time_list_flow,ooo_memory_flow, flow_id):
    # arrival_index = {packet: i for i, packet in enumerate(arrival_order)}
 
    time_bucket = 200000 # 200 microseconds
    # To capture sum of packet sizes when out of order packets are present in time buckets
    time_bucket_list = []
    # To divide packets into time bucket chunks
    current_bucket = [] 
    # print("Relative Time List Flow :",relative_time_list_flow)
    current_time_limit = relative_time_list_flow[0] + time_bucket
    
    for pkt, rel_time in zip(packets, relative_time_list_flow):
        if rel_time <= current_time_limit:
            current_bucket.append([pkt[0], pkt[2]])
            # print("Current bucket appended pkt :",pkt)
        else:
            time_bucket_list.append(current_bucket)
            # print("Ended Bucket :",time_bucket_list)
            current_bucket = [[pkt[0], pkt[2]]]
            current_time_limit = rel_time + time_bucket

    if current_bucket:
        time_bucket_list.append(current_bucket)

    # Compute the arrival and processing order within each time bucket
    # make ooo memroy dictionalry for flow ids across time buckets
    arrival_order = []
    processing_order = []
    for bucket in time_bucket_list:
        processing_order = [pkt[1] for pkt in bucket]
        arrival_order = sorted([pkt[1] for pkt in bucket])
        ooo_mem_bucket = compute_ooo_for_single_flow_across_buckets(arrival_order, processing_order, bucket, max_count_ooo_packets)
        # print("Max Bucket Sum of OOO Packets for this flow id :",ooo_mem_bucket, "Flow ID :",flow_id)
        ooo_memory_flow[flow_id].append(ooo_mem_bucket)
    
    # Print the ooo memory flow dictionary which contains flow ids and their corresponding ooo memory across time buckets

    # for flow_id_key, ooo_mem_values in ooo_memory_flow.items():
    #     # Print if there are any non-zero ooo memory values
    #     if len(ooo_mem_values)!=0:
    #         print(f"Flow ID: {flow_id_key}, OOO Memory across buckets: {ooo_mem_values}")
    
    return ooo_memory_flow

def process_packets(flow_dict, algo, log_file_path,max_count_ooo_packets, ooo_memory_flow):
    avg_out_of_order = 0
    valid_flows_ooo, total_flows = 0, 0
    ooo_list = []
    # print("Flow IDs in the flow dict :",flow_dict.keys())
    # print("Total number of flows to process :",len(flow_dict))
    # print("Flow items :",flow_dict.items())
    sum_of_packets = 0
    for flow_id, packets in flow_dict.items():
        
        # print("Processing Flow ID :",flow_id)
        # print("Packets in this flow :",len(packets))
        # sum_of_packets += len(packets)
        arrival_relative_time_list_flow = [p[1] for p in packets]
        # print("Arrival Relative Time List Flow :",arrival_relative_time_list_flow)
        ooo_memory_flow = out_of_order_percentage(packets,max_count_ooo_packets, arrival_relative_time_list_flow,ooo_memory_flow, flow_id)

        # total_flows += 1
    # print("Total Packets across all flows :",sum_of_packets)

    return ooo_memory_flow

def ooo_metric(order_queue, algo, log_file_path,max_count_ooo_packets):
    
    flow_dict = {}
    ooo_memory_flow = {}
    for packet in order_queue:
        flow_id = packet[3]
        # print("Flow ID 1:",flow_id)
        if flow_id not in flow_dict:
            flow_dict[flow_id] = []
        flow_dict[flow_id].append(packet)
        if flow_id not in ooo_memory_flow:
            ooo_memory_flow[flow_id] = []
    
    # print("Minimum Flow ID :",min(flow_dict.keys()))
    # Divide packets into flows based on flow_id
    ooo_memory_flow_result= process_packets(flow_dict, algo, log_file_path,max_count_ooo_packets, ooo_memory_flow)

    ##

    
    
    return ooo_memory_flow_result

if __name__ == "__main__":
    log_file_path_1 = "ooo_log.txt"
    
    # Updated labels for box plots (same as bar charts)
    config_to_label = {
        '1x_1x': r'$\mathbf{RR_{SMP}(1X,1X)}$',
        '2x_2x': r'$\mathbf{RR_{SMP}(2X,2X)}$',
        '4x_4x': r'$\mathbf{RR_{SMP}(4X,4X)}$',
        '1x_2x_rr': r'$\mathbf{RR_{AMP}(1X,2X)}$',
        '1x_4x_rr': r'$\mathbf{RR_{AMP}(1X,4X)}$',
        '1x_2x_c': r'$\mathbf{MQ\_nWC_{AMP}(1X,2X)}$',
        '1x_4x_c': r'$\mathbf{MQ\_nWC_{AMP}(1X,4X)}$',
        '1x_2x_cs': r'$\mathbf{MQ_{AMP}(1X,2X)}$',
        '1x_4x_cs': r'$\mathbf{MQ_{AMP}(1X,4X)}$',
        '1x_2x_amp': r'$\mathbf{MQp_{AMP}(1X,2X)}$',
        '1x_4x_amp': r'$\mathbf{MQp_{AMP}(1X,4X)}$'
    }
        
    # Initialize data containers
    latency_data = []
    ooo_data = []
    
    # Calculate packet latency for each core configuration.
    for core_config, file_path in core_files.items():
        try:
            print("Core Config :",core_config)
            df =  pd.read_csv(file_path)
            prev_sum = []  # Initialize empty prev_sum
            max_count_ooo_packets = [0] # Initialize max count of ooo packets
            # df2 = pd.read_csv(file_path) # Compute latency
            
            # # Calculate packet latency
            # df2 = packet_latency(df2) # Compute latency
            
            # df2['core_type'] = core_config  # Add core type column
            # latency_data.append(df2)  # Append to list
            
            # Log statistics to file of every core in single file.
            # log_file_path = f"packet_latency_log.txt"  # Log file path
            # algo = core_config  # Extract algo from the filename
            # list_box_plot_values(df2['processing_delay'], log_file_path, algo, 'Packet Latency')

            # Calculate Out of Order percentage.
            algo = core_config  # Extract algo from the filename
            # Convert the order queue to a list of packets
            order_queue = df.values.tolist()  # Convert DataFrame to list of lists
            
            # Give the order queue list to the function to calculate out of order percentage.
            ooo_memory_result = ooo_metric(order_queue, algo, log_file_path_1,max_count_ooo_packets)
            for flow_id_key, ooo_mem_values in ooo_memory_result.items():
                # Print if there are any non-zero ooo memory values
                if len(ooo_mem_values)!=0:
                    print(f"Flow ID: {flow_id_key}, OOO Memory across buckets: {ooo_mem_values}")
    
            # print("OOO Memory Result :",ooo_memory_result)

            # df3 = pd.DataFrame(ooo_list, columns=['Out of Order Percentage'])
            # df3['core_type'] = core_config  # Add core type column
            # ooo_data.append(df3)  # Append to list

        except Exception as e:
            pass
            # print(f"Error processing {core_config}: {e}")

        # print("Prev sum :",prev_sum)
        # print("Max OOO Packet bytes :",max(prev_sum),"bytes") # Sum
        # print("Total sum bytes :",sum(prev_sum), "bytes") # Sum
        # print("Max OOO Packets :",max_count_ooo_packets[0]) # Count
        print("\n")
        # print("Max OOO Packet bytes :",max(max_packet_sizes)) # Sum

