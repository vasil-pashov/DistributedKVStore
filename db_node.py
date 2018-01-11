from swim_node import SWIMNode
from topology import VirtualRing
from time import time
from threading import Timer
import json
import os


class DataObject:
    def __init__(self, data, timestamp):
        self.data = data
        self.timestamp = timestamp


class DBNode(SWIMNode):
    def __init__(self, config_file, network, slots=2**10):
        super(DBNode, self).__init__(config_file, network)
        self.ring = VirtualRing(slots, self.nodes)
        self.__read_config(config_file)
        self.__store = {}
        self.__read_persistent_storage()
        Timer(60, self.__dump).start()

    def start(self):
        ping_thread = self.thread_ping_loop()
        rec_thread = self.thread_receive()
        return (ping_thread, rec_thread)

    def request(self, req_source, msg):
        if msg['type'] == 'read':
            try:
                value = self.__store[msg['key']]
                return {'status': 'ok', 'value': value}
            except KeyError:
                return {'status': 'error'}

    def __read_config(self, config_file):
        config_data = json.load(open(config_file))
        self.__replicas = int(config_data['replicas'])

    def write(self, key, value):
        write_nodes = self.ring.key_to_nodes(key, self.__replicas)
        if write_nodes == []:
            pass  # No nodes
        else:
            timestamp = time()
            for node in write_nodes:
                if node != self.nodes:
                    self._network.send(self.name, 'write',
                                       (key, value, timestamp))
                else:
                    self._write(key, value, timestamp)

    def _process_message(self, src, msg):
        super(DBNode, self)._process_message(src, msg)
        if msg['type'] == 'read_repair':
            try:
                self.__store[msg['key']] = msg['value']
            except KeyError:
                pass
        elif msg['type'] == 'stabilize':
            self.__store[msg['key']] = msg['value']

    def read(self, key):
        read_nodes = self.ring.key_to_nodes(key, self.__replicas)
        results = self.__get_read_results(key, read_nodes)
        last_write = max(results, key=lambda t: t[1].timestamp)[1]
        for res in results:
            if res[1].timestamp != last_write.timestamp:
                payload = {'type': 'read_repair',
                           'key': key, 'value': last_write}
                self._network.send(self.name, res[0], payload)
        return last_write

    def __get_read_results(self, key, read_nodes):
        res = []
        payload = {'type': 'read', 'key': key}
        for node in read_nodes:
            response = self._network.request(self.name, node, payload)
            if response['type'] == 'ok':
                res.append((node, response['value']))
        return res

    def _handle_node_down(self, node):
        super(DBNode, self)._handle_node_down(node)
        self.ring.remove_node(node)
        self.__stabilize()

    def _handle_node_join(self, node):
        super(DBNode, self)._handle_node_join(node)
        self.ring.add_node(node)
        self.__stabilize()

    # Stabilization is done on node join or leave
    # For each key if it has no longer place it is deleted
    # And message to write it is send to the new owners
    def __stabilize(self):
        for key in self.__store:
            nodes = self.ring.key_to_nodes(key, self.__replicas)
            if self.name not in nodes:
                for node in nodes:
                    payload = {'type': 'stablize', 'key': key,
                               'value': self.__store[key]}
                    self._network.send(self.name, node, payload)
                del self.__store[key]

    def _write(self, key, value, timestamp):
        self.__store[key] = DataObject(value, timestamp)

    def _read(self, key, value):
        try:
            data = self.__store[key]
            return (True, data)
        except KeyError:
            return (False, "")

    def __read_persistent_storage(self):
        data_file = "{}_data.json".format(self.name)
        if os.path.isfile(data_file):
            with open(data_file) as data:
                self.__store = json.load(data)
        else:
            f = open(data_file, 'a')
            json.dump({}, f)

    def __dump(self):
        data_file = "{}_data.json".format(self.name)
        with open(data_file, 'w') as fp:
            json.dump(self.__store, fp, sort_keys=True, indent=4)
        Timer(60, self.__dump).start()
