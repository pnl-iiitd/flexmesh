#include <iostream>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <map>
#include <cmath>
#include <algorithm> 
#include <limits>    
#include <iostream> // For input/output operations (cout, cerr)
#include <fstream>  // For file stream operations (ifstream)
#include <vector>   // For using std::vector to store data
#include <string>   // For using std::string
#include <sstream>  // For string stream operations (stringstream)
#include <utility>  // For std::pair
#include <algorithm> // For std::min
#include <iomanip>
#include <bits/stdc++.h>
using namespace std;


std::vector<double> readLatencyColumn(const std::string& filename, int target_latency_column_index) {
    std::vector<double> column_data;
    std::ifstream infile(filename);
    if (!infile.is_open()) {
        std::cerr << "Error: Could not open file " << filename << std::endl;
        return column_data;
    }

    std::string header_line;
    std::getline(infile, header_line); // Skip header

    std::string line;
    int line_number = 1; // For more precise error messages

    while (std::getline(infile, line)) {
        line_number++;
        std::stringstream ss(line);
        std::string segment;
        
        bool target_column_value_added_for_this_line = false;
        bool conversion_error_for_target_column_this_line = false;
        int current_latency_column_idx = 0; // 0-indexed for latency columns

        // 1. Read and discard packet size (first segment)
        if (std::getline(ss, segment, ',')) {
            try {
                std::stoi(segment); // Read but discard packet size
            } catch (const std::invalid_argument& e) {
                std::cerr << "Error (L" << line_number << "): Converting packet size to int in line: \"" << line << "\" - " << e.what() << std::endl;
                continue; // Skip to next line
            } catch (const std::out_of_range& e) {
                 std::cerr << "Error (L" << line_number << "): Packet size out of range in line: \"" << line << "\" - " << e.what() << std::endl;
                continue; // Skip to next line
            }
        } else {
            // Line might be empty or only contain a packet size without a comma
            if (!line.empty()) { // Avoid warning for completely empty lines if any
                 std::cerr << "Warning (L" << line_number << "): Line too short, cannot parse packet size: \"" << line << "\"" << std::endl;
            }
            continue; // Skip to next line
        }

        // 2. Loop through latency value segments to find the target column
        while (std::getline(ss, segment, ',')) {
            if (current_latency_column_idx == target_latency_column_index) {
                try {
                    double latency_value = std::stod(segment);
                    column_data.push_back(latency_value);
                    target_column_value_added_for_this_line = true;
                } catch (const std::invalid_argument& e) {
                    std::cerr << "Error (L" << line_number << "): Converting latency value to double for column " << target_latency_column_index
                              << " in line: \"" << line << "\". Segment: '" << segment << "'. Error: " << e.what() << std::endl;
                    conversion_error_for_target_column_this_line = true;
                } catch (const std::out_of_range& e) {
                     std::cerr << "Error (L" << line_number << "): Latency value out of range for column " << target_latency_column_index
                               << " in line: \"" << line << "\". Segment: '" << segment << "'. Error: " << e.what() << std::endl;
                    conversion_error_for_target_column_this_line = true;
                }
                break; // Found target column (or attempt to parse it), move to next line
            }
            current_latency_column_idx++;
        }

        // 3. Issue warning if target column was not found and no conversion error was reported for it
        if (!target_column_value_added_for_this_line && !conversion_error_for_target_column_this_line) {
            // This means the loop finished (ran out of segments) before current_latency_column_idx reached target_latency_column_index
            // or it reached it but std::getline failed for that segment.
             std::cerr << "Warning (L" << line_number << "): Line does not have data for latency column index " << target_latency_column_index
                       << " or segment is empty. Line: \"" << line << "\"" << std::endl;
        }
    }

    infile.close();
    return column_data;
}


struct Packet {
    int length;
    double relative_time; 
    int packet_id;
    int flow_id;
};


struct CompletedPacket {
    Packet packet_info;
    double finish_time;
    int hardware; 
};



int find_packet(const std::vector<Packet>& hardware_queue, double current_time, double threshold) {
    
    int optimal_packet_idx = 0;
    int min_flow_id = hardware_queue[0].flow_id;
    int max_pkt_length=0;
    map<int,vector<int>>eligible_packets;
    vector<Packet>first_256_packets;
    
    // Capture 256 packets from the hardware queue.
    for(int j=0; j<hardware_queue.size(); j++){
            if(j<256){
                first_256_packets.push_back(hardware_queue[j]);
            }else{
                if(j==256){
                    break;
                }
            }
    }

    for(int i=0; i<first_256_packets.size(); i++){
        // Filter out the elgible packets from the first 256 packets.
        double wait_time = current_time - first_256_packets[i].relative_time;
        if(wait_time > threshold){  // Packet's aging time
            if(first_256_packets[i].length > max_pkt_length){
                max_pkt_length = first_256_packets[i].length;
                optimal_packet_idx = i;
            }
        }
    }
    
    return optimal_packet_idx;
}




