import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
def get_threshold(csv_path):

    df  = pd.read_csv(csv_path)
    flow_list = df.values.tolist()

    # Dictionary to store unique Flow ID's values.
    flow_ids = {}
    cnt=0
    for i in range(0,len(flow_list)):
        # print(flow_list[i])
        if flow_list[i][6] not in flow_ids:
            # temp_list = []
            # temp_list.append(flow_list[i][1])
            flow_ids[flow_list[i][6]] = [flow_list[i][1] * 1000000]
        else:
            flow_ids[flow_list[i][6]].append(flow_list[i][1] * 1000000)



        # print("Flow ID :",flow_list[i][3])

    
    flow_diff_inter_time = {}
    for flow_id, time_list in flow_ids.items():
        if flow_id not in flow_diff_inter_time:
            diff_list = []
            for i in range(len(time_list)-1):
                diff_list.append(time_list[i+1] - time_list[i])
            flow_diff_inter_time[flow_id] = diff_list
    

    all_intervals = []
    for time_list in flow_diff_inter_time.values():
        all_intervals.extend(time_list)

    all_intervals_sorted = np.sort(all_intervals)

    print("Max interval value :",max(all_intervals_sorted))
    print("Average inter packet time value :",np.average(all_intervals_sorted))

    cdf = np.arange(1, len(all_intervals_sorted) + 1) / len(all_intervals_sorted)

    # Plot CDF
    plt.plot(all_intervals_sorted, cdf)
    plt.xlabel('Time Interval')
    plt.ylabel('CDF')
    plt.title('CDF of All Time Intervals')
    # plt.xlim(0, 0.05)
    plt.savefig("cdf_intervals")
    plt.grid(True)
    plt.show()


    

    
    # # print(flow_diff_inter_time_avg[79045])

    # flow_diff_avg ={}
    # for flow_id, data_list in flow_diff_inter_time.items():
    #     if flow_id not in flow_diff_avg:
    #         flow_diff_avg[flow_id] = np.mean(data_list)
    
    # # print(flow_diff_avg[79045])
    
    # # Average threshold across all average flow time
    # avg_values = flow_diff_avg.values()
    # threshold_avg = sum(avg_values)/len(avg_values)

    # print("Threshold Value :",threshold_avg)



        

    # print(flow_ids[79045])



def main():

    csv_path = '/home/iiitd/Aditya/Mawi_Dataset/clipped_Datasets_MAWI/Mawi-Dataset-1_1.6M.csv'
    get_threshold(csv_path)


if __name__ == "__main__":
    main()
    