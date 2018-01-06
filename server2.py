from network import Network
from node import Node
import sys

network = Network()
a = Node('config.json', network)
b = Node('config2.json', network)

network.add_node(a.name, 'UP')
network.add_node(b.name, 'UP')
a.thread_receive()
b.thread_receive()
a.thread_ping_loop()
b.thread_ping_loop()

while True:
    action = raw_input("What to do>>> ")
    if action == 'die':
        sys.exit()
    elif action == 'alive':
        print(a.nodes)
        print(b.nodes)
    elif action == 'kill':
        print(a.name)
        network.kill_node(a.name)
