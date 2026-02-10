# FlexMesh
FlexMesh is a programmable, dynamically reconfigurable, and size-aware framework for 5G/6G cryptographic primitives.

## Publication
Aditya Peer, Rohan Sudhir Basugade, Siddhant, Neeraj Kumar Yadav, Agamdeep Singh, Praveen Tammana, Sumit Darak, Rinku Shah. Designing Size-aware Cryptographic Primitives for FPGA-based Accelerators.
In the proceedings of the CoNEXT 2026 Conference.

## Preparation

### Repository Structure
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

### Hardware
This directory contains variable-size cryptographic cores implementing the **Rocca-S** and **AES-GCM** algorithms.  
The **Scheduler** folder includes:

- **AES-RR Simulation**: Implementation of round-robin scheduling across small size AES-GCM cryptographic cores.
- **Simulation and Testbench**: Code used to evaluate the load balancer and calculate cycle counts.

### Software
This directory contains implementations of different scheduling policies, including:

- Round-robin
- Non-work-conserving
- FlexMesh
- FlexMesh with request-size prioritization

The **Scripts** folder contains code for evaluating processed workloads using performance metrics such as throughput, resource efficiency, power efficiency, and latency.

Users can run the code in the above folders by following the steps described under the **Compile** section.

```
queue_delay.ipynb
``` 


### Compile
In order to compile, use the build script provided above:
```
./common.sh [PROJECT_NAME] switch.p4 
```

### Window 1: switch control daemon
```
./run_switchd.sh -p [PROJECT_NAME]
```
After the bfshell is loaded in, configure the ports. In this example, we will use port 51 and 50 for packet ingress and egress.

```
ucli
pm

port-add 51/- 40G NONE
an-set 51/- 2 
port-enb 51/-

port-add 50/- 40G NONE
an-set 50/- 2 
port-enb 50/-

```
Use **show** command to verify the interfaces are up. If not up, then start to debug the physical links.After the interfaces are up, we can see the output in the given image like this.

![alt text](<show_up interface.png>)

Now **exit** from the **bf-sde.pm** .

### Enter in bfrt python environment
In barefoot CLI with the following command in the SDE:
In order to benefit from a lot of (python) features, we will do the following steps with the python runtime. This can be started within the bfshell:


```
bfrt
bfrt_python
```

Now enter the following commands, to do port bridging. All incomming packets to ingress port 44 are sent to egress port 176.
```
bfrt.l1switchCodel.pipe.SwitchIngress.t_l1_forwarding.clear() 
bfrt.l1switchCodel.pipe.SwitchIngress.t_l1_forwarding.add_with_send(ingress_port=44, egress_port=176)
bfrt.l1switchCodel.pipe.SwitchIngress.t_l1_forwarding.add_with_send(ingress_port=176, egress_port=44)
```
### Enable Mirroring Session
Enable mirroring session for generating mirrored packet which contain synchronized stateful values after end of codel_init and codel_update function.
Now enter the following commands in bfrt cli for enabling mirroring session.

```
mirror.cfg.entry_with_normal(sid=100,direction="BOTH",
session_enable=True,ucast_egress_port = 176,
ucast_egress_port_valid=1,max_pkt_len=100).push()

```

### Window 3: Enable Port Shaping
The corresponding egress port queue must be configured to shape the traffic in order to build up a queue. For that, in a third window, start the following script of the SDE,
We will use the run_pd_rpc.py script :

```
./run_pd_rpc.py
```
and enter the following commands:
```
tm.set_port_shaping_rate(44, False, 1600, 100000)
tm.enable_port_shaping(44)
```

