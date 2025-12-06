# Orca v2.0\! Classic Meets *Even More* Modern: A (Slightly) Pragmatic Learning-Based Congestion Control for the Internet

**This project is based on the findings from the SIGCOMM paper "Classic Meets Modern: A Pragmatic Learning-Based Congestion Control for the Internet" ([https://dl.acm.org/doi/pdf/10.1145/3387514.3405892](https://dl.acm.org/doi/pdf/10.1145/3387514.3405892)). This repository is forked from [https://github.com/Soheil-ab/Orca](https://github.com/Soheil-ab/Orca), which provided scaffolding for our modifications.**

### What We Have Added

This project extends the original Orca implementation with the following key improvements:

  * **Port to Modern Linux Kernel**: We ported the original Orca kernel patches from Linux 4.13 to **Linux Kernel 6.16**, enabling deployment on modern systems.
  * **Dynamic Algorithm Switching**: We implemented an in-kernel meta-controller that dynamically switches the underlying base congestion control algorithm (e.g., between TCP Cubic, Westwood, and BBR) based on real-time classification of the network environment (Wireless, Datacenter, High-BDP, etc.).
  * **Dynamic Monitoring Time Period (MTP)**: We replaced the fixed 20ms control loop with a dynamic MTP that adapts to the flow's Round-Trip Time (RTT). This synchronizes the agent's decision frequency with the network's feedback loop, improving stability on high-latency paths.
  * **Modified Reward Function**: We replaced the original linear reward function with a **logarithmic utility function** ($R = \alpha \log(\text{Throughput}) - \beta \text{Delay} - \gamma \text{Loss}$) to improve stability and fairness.

### Remaining Work

  * Usage of eBPF probes over the creation of the new networking module (DeepCC).
  * Training and finetuning an LSTM model over the current MLP.
  * Creating a three-stage model pipeline for MTP prediction, fallback algorithm prediction, and cwnd prediction.

The final project report and presentation slides can be found in `/documentation`. 


The Orca 1.0 README ([https://github.com/Soheil-ab/Orca](https://github.com/Soheil-ab/Orca)) is copied below.

-----------


# Orca v1.0

This release presents the source code and materials used for the experiments in our SIGCOMM'20 paper: "Classic Meets Modern: A Pragmatic Learning-Based Congestion Control for the Internet" (https://dl.acm.org/doi/abs/10.1145/3387514.3405892).

For the source code of our DeepCC plug-in reported in our IEEE JSAC'21 paper: "Wanna Make Your TCP Scheme Great for Cellular Networks? Let Machines Do It for You!", please checkout https://github.com/Soheil-ab/DeepCC.v1.0/ (The paper can be accessed here: https://ieeexplore.ieee.org/document/9252929)

Installation Guide
==================
    
### Installing Required Tools

Install Mahimahi (http://mahimahi.mit.edu/#getting)

	```sh  
	sudo apt-get install build-essential git debhelper autotools-dev dh-autoreconf iptables protobuf-compiler libprotobuf-dev pkg-config libssl-dev dnsmasq-base ssl-cert libxcb-present-dev libcairo2-dev libpango1.0-dev iproute2 apache2-dev apache2-bin iptables dnsmasq-base gnuplot iproute2 apache2-api-20120211 libwww-perl
	git clone https://github.com/ravinet/mahimahi 
	cd mahimahi
	./autogen.sh && ./configure && make
	sudo make install
	sudo sysctl -w net.ipv4.ip_forward=1
	```

### Orca's DRL Agent 

#### Prerequisites

- Python >= 3.4
- Tensorflow 1.14.0 

##### Create a virtul environment
```
mkdir ~/venv
sudo apt update
sudo apt install python3-pip
sudo pip3 install -U virtualenv
virtualenv ~/venv -p python3
```
If you change the path of the virtual environment, you need to change the source code accordingly. The source code assumes that virtual environment is set @ ~/venv .

##### Install packages
```
source ~/venv/bin/activate
pip install --upgrade pip
pip install gym
pip install tensorflow==1.14
pip install sysv_ipc
```

Verify Installation
```
python -c "import tensorflow as tf; tf.enable_eager_execution(); print(tf.reduce_sum(tf.random_normal([1000, 1000])))"
```

To deactivate venv
```
(venv) $ deactivate
```

### Patching Orca's Kernel: (Option 1)
Simplest option to install Orca's patched Kernels is to install the prepared debian packages:

```
cd linux
sudo dpkg -i linux-image*
sudo dpkg -i linux-header*
sudo reboot 
```

### Patching Orca's Kernel: (Option 2) 

If you have already done the option 1, skip this part! 
Another option is to compile your own kernel using the provided patch. You can use the instructions provided here to do that: https://github.com/Soheil-ab/C2TCP-IFIP/

The source code is available in linux folder (https://github.com/Soheil-ab/Orca/blob/master/linux/linux-4-13-1-orca-0521%2Bc2tcp.patch)

### Verify the new kernel
After installing the Orca's kernel and restarting your system, use the following command to make sure that system is using the new kernel:

```
uname -r
```

The output should be 4.13.1-0521*. If not, you need to bring the 4.13.1-0521* Kernel image on top of the grub list. For instance, you can use grub-customizer application. Install the grub-customizer using following:

```
sudo add-apt-repository ppa:danielrichter2007/grub-customizer
sudo apt-get update
sudo apt-get install grub-customizer
sudo grub-customizer
```

### Build Orca's Server-Client Apps
 To build the required applications, run the following:

```
./build.sh
```

 This release includes two versions: A standalone actor version and an actor-learner version.
In the Standalone actor version, no learner will be initiated. This can be usefull when you simply wanna test the current model over an emulated link. However, the actor-learner version requires a learner being initiated before any actor can be started. The second mode is usefull for learning a new/better model and also, it still can be used for performing a simple test over emulated links.

### Run a Sample Test with the standalone version using the provided learned model
  
```
./orca-standalone-emulation.sh 44444
``` 

### Run a Sample Test with the acotr-learner version using the provided learned model

```
./orca.sh 4 44444
``` 


Results will be generated automatically in rl-module/log/*
You can check out the summary of results at rl-module/log/sum-*

### Some notes on the training:
1. To distribute the actors over remote servers, you need to change "learner_ip" and "actor_ip" fields of the params.json file to the corresponding server IPs.
2. Start the learner first.
3. Set `remote:true` when using remote servers.
4. Set `num_actors: N`, N is the number of actors.

### Cellular traces:
To use traces avaialbe @ https://github.com/Soheil-ab/Cellular-Traces-NYC , copy them to the traces folder of the project.
