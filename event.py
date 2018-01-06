class Event:
    def __init__(self, event, node, incarnation=None):
        self.event = event
        self.node = node
        self.incarnation = incarnation

    def to_map(self):
        res = {'event': self.event, 'node': self.node}
        if self.incarnation:
            res['incarnation'] = self.incarnation
        return res

    @classmethod
    def from_map(cls, m):
        if 'incarnation' in m:
            return cls(m['event'], m['node'], m['incarnation'])
        else:
            return cls(m['event'], m['node'])
