from network import Network
from swim_node import SWIMNode
from db_node import DBNode
import random
import sys

network = Network()

nodes = {}

def init():
    configs = ['config/config.json', 'config/config1.json', 'config/config2.json']
    for config in configs:
        new_node = DBNode(config, network)
        nodes[new_node.name] = new_node
        network.add_node(new_node, 'UP')
    for node in nodes:
        nodes[node].start()


init()

while True:
    action = raw_input()
    action = action.split()

    if action[0] == 'netstat':
        print(network.connection)
    elif action[0] == 'alive':
        for node_name in nodes:
            node = nodes[node_name]
            print("Node {} knows about {} and has ring {}".format(
                node_name, node.nodes, node.ring.nodes))
    elif action[0] == 'die':
        sys.exit()
    elif action[0] == 'revive':
        network.revive_node(action[1])
    elif action[0] == 'cut_off':
        network.cut_off_node(action[1])
    elif action[0] == 'disconnect':
        print("DISCONNECTING")
        network.disconnect(action[1], action[2])
    elif action[0] == 'shutdown':
        nodes[action[1]].shutdown()
    elif action[0] == 'add':
        new_node = DBNode(action[1], network)
        nodes[new_node.name] = new_node
        network.add_node(new_node, action[2])
        new_node.start()
    elif action[0] == 'write':
        name, node = random.choice(list(nodes.items()))
        node.write(action[1], action[2])
    elif action[0] == 'read':
        name, node = random.choice(list(nodes.items()))
        print(node.read(action[1]))