void process_single_queue_wc(std::vector<Packet>& queue1, std::vector<Packet>& queue2, double& t1, double& t2) {
    int empty_queue_id = 0; 

    if (queue1.empty() && !queue2.empty()) {
        empty_queue_id = 1;
    } else if (queue2.empty() && !queue1.empty()) {
        empty_queue_id = 2;
    } else {
        return;
    }

    if (empty_queue_id == 1) { // queue1 is empty, queue2 has packets
        if (t1 < queue2[0].relative_time) {
            t1 = queue2[0].relative_time; // Hardware 1 waits for packet from queue 2 to arrive
        }
        queue1.push_back(queue2[0]);
        queue2.erase(queue2.begin());
    } else { 
        if (t2 < queue1[0].relative_time) {
            t2 = queue1[0].relative_time; 
        }
        queue2.push_back(queue1[0]);
        queue1.erase(queue1.begin());
    }
}



void classifier(std::vector<Packet>& central_queue, int packet_threshold,
                std::vector<Packet>& queue1, std::vector<Packet>& queue2,
                double& t1, double& t2, int max_size_queue1, int max_size_queue2,
                std::vector<std::pair<int, Packet>>& dropped_packets) {

    int central_idx = 0;
    for (int i = 0; i < central_queue.size(); i++) {
        const auto& packet = central_queue[i];
        if (packet.relative_time > std::max(t1, t2)) {
            break;
        }

        if(packet.length <= packet_threshold) { 
            if (packet.relative_time > t1) {
                if(queue1.size() == 0){
                    t1 = packet.relative_time;
                }
                else{
                    break;
                }  
            }
            if(queue1.size() >= max_size_queue1) { 
                dropped_packets.push_back({1, packet}); 
                central_idx+=1;
            } else {
                queue1.push_back(packet);
                central_idx+=1;
            }

        } else { 
            if (packet.relative_time > t2) {
                if(queue2.size() == 0){
                    t2 = packet.relative_time;
                }
                else{
                    break;
                }  
            }
            if (queue2.size() >= max_size_queue2) { // Check if queue2 is full
                dropped_packets.push_back({2, packet}); // 2 indicates queue2 dropped
                central_idx+=1;
            } else {
                queue2.push_back(packet);
                central_idx+=1;
            }
        }
    }

    central_queue.erase(central_queue.begin(), central_queue.begin() + central_idx);
}


void process_both_queue(std::vector<Packet>& working_queue1, std::vector<Packet>& working_queue2,
                       double& t1, double& t2,
                       std::vector<CompletedPacket>& order_queue,
                       const std::vector<double>& poly_coeffs1, const std::vector<double>& poly_coeffs2,
                       double threshold1,
                       double threshold2) {

    // Continue processing as long as both queues are non-empty
    while (!working_queue1.empty() && !working_queue2.empty()) {
        int optimal_packet1_idx = find_packet(working_queue1, t1, threshold1);
        int optimal_packet2_idx = find_packet(working_queue2, t2, threshold2);
        Packet packet1 = working_queue1[optimal_packet1_idx];
        Packet packet2 = working_queue2[optimal_packet2_idx];
        
        double latency1 = poly_coeffs1[packet1.length % 8000] +
                          (packet1.length/ 8000) * poly_coeffs1[8000]; // Pass 8000.0 for clarity

        double latency2 = poly_coeffs2[packet2.length % 8000] +
                          (packet2.length / 8000) * poly_coeffs2[8000];
        
        
        // std::cout<<"Ploy coeff 2 "<<poly_coeffs1[packet2.length % 8000]<<" "<<"Above 8000 :"<<(packet2.length/ 8000) * poly_coeffs2[8000]<<endl;    
        
        if (latency1 < 0 || latency2 < 0){
             std::cerr << "WARNING: Negative latency calculated!" << std::endl;
        }
        
        double updated_time1 = t1 + latency1;
        double updated_time2 = t2 + latency2;

        if(t1 == t2){
            t1 = updated_time1;
            t2 = updated_time2;
            if (latency1 <= latency2) {
                order_queue.push_back({packet1, t1, 1});
                order_queue.push_back({packet2, t2, 2});
                working_queue1.erase(working_queue1.begin() + optimal_packet1_idx);
                working_queue2.erase(working_queue2.begin() + optimal_packet2_idx);
            } 
            else {
                order_queue.push_back({packet2, t2, 2});
                order_queue.push_back({packet1, t1, 1});
                working_queue1.erase(working_queue1.begin() + optimal_packet1_idx);
                working_queue2.erase(working_queue2.begin() + optimal_packet2_idx);
            }
        } else if (t1 < t2) {
            t1 = updated_time1;
            order_queue.push_back({packet1, t1, 1});
            working_queue1.erase(working_queue1.begin() + optimal_packet1_idx);
        } else if (t2 < t1) {
            t2 = updated_time2;
            order_queue.push_back({packet2, t2, 2});
            working_queue2.erase(working_queue2.begin() + optimal_packet2_idx);
        }
    }
}


