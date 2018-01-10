from network import Network
from swim_node import SWIMNode
import sys

network = Network()

nodes = {}

# a = Node('config.json', network)
# b = Node('config2.json', network)

# network.add_node(a.name, 'UP')
# network.add_node(b.name, 'UP')
# a.thread_receive()
# b.thread_receive()
# a.thread_ping_loop()
# b.thread_ping_loop()

# for conf in ['config.json', 'config1.json', 'config2.json']:
#     new_node = Node(conf, network)
#     nodes[new_node.name] = new_node
#     network.add_node(new_node.name, 'UP')
#     new_node.thread_receive()
#     new_node.thread_ping_loop()

while True:
    action = raw_input()
    action = action.split()

    if action[0] == 'netstat':
        print(network.connection)
    elif action[0] == 'alive':
        for node_name in nodes:
            node = nodes[node_name]
            print("Node {} knows about {}".format(node_name, node.nodes))
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
        new_node = SWIMNode(action[1], network)
        nodes[new_node.name] = new_node
        network.add_node(new_node.name, action[2])
        new_node.thread_receive()
        new_node.thread_ping_loop()
