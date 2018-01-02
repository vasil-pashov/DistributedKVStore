import json
import requests
import random
import collections
import urlparse


class NodeStatus:
    def __init__(self, status, incarnation):
        self.status = status
        self.incarnation = incarnation


class Event:
    def __init__(self, event, node, incarnation=None):
        self.event = event
        self.node = node
        self.incarnation = incarnation

    def to_map(self):
        res = {'event': self.event_type, 'node': self.node}
        if self.incarnation:
            res['incarnation'] = self.incarnation
        return res


class Node:
    def __init__(self, config_file):
        config_data = json.load(open(config_file))
        random.shuffle(config_data['nodes'])
        self.incarnation = 0
        self.events_len = float(config_data['events_len'])
        self.events = collections.deque(maxlen=self.events_len)
        self.nodes = config_data['nodes']
        self.ping_req_cnt = config_data['ping_req_cnt']
        self.ping_timeout = float(config_data['ping_timeout'])
        self.node_status = {node: NodeStatus('UP', 0) for node in self.nodes}
        self.ping_idx = 0

    def ping(self):
        if self.ping_idx >= len(self.nodes):
            self.ping_idx = 0
        target_node = self.nodes[self.ping_idx]
        target_address = urlparse.urljoin(target_node, "ping")
        ping_received = False
        try:
            params = {'events': self._prepare_events()}
            resp = requests.get(
                target_address, params=params, timeout=self.ping_timeout)
            self.node_status[target_node].status = "UP"
            ping_received = True
        except requests.exceptions.RequestException:
            print("Cannot ping: {}".format(target_address))
            if self._indirect_ping(target_node):
                ping_received = True
        self.ping_idx += 1
        if not ping_received and self.node_status[target_node].status == "UP":
            self.node_status[target_node].status = "SUSPECT"
            self.events.append(Event("suspect", target_node))
        if ping_received and self.node_status[target_node].status != "UP":
            self.node_status[target_node].status = "UP"
            self.events.append(Event("joined", target_node))

    def _indirect_ping(self, target):
        mediator_nodes = self._get_indirect_pingers()
        ping_received = False
        print("Initiating indirect_ping using: {}".format(mediator_nodes))
        for node in mediator_nodes:
            try:
                address = urlparse.urljoin(node, "ping_req")
                params = {'target': target, 'events': self._prepare_events()}
                resp = requests.get(address, params=params,
                                    timeout=self.ping_timeout)
                if resp.json()['type'] == 'ACK':
                    ping_received = True
            except requests.exceptions.RequestException:
                pass
        return ping_received

    def _get_indirect_pingers(self):
        res = []
        alive_nodes = self._alive_nodes()
        if len(alive_nodes) < self.ping_req_cnt:
            return alive_nodes
        else:
            while len(alive_nodes) < self.ping_req_cnt:
                node = random.choice(alive_nodes)
                if node not in res and node != self.address:
                    res.append(node)
        return res

    def process_ping_req(self, target):
        target_address = urlparse.urljoin(target, "ping")
        try:
            resp = requests.get(target_address, timeout=self.ping_timeout)
            return resp.json()
        except requests.exceptions.RequestException:
            return {'type': 'ACK_FAILED', 'events': self._prepare_events()}

    def _alive_nodes(self):
        statuses = self.node_status
        return [node for node in statuses if statuses[node].status != "DOWN"]

    def _process_events(self, events):

    def _prepare_events(self):
        return [event.to_map() for event in self.events]
