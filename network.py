from Queue import Queue


class Network:
    def __init__(self):
        print("Init network")
        self.nodes = {}
        self.messages = {}

    def add_node(self, node, status):
        self.nodes[node] = status
        self.messages[node] = Queue()

    def send(self, source, desination, message):
        if desination in self.nodes and self.nodes[desination] != 'DOWN':
            self.messages[desination].put((source, message))

    def receive(self, source):
        if source in self.nodes and self.nodes[source] != 'DOWN':
            return self.messages[source].get(block=True)

    def kill_node(self, node):
        if node in self.nodes:
            self.nodes[node] = 'DOWN'

    def revive_node(self, node):
        if node in self.nodes:
            self.nodes[node] = 'UP'
