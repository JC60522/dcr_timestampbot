import json
import ipfshttpclient


class Ipfs:
    '''
    2 functions for search(from) / add(to) ipfs node/daemon
    '''
    def __init__(self, query):
        self.query = query

    def search(self):
        try:
            client = ipfshttpclient.connect(timeout=5)
            return client.cat(self.query)
        except Exception as e:
            print(e)
            return "Oops...Some error occured while quering your document Hash."

    def add(self):
        try:
            client = ipfshttpclient.connect(timeout=5)
            return client.add_json(self.query)
        except Exception as e:
            print(e)
            return "Oops...Some error occured while quering your document Hash."

