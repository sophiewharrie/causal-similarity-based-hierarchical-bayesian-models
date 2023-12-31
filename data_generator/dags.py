import numpy as np
import copy
import networkx as nx

from utils import valid_DAG
from utils import make_graph


def apply_graph_constraints(A_t, G_ref):
    """Takes an adjacency matrix A_t for a task DAG as input and adjusts it
    according to a set of hard-coded constraints. 

    Returns the adjusted adjacency matrix
    """
    G_t = make_graph(A_t, G_ref)

    T_nodes = [v for v in G_t.nodes() if v.startswith('T')]
    
    # no self edges
    G_t.remove_edges_from(nx.selfloop_edges(G_t))

    # no Y --> edges
    for edge in list(G_t.out_edges('Y')):
        G_t.remove_edge(edge[0], edge[1])

    for T in T_nodes:
        node_remove = []
        for path in [l for l in nx.all_simple_paths(G_t, source=T, target='Y')]:
            # remove Tn --> Tm edges
            if path[1].startswith('T'): node_remove.append(path[1])
            # remove Tn --> X if an X --> Tm path exists
            if 'T' in [p[0] for p in path[1:]]: node_remove.append(path[1])
        for node in list(set(node_remove)):
            G_t.remove_edge(T, node)

    # if there is no T --> ... --> Y path then add a direct T --> Y path
    for T in T_nodes:
        if len([l for l in nx.all_simple_paths(G_t, source=T, target='Y')])==0:
            G_t.add_edge(T, 'Y')

    return nx.to_numpy_array(G_t)


def get_task_DAG(A_ref, G_ref, epsilon, max_iter=5000):
    """Simulate a task DAG from a reference DAG, by randomly flipping edges in the adjacency matrix.
    The probability of flipping an edge is p, where p ~ Unif(0, s).
    """
    A_t = None
    p = np.random.uniform(0, epsilon)
    counter = 0
    while not valid_DAG(A_t, G_ref) and counter < max_iter:
        counter += 1
        A_t = copy.deepcopy(A_ref)
        # sample entries to modify
        sample_edges = [(i,j) for i in range(A_ref.shape[0]) for j in range(A_ref.shape[0]) if np.random.binomial(1, p)]
        # modify entries in the adjacency matrix by flipping edges on/off
        for edge in sample_edges:
            A_t[edge[0],edge[1]] = 1 - A_t[edge[0],edge[1]]
        # apply rules for constructing graphs
        A_t = apply_graph_constraints(A_t, G_ref)
    # if no suitable graph found after max_iter iterations use reference
    if counter == max_iter: 
        A_t = copy.deepcopy(A_ref)
    return A_t
