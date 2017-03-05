"""
Record object - Stores patient record information
@author: Will Kearns

"""
import re
from annotation_matcher import search_annotation
from collections import defaultdict
from config import METAMAP_DIR
from subprocess import Popen, PIPE, STDOUT
import sys


class Record:

    def __init__(self, rid, record, file, annotation):
        """
        Stores patient record

        :param rid: record id number
        :param record: free text note
        :param file: filename
        :param annotation:
        """
        self.rid = rid
        self.text = record
        self.sections = self.close_tags(record)
        self.file = file
        self.annotation = annotation
        self.gold = self._get_grades()
        self.umls_tags = []

    def _get_grades(self):
        annots_string = search_annotation(self.annotation, "Grade Category")
        return [int(n.group()) for n in re.finditer("\\d+", annots_string)]

    @staticmethod
    def close_tags(text):
        """
        Method to create a dictionary of record sections from XML

        :param text: input XML text with unclosed tags
        :return: return a dictionary of with XML tag keys and values being the inner text
        """
        stack = []
        cleaned = defaultdict(str)
        curr_tag = None
        for line in text.split("\n"):
            open_tag = re.search(r"<(\w+)>", line)
            closed_tag = re.search(r"</(\w+]?)>", line)
            if open_tag is not None:
                curr_tag = open_tag.expand(r"\1")
                stack.append(open_tag.expand(r"\1"))
            elif closed_tag is not None:
                stack.pop()
            elif curr_tag:
                cleaned[curr_tag] += line + " "
        return cleaned

    def get_umls_tags(self, text):
        """
        Runs Metamap Lite over a given input string

        :param text: text to run NER using the UMLS terms within Metamap Lite
        :return: a list of terms extracted from the text along with their associated concepts
        """
        if "win" in sys.platform:
            metamap_path = METAMAP_DIR + r"/metamaplite.bat"
        else:
            metamap_path = METAMAP_DIR + r"/metamaplite.sh"
        p = Popen([metamap_path, "--pipe",
                   "--indexdir=" + METAMAP_DIR + r"/data/ivf/strict",
                   "--modelsdir=" + METAMAP_DIR + "/data/models",
                   "--specialtermsfile=" + METAMAP_DIR + "/data/specialterms.txt",
                   "--brat"], stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
        stdout = p.communicate(input=text.encode())[0]

        CURR_TAG = None
        for line in stdout.decode().split("\n"):
            if re.match(r"T[0-9]+", line):
                line = line.split()
                CURR_TAG = Term(line[0], line[2], line[3], line[4])
                self.umls_tags.append(CURR_TAG)
            elif re.match(r"[A-Z][0-9]+", line):
                line = line.split()
                CURR_TAG.concepts.append(Concept(line[0], line[3], line[4]))
        return self.umls_tags

    def get_tumor_mentions(self):
        for term in self.get_umls_tags(self.text):
            print(term.tag)
            for concept in term.concepts:
                print(concept.concept_id)

    def dump(self, output_file):
        output_file.write(self.text)


class Term:

    def __init__(self, id_, start, stop, name):
        """
        A named entity extracted with Metamap Lite

        :param id_: The term id within the document, not necessarily numbered by occurrence
        :param start: The character number where the term begins
        :param stop: The character number where the term ends
        :param name: The name of the term
        """
        self.id = id_
        self.start = start
        self.stop = stop
        self.tag = name
        self.concepts = []


class Concept:
    def __init__(self, id_, concept_id, concept):
        """
        This class holds the Concept Ids extracted from the BRAT annotations coinciding with a given named entity

        :param id_: the concept id within the document
        :param concept_id: follows the format Ontology:term, e.g. for the UMLS Concept Identifiers, ConceptId:C199726
        :param concept: the name of the concept
        """
        self.id = id_
        self.concept_id = concept_id
        self.concept = concept
