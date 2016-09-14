import networkx as nx

from family_tree.reading import read
from family_tree.semester import *
from family_tree.writing import *
from family_tree.tree import decorate_tree
from family_tree import family_tree

# Initialization

graph = family_tree.generate_graph('directory.csv', 'chapters.csv', 'brothers_not_knights.csv', 'family_colors.csv')
decorate_tree(graph)
dotgraph = create_graph(graph)

print(dotgraph.to_dot())

