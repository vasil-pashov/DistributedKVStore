from swim_node import SWIMNode
from topology import VirtualRing


class DBNode(SWIMNode):
    def __init__(self, config_file, network, slots=2**10):
        super(DBNode, self).__init__(config_file, network)
        self.ring = VirtualRing(slots, self.nodes)

    def write(self, key, value):
        write_nodes = self.ring.key_to_nodes(key)
        for node in write_nodes:
            self.network.send()

    def read(self, key, value):
        pass
