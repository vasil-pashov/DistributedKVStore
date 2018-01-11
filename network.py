from Queue import Queue


class Network:
    def __init__(self):
        print("Init network")
        # Dict with key node name and value status of node and the
        # actual object, the object will be used to simulate HTTP kind
        # of request
        self.nodes = {}
        self.connection = {}
        self.messages = {}

    def add_node(self, node, status):
        self.connection[node.name] = {n: self.nodes[n] for n in self.nodes}
        for n in self.nodes:
            self.connection[n][node.name] = status
        self.nodes[node.name] = (status, node)
        self.messages[node.name] = Queue()

    def send(self, source, desination, message):
        try:
            if (self.nodes[desination][0] != 'DOWN' and
                    self.connection[source][desination] != 'DOWN'):
                self.messages[desination].put((source, message))
        except KeyError:
            pass

    def receive(self, source_name):
        if source_name in self.nodes and self.nodes[source_name][0] != 'DOWN':
            return self.messages[source_name].get(block=True)

    # Globally disconect everyone sees it as dead
    def cut_off_node(self, node_name):
        if node_name in self.nodes:
            self.nodes[node_name][0] = 'DOWN'

    # Reverts cut_off_node but if connection[a][node] == 'DOWN'
    # a still cannot sett node
    def revive_node(self, node_name):
        if node_name in self.nodes:
            self.nodes[node_name][0] = 'UP'

    def disconnect(self, a, b):
        self.connection[a][b] = 'DOWN'

    def connect(self, a, b):
        self.connection[a][b] = 'UP'

    # HTTP kind of request response message
    def request(self, source_name, dest_name, msg):
        return self.nodes[dest_name][1].request(source_name, msg)
