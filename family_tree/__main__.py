import networkx as nx
from family_tree.tree import FamilyTree

# Initialization

tree = FamilyTree.from_paths(
    'directory.csv',
    'chapters.csv',
    'brothers_not_knights.csv',
    'family_colors.csv',
    'settings.yaml',
)
tree.decorate()
dotgraph = tree.to_dot_graph()

print(dotgraph.to_dot())

