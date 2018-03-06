# Distributed key value store

**The source code is mostly done. The description/tutorial part is still in progres, but I'm doing the best I can to finish it. If anyone notices bugs, errors or has some idea on how to improve this, feel free to open issue, send pull request or just mail me so we can discuss it.**

This is my toy key value store. Optimizations like boom filters are omited. I'll try to explain the main components of such databese and how to implement them. To make this tutorial shorter I'll assume that you know what NoSQL database is as well as how distibuted systems function. The main components that we will need are:

* Network simulator (or real network)
* Database node
  * Membership protocol
  * Topology
  * Stabilization algorithm

In order to avoid avoid complications our databese nodes will run as threads started from [server2.py](https://github.com/vasil-pashov/DistributedKVStore/blob/master/server2.py) it will also provide some commands for testing and interaction with the system. All nodes will have acess to the network object, which will simulate real network, and all interactions between nodes will happen trough the network object (as would in the real world). Each node of the system must have corresponding config.json file in the confing folder. Each node in the system should be aware of which nodes are up/down, this will hapen trough the membership protocol. We will use the SWIM protocol for our system. Once we have component that can assure (not 100%, but close) that each node knows which nodes are up, we can think as the whole system as homogeneous system and request data according to our topology. The last piece of the puzzel is the stabilization algorithm, which will replicate data when node goes down and fill up with data new nodes that are joined or revived.

## Network simulator

This is needed in order to have more controlled environment. For this part we will simulate a network working with UDP and HTTP, if you have decided to use real network you can skip this it. The source code for this part is in [network.py](https://github.com/vasil-pashov/DistributedKVStore/blob/master/network.py). We will use statuses UP and DOWN to represent states of nodes. The connection is a table which describes conectivity between each two nodes. It can be used to make network disruption between two particular nodes. Nodes field is dictionary with 'global' node status (which means that if it is DOWN the node will act as disjoined from the whole network) and the node object itslef. It is used when we simulate HTTP, then we will call node functions directly from the object, it it is UP. In messages we keep thread safe message queue for each node in the network. This is how we simulate UDP. Each node will wait for something to be pushed on the queue and act on it. The functions are pretty straightforward, the most important are:

* **add_node** each node should be added with its name in order to join the network
* **send** is used for sending message (similar to UDP)
* **receive** is used for getting the first message in the node message queue. This is blocking call and in the real world it won't happen like this, so everyone should check the queue at given time interval, but this is easier for implementation.
* **request** in a way simulates HTTP request. It gets data directly from a node and returns the result to the caller

## Membership protocol

This is one of the most important parts. Having many nodes running simultaniously as one system makes the whole system dynamic, meaning nodes can go down or up, there may be network problems such as flooded network, network topology changes and so on. Becouse of this fact each node must know which are currently up and running and dynamically update it's knowledge of the system topology. This is where the membership protocol kiks in, it will help us make sure that each node knows which nodes are alive and propagate its knowledge to the other nodes in the system when it detects change. We will use the SWIM protocol, the full article, which I highly recommend reading can be found [here](https://pdfs.semanticscholar.org/8712/3307869ac84fc16122043a4a313604bd948f.pdf).

The protocol is composed of two parts failure detection and dessimetion protocol, as the names suppose failure detection is used to detect nodes going down while dessimetion protocol sreads the word to the othre nodes in the system. The source code can be found in [node.py](https://github.com/vasil-pashov/DistributedKVStore/blob/master/node.py) within the class SWIMNode.

This part of the systems uses UDP. We will use separate thread which will listen for new messages comming from the network. We start it using the **thread_receive()** function.

### Failure detection

Some high level description of the failure detection part looks like this:

```
failure_detection()
  ping_random_node()
  if not node_responded:
    indirect_ping_same_node()
    if not indirect_ping_respond()
      suspect_node()
  failure_detection()
```
We will run this failure detection in separate thread and repeat it each **__protocol_time** seconds. The thread is strarted in the **thread_ping_loop()**. In **nodes_status** we will keep every node in the system alongside with it status. At each iteration we will select random node and send *ping* message to it. If node is pinged it should send *ack* message back. This means that the node is alive and running. If after pinging node we don't get *ack* after **__ping_timeout** seconds we assume that there is some network problem between these two particular nodes, so we try to do indirect pinging. Indirect pinging is a procedure, in which we select randomly another node and send him *ping_req* message, meaning we ask it to send ping message on our behalf. The selected node sends *ping* request to our target and waits for *ack*. If it recieves *ack* message it redirects back to us the *ack*. If we still do not receive *ack* message we change the status of the originally pinged node to *suspected*. At this point there are two options there is some network problem (conjested network, all ping packets are lost) or the node is really dead, so we start a timer. If at the end of that timer we still don't get anything (now we wait for any kind of messages including those from dessimation part) we change the status of the node to DOWN. In order to keep track of all *ack* messages we use **_ack** for *ack* messages that we have received directly from the pinged node and **__ping_req_ack** for *ack* messages that we have received after *ping_req*.

One last detail we shall discuss is how to randomly select nodes for pinging. If choose nodes randomly, we can have delays of finding dead nodes. This can happen if we, by chance don't pick them. Happily, this is avoidable with simple techique. Initially we shuffle nodes randomly and proceed pinging then in round-robin fashion, keeping track which nodes were pinged In our case **_ping_idx** is the index of the last pinged node. When we reach the end of the nodes list we shuffle them again.

### Dessimation protocol

