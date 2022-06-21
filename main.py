from uuid import uuid4
from pprint import pp

inputs = [
    ["/api/v2/student", 'GET', 'http://localhost/api/student'],
    ["/api/v1/student", 'GET', 'http://localhost/api/v1/student'],
    ["/api/v2", 'GET', 'http://localhost/api/v2'],
    ["/api/v2", 'OPTION', None],
    ["/api/v2/student/{student_id}", 'GET', 'http://localhost/api/student/{student_id}'],
]


class URLNode:
    def __init__(self, name, parent=None, children=None):
        self.integration_options = {}
        self.parent_id = None
        self.id = None
        if children is None:
            children = {}
        self.name = name
        self.parent = parent
        self.children = children

    def get_child(self, name):
        return self.children.get(name, None)

    def update_integration(self, options):
        self.integration_options = {**self.integration_options, **options}

    def get_full_path(self):
        temp = []

        curr = self
        while curr.parent is not None:
            temp.append(curr.name)
            curr = curr.parent
        temp.reverse()
        # if root node
        if len(temp) == 1:
            return "/"
        return "/".join(temp)

    def construct_aws_resource(self):
        if not self.parent.get_id():
            raise ValueError("parent was not yet constructed")
        if self.id:
            raise ValueError("can only construct the node once")
        self.id = generate_id()
        self.parent_id = self.parent.get_id()

    def get_id(self):
        return self.id


class URLRootNode(URLNode):
    def construct_aws_resource(self):
        self.id = "pre-defined"
        self.parent_id = None


def apply_defn(root_node, defn):
    node = build_tree_from_url(root_node, defn.path)
    node.update_integration(defn.options)


def build_tree(definitions):
    root_node = URLNode(None)
    # the first root node is already created?
    root_node.children[""] = URLRootNode("", root_node)
    for defn in definitions:
        apply_defn(root_node, defn)
    return root_node.get_child("")


# depth first build, return back the node
def build_tree_from_url(root, url):
    elements = url.split("/")
    curr = root
    for idx, element in enumerate(elements):
        if curr.get_child(element) is None:
            curr.children[element] = URLNode(element, curr)
        curr = curr.get_child(element)
    return curr


class ProxyIntegrationDefinitions:
    def __init__(self, path, method, endpoint=None):
        self.path = path
        self.options = {}
        self.options[method] = {
            "endpoint": endpoint
        }


def parse_inputs(inputs):
    # going through each of the input and for each element build a tree
    definitions = []
    for proxy_defs in inputs:
        path_part = proxy_defs[0]
        method_part = proxy_defs[1]
        endpoint_part = proxy_defs[2]
        definitions.append(ProxyIntegrationDefinitions(path_part, method_part, endpoint_part))
    root = build_tree(definitions)
    create_all_nodes(root)
    print_tree(root)


def create_all_nodes(root):
    queue = [root]
    while queue:
        node = queue.pop(0)
        # creation of the nodes by calling aws api
        node.construct_aws_resource()
        queue.extend(node.children.values())
    # after creation of the resources, set the options


def print_tree(root):
    queue = [root]
    lookup = {}
    while queue:
        node = queue.pop(0)
        lookup[node.get_full_path()] = {"id": node.id, "parent-id": node.parent_id,
                                        "integration_options": node.integration_options}
        queue.extend(node.children.values())
    pp(lookup)


def generate_id():
    return uuid4()


if __name__ == "__main__":
    parse_inputs(inputs)
