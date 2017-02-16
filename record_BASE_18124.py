from bs4 import BeautifulSoup

class Record:
    def __init__(self, pid, record):
        self.pid = pid
        self.record = record

    def parse(self):
        return BeautifulSoup(self.record, "xml")

    def dump(self, output_file):
        output_file.write(self.record)
