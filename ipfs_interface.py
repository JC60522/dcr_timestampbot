import ipfshttpclient


class Ipfs:
    def __init__(self, query):
        self.query = query

    def search(self):
        """
        Method searches for content from IPFS node.
        :return: Returns search result.
        """
        try:
            client = ipfshttpclient.connect(timeout=5)
            res = client.cat(self.query)
            return res
        except Exception as e:
            print(e)
            return False

    def add(self):
        """
        Method adds content to IPFS node.
        :return: Returns CIDv0.
        """
        try:
            client = ipfshttpclient.connect(timeout=5)
            res = client.add_json(self.query)
            return res
        except Exception as e:
            print(e)
            return False

