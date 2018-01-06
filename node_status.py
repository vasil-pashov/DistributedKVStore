class NodeStatus:
    def __init__(self, status, incarnation):
        self.status = status
        self.incarnation = incarnation

    @classmethod
    def from_event(cls, event):
        return cls(event.event, event.incarnation)
