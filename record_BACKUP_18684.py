"""
Record object - Stores patient record information
@author: Will Kearns

"""
import re
from collections import defaultdict


class Record:
<<<<<<< HEAD
    def __init__(self, pid, record, file):
        self.pid = pid
        self.record = record
        self.file = file
=======

    def __init__(self, pid, record):
        """
        Record- Stores patient record

        Still needs further development.

        :param pid: patient id number
        :param record: free text note
        """
        self.pid = pid
        self.text = record
        self.sections = self.close_tags(record)
>>>>>>> 0285c757ca59d5e33a48d08634c829b7707b51f9

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

    def dump(self, output_file):
        output_file.write(self.text)
