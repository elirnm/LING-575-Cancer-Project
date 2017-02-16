from bs4 import BeautifulSoup

class Record:
    def __init__(self, pid, record, file):
        self.pid = pid
        self.record = record
        self.file = file

    def parse(self):
        return BeautifulSoup(self.record, "xml")

    def dump(self, output_file):
        output_file.write(self.record)
