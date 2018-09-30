#!/usr/bin/env python3


from argparse import ArgumentParser
from xml.etree import ElementTree


class Person:
    def __init__(self, id, data):
        self.id = id
        self.parse_data(data)

    def parse_data(self, data):
        self.data = data

    def __repr__(self):
        return "Person%d" % self.id


class Family:
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return "Family%d" % self.id


class Relation:
    def __init__(self, id, source, target):
        self.id = id
        self.source = source
        self.target = target

    def __repr__(self):
        return "Relation%d(%d->%d)" % (self.id, self.source, self.target)


def id2int(graphid):
    assert graphid[0] in ["e", "n"]
    return int(graphid[1:])


def parse_xmltree(tree):
    root = tree.getroot()
    graphs = [child for child in root if child.tag.endswith("graph")]
    nodes = [child for child in graphs[0] if child.tag.endswith("node")]
    edges = [child for child in graphs[0] if child.tag.endswith("edge")]
    return nodes, edges


def parse_nodes(nodes):
    nodes = [(node.attrib["id"], node.findall(".//{http://www.yworks.com/xml/graphml}NodeLabel")) for node in nodes]
    nodes = [(node[0], [label.text for label in node[1] if len(label.text.strip()) > 0]) for node in nodes]
    persons = list(filter(lambda x: len(x[1]) > 0, nodes))
    families = list(filter(lambda x: len(x[1]) == 0, nodes))
    assert len(nodes) == len(persons) + len(families)
    persons_data = [(id2int(person[0]), person[1][0].strip()) for person in persons]
    families_ids = [id2int(family[0]) for family in families]
    return [Person(person[0], person[1]) for person in persons_data], [Family(family) for family in families_ids]


def parse_edges(edges):
    relations = [Relation(id2int(edge.attrib["id"]), id2int(edge.attrib["source"]), id2int(edge.attrib["target"])) for edge in edges]
    return relations


def parse_graphml(path):
    tree = ElementTree.parse(path)
    nodes, edges = parse_xmltree(tree)
    print("Found:", len(nodes), "nodes,", len(edges), "edges")
    persons, families = parse_nodes(nodes)
    relations = parse_edges(edges)
    print("Detected:", len(persons), "persons,", len(families), "families,", len(relations), "relations")


def main():
    parser = ArgumentParser()
    parser.add_argument("input")
    args = parser.parse_args()
    parse_graphml(args.input)


if __name__ == "__main__":
    main()