void process_single_queue(std::vector<Packet>& working_queue, double &t,
                           std::vector<CompletedPacket>& order_queue,
                           const std::vector<double>& poly_coeffs, double threshold, int hardware) {

    int optimal_idx = find_packet(working_queue, t, threshold);
    Packet packet = working_queue[optimal_idx];
    double latency = poly_coeffs[packet.length % 8000] +
                          (packet.length / 8000) * poly_coeffs[8000]; // Pass 8000.0 for clarity
     if (latency < 0) {
         std::cerr << "WARNING: Negative latency calculated in single queue!" << std::endl;
     }
    t += latency;
    order_queue.push_back({packet, t, hardware});
    working_queue.erase(working_queue.begin() + optimal_idx);
}


std::tuple<double, double, double, double>
min_time_to_complete(std::vector<Packet> central_queue,
                     int algo1_idx, int algo2_idx, int packet_threshold,
                     int max_queue_size1, int max_queue_size2,
                     std::vector<Packet>& working_queue1,
                     std::vector<Packet>& working_queue2,
                     std::vector<CompletedPacket>& order_queue,
                     int data_change,
                     int new_algo1_idx, int new_algo2_idx,
                     double threshold1, double threshold2, int new_packet_threshold) {

    double idle_time1 = 0.0, idle_time2 = 0.0;
    double t1 = 0.0, t2 = 0.0; 
    std::vector<std::pair<int, Packet>> dropped_packets; // To store dropped packets
    string file_path = "packet_latencies.txt";
    vector<double> poly_coeffs1 = readLatencyColumn(file_path, algo1_idx);
    vector<double> poly_coeffs2 = readLatencyColumn(file_path, algo2_idx);
    classifier(central_queue, packet_threshold, working_queue1, working_queue2, t1, t2, max_queue_size1, max_queue_size2, dropped_packets);

    while (!central_queue.empty() || !working_queue1.empty() || !working_queue2.empty()) {

        process_both_queue(working_queue1, working_queue2, t1, t2, order_queue, poly_coeffs1, poly_coeffs2, threshold1, threshold2);
        classifier(central_queue, packet_threshold, working_queue1, working_queue2, t1, t2, max_queue_size1, max_queue_size2, dropped_packets);

        if (working_queue1.empty() && working_queue2.empty()) {
            // std::cout << "Both working queues are empty, checking central queue..." << std::endl;
            if (central_queue.empty()) {
                break;
            }
            double next_arrival_time = central_queue[0].relative_time;
            if (t1 < next_arrival_time && t2 < next_arrival_time) {
                idle_time1 += t1 - next_arrival_time; // Using t1 *after* the reset, still seems wrong
                idle_time2 += t2 - next_arrival_time; // Using t2 *after* the reset
                t1 = next_arrival_time; 
                t2 = next_arrival_time;
                classifier(central_queue, packet_threshold, working_queue1, working_queue2, t1, t2, max_queue_size1, max_queue_size2, dropped_packets);
            }
        }
        else if (working_queue1.empty() || working_queue2.empty()) {
            // std::cout << "One of the working queues is empty, processing the other..." << std::endl;
                if (working_queue1.size() == 1 && working_queue2.empty()) {
                    process_single_queue(working_queue1, t1, order_queue, poly_coeffs1, threshold1, 1);
                } else if (working_queue1.empty() && working_queue2.size() == 1) {
                    process_single_queue(working_queue2, t2, order_queue, poly_coeffs2, threshold2, 2);
                }
                if((working_queue1.empty() && working_queue2.size() > 1)  || (working_queue2.empty() && working_queue1.size() > 1)){
                    process_single_queue_wc(working_queue1, working_queue2, t1, t2);
                } 
                classifier(central_queue, packet_threshold, working_queue1, working_queue2, t1, t2, max_queue_size1, max_queue_size2, dropped_packets);
            }
    }

    double final_processing_time1 = t1 - idle_time1;
    double final_processing_time2 = t2 - idle_time2;
    return {t1, t2, final_processing_time1, final_processing_time2};
}


