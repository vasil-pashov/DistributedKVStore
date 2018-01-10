from Queue import Queue


class Network:
    def __init__(self):
        print("Init network")
        self.nodes = {}
        self.connection = {}
        self.messages = {}

    def add_node(self, node, status):
        self.connection[node] = {n: self.nodes[n] for n in self.nodes}
        for n in self.nodes:
            self.connection[n][node] = status
        self.nodes[node] = status
        self.messages[node] = Queue()

    def send(self, source, desination, message):
        try:
            if (self.nodes[desination] != 'DOWN' and
                    self.connection[source][desination] != 'DOWN'):
                self.messages[desination].put((source, message))
        except KeyError:
            pass

    def receive(self, source):
        if source in self.nodes and self.nodes[source] != 'DOWN':
            return self.messages[source].get(block=True)

    # Globally disconect everyone sees is as dead
    def cut_off_node(self, node):
        if node in self.nodes:
            self.nodes[node] = 'DOWN'

    # Reverts cut_off_node but if connection[a][node] == 'DOWN'
    # a still cannot sett node
    def revive_node(self, node):
        if node in self.nodes:
            self.nodes[node] = 'UP'

    def disconnect(self, a, b):
        self.connection[a][b] = 'DOWN'

    def connect(self, a, b):
        self.connection[a][b] = 'UP'
