"""
Record object - Stores patient record information
@author: Will Kearns

"""
import re
from collections import defaultdict
from config import METAMAP_DIR
from subprocess import Popen, PIPE, STDOUT


class Record:
    """
    Record- Stores patient record

    Still needs further development.

    :param pid: patient id number
    :param record: free text note
    """

    def __init__(self, pid, record, file, annotation):
        self.pid = pid
        self.text = record
        self.sections = self.close_tags(record)
        self.file = file
        self.annotation = annotation

    @staticmethod
    def close_tags(text):
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

    @staticmethod
    def get_umls_tags(text):
        metamap_path = METAMAP_DIR + r"\metamaplite.bat"
        p = Popen([metamap_path, "--pipe",
                   "--indexdir=" + METAMAP_DIR + r"\data\ivf\strict",
                   "--modelsdir=" + METAMAP_DIR + "\data\models",
                   "--specialtermsfile=" + METAMAP_DIR + "\data\specialterms.txt",
                   "--brat"], stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
        stdout = p.communicate(input=text.encode())[0]
        for line in stdout.decode().split("\n"):
            if re.match(r"[A-Z][0-9]+", line):
                yield line

    def dump(self, output_file):
        output_file.write(self.text)
