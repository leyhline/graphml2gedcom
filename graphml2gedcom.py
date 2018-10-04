#!/usr/bin/env python3


"""
graphml2gedcom.py

A short script for converting a family tree build with yEd and saved in graphml format
to gedcom. Graphml is simple XML:

- Nodes are persons and families.
- Edges are relations.
- Persons most of the time have a description with name as well as dates for birth and death.
- Since there are no informations about sex I assume everyone is male.
- Therefore, the outputted gedcom needs to be manually edited afterwards.
"""


from argparse import ArgumentParser
from xml.etree import ElementTree
import datetime
import re


class Person:
    REGEX_SPLIT_PERON_DATA = re.compile(r"""(?P<name>[^\*]*)\*?(?P<birth>[^†]*)†?(?P<death>.*)""")
    REGEX_NAME_PREFIX = re.compile(r"""\(\d+\)""")
    def __init__(self, id, data):
        self.id = id
        self.parse_data(data)

    def parse_data(self, data):
        """Parse description of person node and extract name and dates."""
        data = data.replace("\n", "")
        match = self.REGEX_SPLIT_PERON_DATA.match(data)
        self.name = self.REGEX_NAME_PREFIX.sub("", match.group("name")).strip()
        try:
            self.birth = datetime.datetime.strptime(match.group("birth").strip(), "%d.%m.%Y")
        except ValueError as e:
            print(self.name, "(birth)", "->", e)
            self.birth = None
        try:
            self.death = datetime.datetime.strptime(match.group("death").strip(), "%d.%m.%Y")
        except ValueError as e:
            print(self.name, "(death)", "->", e)
            self.death = None

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
    """Convert ids from graphml (e for edge, n for node) to integers."""
    assert graphid[0] in ["e", "n"]
    return int(graphid[1:])


def parse_xmltree(tree):
    root = tree.getroot()
    graphs = [child for child in root if child.tag.endswith("graph")]
    nodes = [child for child in graphs[0] if child.tag.endswith("node")]
    edges = [child for child in graphs[0] if child.tag.endswith("edge")]
    return nodes, edges


def parse_nodes(nodes):
    """Parse nodes, returning a list of persons and a list of families."""
    nodes = [(node.attrib["id"], node.findall(".//{http://www.yworks.com/xml/graphml}NodeLabel")) for node in nodes]
    nodes = [(node[0], [label.text for label in node[1] if len(label.text.strip()) > 0]) for node in nodes]
    persons = list(filter(lambda x: len(x[1]) > 0, nodes))
    families = list(filter(lambda x: len(x[1]) == 0, nodes))
    assert len(nodes) == len(persons) + len(families)
    persons_data = [(id2int(person[0]), person[1][0].strip()) for person in persons]
    families_ids = [id2int(family[0]) for family in families]
    return [Person(person[0], person[1]) for person in persons_data], [Family(family) for family in families_ids]


def parse_edges(edges):
    """Parse edges returning a list of relations."""
    relations = [Relation(id2int(edge.attrib["id"]), id2int(edge.attrib["source"]), id2int(edge.attrib["target"])) for edge in edges]
    return relations


def parse_graphml(path):
    """Parse a whole graphml file returning lists of persons, families and relations."""
    tree = ElementTree.parse(path)
    nodes, edges = parse_xmltree(tree)
    print("Found:", len(nodes), "nodes,", len(edges), "edges")
    persons, families = parse_nodes(nodes)
    relations = parse_edges(edges)
    print("Detected:", len(persons), "persons,", len(families), "families,", len(relations), "relations")
    return persons, families, relations


def create_child_gedcom(person_id, relations):
    return "\n".join("1 FAMC @F{id}@".format(id=relation.source) for relation in relations if person_id == relation.target)


def create_spouse_gedcom(person_id, relations):
    return "\n".join("1 FAMS @F{id}@".format(id=relation.target) for relation in relations if person_id == relation.source)


def create_person_entries(persons, relations):
    """Create gedcom strings from a list of persons."""
    gedcom = []
    for person in persons:
        entry = "0 @I{id}@ INDI\n1 NAME {name}".format(id=person.id, name=person.name)
        if person.birth:
            entry += "\n1 BIRT\n2 DATE {date}".format(date=person.birth.strftime("%d %b %Y").upper())
        if person.death:
            entry += "\n1 DEAT\n2 DATE {date}".format(date=person.death.strftime("%d %b %Y").upper())
        entry += "\n" + create_child_gedcom(person.id, relations)
        entry += "\n" + create_spouse_gedcom(person.id, relations)
        gedcom.append(entry)
    return "\n".join(gedcom)


def create_relations_gedcom(family_id, relations):
    children = [relation.target for relation in relations if relation.source == family_id]
    spouses = [relation.source for relation in relations if relation.target == family_id]
    children_gedcom = "\n".join("1 CHIL @I{id}@".format(id=child) for child in children)
    spouses_gedcom = "\n".join("1 HUSB @I{id}@".format(id=spouse) for spouse in spouses)
    return children_gedcom + "\n" + spouses_gedcom


def create_family_entries(families, relations):
    """Create gedcom string from a list of families."""
    gedcom = []
    for family in families:
        entry = "0 @F{id}@ FAM".format(id=family.id)
        entry += "\n" + create_relations_gedcom(family.id, relations)
        gedcom.append(entry)
    return "\n".join(gedcom)


def create_gedcom(persons, families, relations):
    """Create a whole gedcom string for directly writing into a file."""
    gedcom = "0 HEAD\n1 SOUR UNSPECIFIED\n1 GEDC\n2 VERS 5.5.1\n2 FORM Lineage-Linked\n1 CHAR UTF-8"
    gedcom += "\n" + create_person_entries(persons, relations)
    gedcom += "\n" + create_family_entries(families, relations)
    gedcom += "\n0 TRLR"
    return gedcom


def main():
    parser = ArgumentParser()
    parser.add_argument("input", help="Path to .graphml input file.")
    parser.add_argument("-o", "--output", help="Path where .ged output file should be written.")
    args = parser.parse_args()
    persons, families, relations = parse_graphml(args.input)
    gedcom = create_gedcom(persons, families, relations)
    gedcom = gedcom.replace("\n\n", "\n")
    if not args.output:
        print(gedcom)
        return
    with open(args.output, "w") as fd:
        fd.write(gedcom)
    print(args.output, "written.")


if __name__ == "__main__":
    main()
