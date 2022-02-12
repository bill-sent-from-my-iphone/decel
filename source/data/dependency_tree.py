
class DependencyNode:

    def __init__(self, value):
        self.value = value
        self.children = []
        self.parents = []

    def add_parent(self, parent):
        self.parents.append(parent)

    def add_child(self, child):
        self.children.append(child)

    def yield_values(self, seen=None):
        if seen is None:
            seen = []

        for parent in self.parents:
            if parent.value not in seen:
                for v in parent.yield_values(seen=seen):
                    yield v

        yield self.value
        seen.append(self.value)

        for child in self.children:
            if child.value not in seen:
                for v in child.yield_values(seen=seen):
                    yield v

    def __eq__(self, other):
        return self.value == other.value

class DependencyTree:

    def __init__(self):
        self.node_dict = {}

    def shake(self):
        self.node_dict = {}

    def get_node(self, value):
        if value in self.node_dict:
            return self.node_dict[value]
        out = DependencyNode(value)
        self.node_dict[value] = out
        return out

    def add_dependency(self, parent, child):
        p = self.get_node(parent)
        c = self.get_node(child)
        if p not in c.parents:
            c.add_parent(p)
        if c not in c.children:
            p.add_child(c)

    def get_roots(self):
        roots = []
        for val in self.node_dict:
            node = self.node_dict[val]
            if len(node.parents) == 0:
                roots.append(node)
        return roots

    def yield_values(self):
        seen = []
        for r in self.get_roots():
            for v in r.yield_values(seen):
                yield v

