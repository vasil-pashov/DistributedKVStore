import binascii
import utils


class VirtualRing:
    def __init__(self, slots, nodes):
        self.slots = slots
        self.nodes = [(node, self.ring_position(node)) for node in nodes]
        self.nodes.sort(key=lambda p: p[1])

    # Given key find the node that has the same or
    # The next hash function (as number)
    # If no node has larger return the first
    def key_to_node(self, key):
        index = self._key_to_node_idx(key)
        return self.nodes[index][0]

    # Maps key to many nodes
    # Usefull for geting replica nodes
    def key_to_nodes(self, key, nodes_cnt):
        if len(self.nodes) <= nodes_cnt:
            return []  # [node for (node, _) in self.nodes]
        else:
            idx = self._key_to_node_idx(key)
            taken = 0
            res = []
            while taken < nodes_cnt:
                res.append(self.nodes[idx])
                taken += 1
                idx = idx + 1 if idx + 1 < len(self.nodes) else 0
            return res

    # At which index in self.nodes is the node responsible for key
    def _key_to_node_idx(self, key):
        ring_pos = self.ring_position(key)
        if ring_pos > self.nodes[-1][1]:
            return 0
        return utils.binary_search(self.nodes, ring_pos, lambda t: t[1])

    def add_node(self, name):
        ring_pos = self.ring_position(name)
        insert_idx = self._binary_search(ring_pos)
        self.nodes.insert(insert_idx, (name, ring_pos))

    # Find position in ring and using binnary search and delete node if it is
    # in the ring
    def remove_node(self, name):
        ring_pos = self.ring_position(name)
        node_pos = utils.binary_search(self.nodes, ring_pos, lambda t: t[1])
        if self.nodes[node_pos][0] == name:
            del self.nodes[node_pos]

    def ring_position(self, key):
        return self._hash(key) % self.slots

    def _hash(self, key):
        return binascii.crc32(key) % (1 << 32)
