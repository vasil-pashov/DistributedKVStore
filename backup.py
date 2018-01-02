    def send_ping_req(self, original):
        alive = self._alive_nodes()
        to_req = self._pick_random(alive, original)
        node_alive = False
        print("Sending ping_req. Alive nodes: {}, chosen: {}".format(alive, to_req))
        for node in to_req:
            try:
                address = urlparse.urljoin(node, "/ping_req")
                print("Send ping request to: {}".format(address))
                req_params = {'node': original}
                ping_req_resp = requests.get(
                    address, params=req_params, timeout=self.ping_timeout)
                node_alive = node_alive or self._process_ping_req_resp(ping_req_resp)
            except requests.exceptions.RequestException:
                pass
        if not node_alive:
            self.node_status[original].status = "SUSPECTED"
            self.events.append({'type': 'suspect', 'node': original})

    def process_ping_req(self, node):
        try:
            address = urlparse.urljoin(node, "ping")
            resp = requests.get(address, timeout=self.ping_timeout)
            resp.json()['status'] = "UP"
            return resp.json()
        except requests.exceptions.RequestException:
            return {'status': 'DOWN'}



    def _process_resp(self, resp, requested_node=None):
        data = resp.json()
        if data['type'] == "ACK":
            self._process_ack_resp(data)

    def _process_ack_resp(self, data):
        node = data['node']
        previous_status = self.node_status[node].status
        if previous_status != "UP":
            self.events.append(Event('alive', node, data['incarnation']))
            self.node_status[node].status = "UP"

    def _process_ping_req_resp(self, data, requested_node):
        if data['status'] == "UP":
            previous_status = self.node_status[requested_node].status
            if previous_status != "UP":
                event = Event('alive', requested_node, data['incarnation'])
                self.events.append(event)
                self.node_status[requested_node].status = "UP"
            return True
        return False
