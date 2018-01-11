import json
import random
import collections
from threading import Thread, Lock, Timer
from time import sleep
from node_status import NodeStatus
from event import Event


class SWIMNode(object):
    def __init__(self, config_file, network):
        self.__read_config(config_file)
        self.__lock = Lock()
        self.__ack_lock = Lock()
        self.__ping_ack_lock = Lock()
        self.__incarnation = 0
        self.events = collections.deque(maxlen=self.__events_len)
        self.node_status = {node: NodeStatus('up', 0) for node in self.nodes}
        self.__ping_idx = 0
        self._network = network
        self._ack = {}
        self.__shutdowned = False
        self._ping_req_ack = {}

    def __read_config(self, config_file):
        config_data = json.load(open(config_file))
        random.shuffle(config_data['nodes'])
        self.nodes = config_data['nodes']
        self.name = config_data['name']
        self.__events_len = float(config_data['events_len'])
        self.__ping_req_cnt = config_data['ping_req_cnt']
        self.__ping_timeout = float(config_data['ping_timeout'])
        self.__protocol_time = float(config_data['protocol_time'])

    def shutdown(self):
        self.__shutdowned = True

    def thread_ping_loop(self):
        ping_t = Thread(target=self._ping_loop)
        ping_t.setDaemon(True)
        ping_t.start()
        return ping_t

    def thread_receive(self):
        rec_t = Thread(target=self._receive_loop)
        rec_t.setDaemon(True)
        rec_t.start()
        return rec_t

    def _receive_loop(self):
        while not self.__shutdowned:
            (src, msg) = self._network.receive(self.name)
            print("Node {} has message from {}. Message {}".format(
                self.name, src, msg['type']))
            self._process_message(src, msg)

    # Ping nodes using round robin rotation
    def _ping_loop(self):
        while not self.__shutdowned:
            target = self._get_ping_target()
            if target:
                self._ack = {}
                self._ping(target)
                Timer(self.__ping_timeout, self._indirect_ping, (target,)).start()
                self.__ping_idx += 1
            sleep(self.__protocol_time)

    def _get_ping_target(self):
        self.__lock.acquire()
        if self.__ping_idx >= len(self.nodes):
            self.__ping_idx = 0
            random.shuffle(self.nodes)
        target = None if len(self.nodes) == 0 else self.nodes[self.__ping_idx]
        self.__lock.release()
        return target

    def _ping(self, target):
        print("{} pinging node {}".format(self.name, target))
        self._send(target, 'ping')
        self._ack = {target: False}

    # Select intermediate nodes and try pinging trough them
    def _indirect_ping(self, target):
        if not self._ack[target]:
            mediator_nodes = self._get_indirect_pingers(target)
            print("{} is indirect pinging {} trough {}".format(
                self.name, target, mediator_nodes))
            self.__ack_lock.acquire()
            for node in mediator_nodes:
                self._ack[node] = False
                self._send(node, 'ping_req', {'target': target})
            self.__ack_lock.release()
            Timer(self.__ping_timeout, self._suspect, (target,)).start()

    def _get_indirect_pingers(self, target):
        res = []
        self.__lock.acquire()
        possible_pingers = [node for node in self.nodes if node != target]
        self.__lock.release()
        if len(possible_pingers) < self.__ping_req_cnt:
            return possible_pingers
        else:
            while len(res) < self.__ping_req_cnt:
                node = random.choice(possible_pingers)
                if node not in res:
                    res.append(node)
        return res

    # If no ack received from target or intermediate nodes declare node
    # to be suspected after some interval see if it responded and kill if not
    def _suspect(self, target):
        if not self._ack_received():
            print("{} suspects node {}".format(self.name, target))
            self.__lock.acquire()
            if target in self.node_status:
                if self.node_status[target].status == 'up':
                    incarnation = self.node_status[target].incarnation
                    self.node_status[target].status = 'suspected'
                    self.events.append(Event('suspect', target, incarnation))
            self.__lock.release()
            Timer(self.__ping_timeout, self._check_suspected, (target, )).start()
        else:
            print("Indirect ping successful")

    # If node is suspected and there was no signal from it declare it dead
    def _check_suspected(self, target):
        print("{} checks if suspected node {} is dead".format(self.name, target))
        self.__lock.acquire()
        if (target in self.node_status and
                self.node_status[target].status == 'suspected'):
            print("{} says node {} is dead".format(self.name, target))
            incarnation = self.node_status[target].incarnation
            self.events.append(Event('dead', target, incarnation))
            self.nodes.remove(target)
            del self.node_status[target]
        self.__lock.release()

    def _remove_node(self, node):
        self.__lock.acquire()
        if node in self.nodes:
            self.nodes.remove(node)
        if node in self.node_status:
            del self.node_status[node]
        self.__lock.release()

    def _process_message(self, src, msg):
        if msg['type'] == 'ping':
            self._process_events(msg['events'])
            if src not in self.node_status:
                self._handle_node_join(src)
                self.events.append(Event('join', src, 0))
            self._send(src, 'ack')
        if msg['type'] == 'ack':
            self._ack_ping(src)
            self._process_events(msg['events'])
        elif msg['type'] == 'ping_req':
            target = msg['target']
            self._execute_ping_req(target)
            Timer(self.__ping_timeout, self._ping_req_ack_receive,
                  (src, target)).start()
            self._process_events(msg['events'])
        elif msg['type'] == 'empty':
            self._process_events(msg['events'])

    def _ack_ping(self, src):
        self.__ack_lock.acquire()
        # ack direct ping
        if src in self._ack:
            self._ack[src] = True
        self.__ack_lock.release()
        # if receive ack from suspected node -> unsuspect it
        try:
            self.node_status[src].status = 'alive'
        except KeyError:
            pass
        # when this node is intermediate in ping_req and
        # gets ack from target
        if src in self._ping_req_ack:
            self._ping_req_ack[src] = True

    # check if ack is received when the sender is intermediate node 
    def _ping_req_ack_receive(self, src, target):
        ack_received = False
        try:
            ack_received = self._ping_req_ack[target]
        except KeyError:
            pass
        if ack_received:
            print("Ping ack from {} to {} successful".format(src, target))
            msg_type = 'ack'
        else:
            msg_type = 'empty'
        self._send(src, msg_type)
        self._ping_req_ack = {}

    # checks if ack from target or intermediate is received
    def _ack_received(self):
        self.__ack_lock.acquire()
        for node in self._ack:
            if self._ack[node]:
                self.__ack_lock.release()
                return True
        self.__ack_lock.release()
        return False

    # Send ping on behalf of some node
    def _execute_ping_req(self, target):
        self._ping_req_ack[target] = False
        self._send(target, 'ping')

    def _send(self, target, msg_type, opt_params={}):
        params = {'type': msg_type, 'events': self._prepare_events()}
        params.update(opt_params)
        self._network.send(self.name, target, params)

    def _process_events(self, events):
        for event in events:
            self._process_event(event)

    def _process_event(self, event):
        event = Event.from_map(event)
        current_status = self.__get_member_status(event.node)
        if not current_status:
            return
        if event.event == 'alive':
            if (current_status.status == 'suspect' and
                    event.incarnation > current_status.incarnation):
                self.events.append(event)
                new_status = NodeStatus.from_event(event)
                self.__set_member_status(event.node, new_status)
            elif (current_status == 'alive' and
                    event.incarnation > current_status.incarnation):
                self.events.append(event)
                new_status = NodeStatus.from_event(event)
                self.__set_member_status(event.node, new_status)
        elif event.event == 'suspect':
            if event.node == self.name:
                self.__incarnation += 1
                self.events.append(
                    Event('alive', self.name, self.__incarnation))
            elif (current_status.status == 'suspect' and
                    event.incarnation > current_status.incarnation):
                self.events.append(event)
                new_status = NodeStatus.from_event(event)
                self.__set_member_status(event.node, new_status)
            elif (current_status.status == 'alive' and
                    event.incarnation >= current_status.incarnation):
                self.events.append(event)
                new_status = NodeStatus.from_event(event)
                self.__set_member_status(event.node, new_status)
        elif event.event == 'dead':
            if event.node == self.name:
                self.__incarnation += 1
                self.events.append(
                    Event('alive', self.name, self.__incarnation))
            else:
                self.events.append(event)
                self._handle_node_down(event.node)
        elif (event.event == 'join' and self.name != event.node and
                event.node not in self.node_status):
            self.events.append(event)
            self._handle_node_join(self, event.node)

    def _handle_node_down(self, node):
        self._remove_node(node)

    def __set_member_status(self, node, status):
        self.__lock.acquire()
        if node in self.node_status:
            self.node_status[node] = status
        self.__lock.release

    def __get_member_status(self, node):
        try:
            return self.node_status[node]
        except KeyError:
            return None

    def _handle_node_join(self, node):
        self.__lock.acquire()
        if node not in self.node_status:
            self.node_status[node] = NodeStatus('up', 0)
            self.nodes.insert(random.randint(0, len(self.nodes)), node)
        self.__lock.release()

    def _prepare_events(self):
        return [event.to_map() for event in self.events]
