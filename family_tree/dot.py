from abc import ABCMeta, abstractmethod
from collections import namedtuple

# TODO add indents to final DOT file


def dict_to_dot_attributes(attributes_dict, sep=','):
    '''
    Form a DOT attribute list from the provided dictionary, using the separator
    to separate attributes. The attributes will be sorted by key and value, to
    ensure consistency when compiling (i.e., to make the result code more
    diffable).
    '''

    dot_attributes = []
    for key, value in sorted(attributes_dict.items()):

        # If the value is a string bracketed by '<' and '>', use those
        if type(value) == str and len(value) >= 2 and (value[0], value[-1]) == ('<', '>'):
            bracketed_value = '{}'.format(value)

        # Otherwise, use quotes
        else:
            bracketed_value = '"{}"'.format(value)

        dot_attributes.append('{}={}'.format(key, bracketed_value))

    return sep.join(dot_attributes)

class DotCommon(metaclass=ABCMeta):

    def __init__(self, key, attributes=None):
        self.key = key
        self.attributes = attributes or {}

    @abstractmethod
    def to_dot(self):
        pass

class Graph(DotCommon):

    graph_types = ('graph', 'digraph', 'subgraph')

    def __init__(self, key, graph_type, children=None, attributes=None,
            node_defaults=None, edge_defaults=None):

        if graph_type not in Graph.graph_types:
            msg = 'Expected graph type in {}, but received: {}'
            vals = Graph.graph_types, graph_type
            raise ValueError(msg.format(*vals))

        self.graph_type = graph_type
        self.children = children or []
        self.node_defaults = node_defaults or {}
        self.edge_defaults = edge_defaults or {}
        super().__init__(key, attributes)

    def to_dot(self):

        lines = []
        lines.append('{} "{}" {{'.format(self.graph_type, self.key))
        if self.attributes:
            lines.append('{};'.format(dict_to_dot_attributes(self.attributes, sep=';\n')))
        if self.node_defaults:
            lines.append('node [{}];'.format(dict_to_dot_attributes(self.node_defaults)))
        if self.edge_defaults:
            lines.append('edge [{}];'.format(dict_to_dot_attributes(self.edge_defaults)))
        for child in self.children:
            lines.append(child.to_dot())
        lines.append('}')

        return '\n'.join(lines)

class Node(DotCommon):

    def to_dot(self):

        attr_string = dict_to_dot_attributes(self.attributes)

        if attr_string:
            return '"{}" [{}];'.format(self.key, attr_string)
        else:
            return '"{}";'.format(self.key)

class Edge(DotCommon):

    EdgeKey = namedtuple('EdgeKey', ['parent', 'child'])

    def __init__(self, parent_key, child_key, attributes=None):
        super().__init__(Edge.EdgeKey(parent_key, child_key), attributes)

    def to_dot(self):

        attr_string = dict_to_dot_attributes(self.attributes)

        if attr_string:
            return '"{}" -> "{}" [{}];'.format(self.key.parent, self.key.child, attr_string)
        else:
            return '"{}" -> "{}";'.format(self.key.parent, self.key.child)

class Rank:

    def __init__(self, keys=None):
        self.keys = keys or []

    def to_dot(self):
        return '{{rank=same {}}};'.format(
                ' '.join(['"{}"'.format(key) for key in sorted(self.keys, key=str)])
                )

