import os
import time

import networkx as nx
import requests
import socketio

from angrmanagement.logic.threads import gui_thread_schedule_async

URL = "http://localhost:4242/"


class GraphUpdateNamespace(socketio.ClientNamespace):
    def __init__(self, graph, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.graph = graph
        self.callback = callback

    def on_update(self, data):
        parent_id, node_id = data["src_id"], data["dst_id"]

        def get_trace(attr):
            return requests.get(f"{URL}/trace/{attr}/{node_id}").json()

        node_attrs = {
            attr: get_trace(attr)
            for attr in ["basic_blocks", "syscalls", "interactions"]
        }
        self.graph.add_node(node_id, **node_attrs)
        if node_id:
            self.graph.add_edge(parent_id, node_id)
        gui_thread_schedule_async(self.callback, args=(node_id,))


def initialize_client(graph, update_callback):
    client = socketio.Client()
    graph_update_namespace = GraphUpdateNamespace(graph, update_callback)
    client.register_namespace(graph_update_namespace)
    client.connect(URL)