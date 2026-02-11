# FlexMesh
FlexMesh is a programmable, dynamically reconfigurable, and size-aware framework for 5G/6G cryptographic primitives.

## Publication
Aditya Peer, Rohan Sudhir Basugade, Siddhant, Neeraj Kumar Yadav, Agamdeep Singh, Praveen Tammana, Sumit Darak, Rinku Shah. Designing Size-aware Cryptographic Primitives for FPGA-based Accelerators.
In the proceedings of the CoNEXT 2026 Conference.

## Preparation

### Repository Structure
The repository contains the implementation of variable-size cryptographic cores of the Rocca-S and AES-GCM algorithms under different scheduling policies.
```
├── Hardware 
     └── Cryptographic Cores
           └── Rocca-S
           └── AES-GCM
     └── Scheduler
          └── AES-RR Simulation
          └── Simulation
          └── Testbench
├── Software
|    └── Scheduler Simulation
|    └── Scripts 
```
## Description

### Software
This directory contains implementations of different scheduling policies, including:

- Round-robin
- Non-work-conserving
- FlexMesh
- FlexMesh with request-size prioritization

The **Scripts** folder contains code for evaluating processed workloads using performance metrics such as throughput, resource efficiency, power efficiency, and latency.

Users can run the code in the above folders by following the steps described under the **Compile** section.

**Input datasets**

The 5G workload datasets required for the scheduler simulation can be downloaded from the following Google Drive link:

5G Dataset (Google Drive):https://drive.google.com/drive/folders/11Gax78Uj_NIWJVP69aA1KMCxUWoTMXX_?usp=drive_link

After downloading the files, users must provide two input paths while running the simulation:

- Path to the 5G dataset CSV file

- Path to the packet latency file (packet_latencies.txt)

```
python3 ./software/scheduling_policies.py
``` 

### Hardware
This directory contains variable-size cryptographic cores implementing the **Rocca-S** and **AES-GCM** algorithms.  
The **Scheduler** folder includes:

- **AES-RR Simulation**: Implementation of round-robin scheduling across small size AES-GCM cryptographic cores.
- **Simulation and Testbench**: Code used to evaluate the load balancer and calculate cycle counts.

