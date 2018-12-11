# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 16:27:37 2018

@author: thomas
"""

import geopandas as gpd
import pandas as pd
import networkx as nx
import json
import numpy as np

def graph_to_df(graph, edges_path, nodes_path):
    """
    Write json files with edges and nodes
    
    @graph(Networkx graph): graph with geometries
    @edges_path(str): complete path with filename for edges
    @nodes_path(str): complete path with filename for nodes
    
    """
    #Get edges and write GeoJSON
    df_edges = nx.to_pandas_edgelist(graph)
    df_edges = df_edges[["source", "target", "time"]]
    df_edges.to_json(edges_path, force_ascii=True, orient="records")

    #Get nodes (get 'x' and 'y' for futur center_nodes operations)
    # and write json to get a dict of nodes attributes
    l_nodes = list(graph.nodes(data=True))
    nodes = dict(l_nodes)
    with open(nodes_path, "w") as fp:
        json.dump(nodes, fp, ensure_ascii=False)
    
def df_to_graph(edges_path, nodes_path, source="source", target="target"):
    """
    Get edges and nodes json files and return G, a Networkx graph
    
    @edges_path(str): complete path with filename for edges
    @nodes_path(str): complete path with filename for nodes
    @source(str): name of source field
    @target(str): name of target field
    """
    G = nx.Graph()
    df_edges = pd.read_json(edges_path, orient="records")
    dict_edges = df_edges.to_dict(orient="list")
    edges = pd.DataFrame(dict_edges)
    G = nx.from_pandas_edgelist(edges, source=source, target=target, edge_attr=True)
    
    with open(nodes_path, "r") as fp:
        attrs = json.load(fp)
    
    new_attrs = {}
    for key,value in attrs.items():
        new_attrs[np.int64(key)] = value
    
    nx.set_node_attributes(G, new_attrs)
    
    return G