std::vector<Packet> read_csv(const std::string& filename) {
    std::vector<Packet> data_list;
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error opening file: " << filename << std::endl;
        return data_list; // Return empty vector on error
    }

    std::string line;
    std::getline(file, line);

    int packet_counter = 1; 

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string segment;
        std::vector<std::string> segments;

        while (std::getline(ss, segment, ',')) {
            segments.push_back(segment);
        }

        if (segments.size() >= 4) { 
            try {
                int length = std::stoi(segments[5]);
                double relative_time = std::stod(segments[2]) * 1e6;
                int flow_id = std::stoi(segments[6]); 
                int packet_id;
                if (!data_list.empty() && data_list.back().relative_time == relative_time) {
                    packet_id = data_list.back().packet_id;
                }
                else{
                    packet_id = packet_counter;
                }
                packet_counter++;
                data_list.push_back({length, relative_time, packet_id, flow_id});
            } catch (const std::invalid_argument& e) {
                std::cerr << "Invalid number in row: " << line << " - " << e.what() << std::endl;
            } catch (const std::out_of_range& e) {
                std::cerr << "Number out of range in row: " << line << " - " << e.what() << std::endl;
            }
        } else {
             std::cerr << "Skipping row due to insufficient columns: " << line << std::endl;
        }
    }

    file.close();
    return data_list;
}

// Write completed packet data to a CSV file
void write_completed_packets_csv(const std::string& filename, const std::vector<CompletedPacket>& data) {
    std::ofstream file(filename);
     if (!file.is_open()) {
        std::cerr << "Error opening file for writing: " << filename << std::endl;
        return;
    }

    file << "Length,Relative Time,Packet ID,Flow ID,Processing Time,Hardware" << std::endl;
    // file << "Length" << std::endl;

    for (const auto& completed_packet : data) {
        file << std::fixed << std::setprecision(6)<< completed_packet.packet_info.length << ","
             << std::fixed << std::setprecision(6) << completed_packet.packet_info.relative_time << ","
             << std::fixed << std::setprecision(6) << completed_packet.packet_info.packet_id << ","
             << std::fixed << std::setprecision(6) << completed_packet.packet_info.flow_id << ","
             << std::fixed << std::setprecision(6) << completed_packet.finish_time << ","
             << std::fixed << std::setprecision(6) << completed_packet.hardware << std::endl;
    }

    // for (const auto& completed_packet : data) {
    //     file << completed_packet.packet_info.length<<std::endl;
    // }

    file.close();
    std::cout << "Completed packet data saved to " << filename << std::endl;
}



int main() {

    int algo1_idx = 4;  // 3x M
    int algo2_idx = 5;  // 6x L


    int packet_threshold = 1024;
    int max_queue_size1 = INT_MAX;
    int max_queue_size2 = INT_MAX;
    int data_change = 100000000;
    std::string csv_filepath =  "/home/iiitd/Aditya/Mmtc_Dataset/clipped_8k_mmtc_avg_854_12G_1.6.csv";
    std::vector<Packet> central_queue = read_csv(csv_filepath);


    std::vector<CompletedPacket> order_queue;
    std::vector<Packet> working_queue1; 
    std::vector<Packet> working_queue2; 

    int new_algo2_idx = 2;
    int new_algo1_idx = 1;
    
    double threshold1 = 1; // 1 us time interval
    double threshold2 = 1; // 1 us time interval
    int new_packet_threshold = 1024;
    auto results = min_time_to_complete(central_queue, algo1_idx, algo2_idx,
                                        packet_threshold, max_queue_size1, max_queue_size2,
                                        working_queue1, working_queue2, order_queue, data_change, new_algo1_idx, new_algo2_idx,
                                        threshold1, threshold2, new_packet_threshold);
    // write_completed_packets_csv("../amp_load_balancer_1x_6x/output_500_user_request_length_max_inter_packet_time.csv", order_queue);
    write_completed_packets_csv("output.csv", order_queue);

    return 0;
}