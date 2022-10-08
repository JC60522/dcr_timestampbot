import json, subprocess, uuid


class Ipfs:
    def __init__(self, query):
        self.query = query

    def search(self):
        """
        Method searches for content from IPFS node.
        :return: Returns search result.
        """
        try:
            res = subprocess.check_output(["ipfs", "cat", self.query], timeout=5)
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
            serialized_query = json.dumps(self.query)
            unique_id = str(uuid.uuid4())
            with open(f"./temp/{unique_id}.json", "w") as f:
                f.write(serialized_query)
            res = subprocess.check_output(["ipfs", "add", f"./temp/{unique_id}.json"], timeout=5).split()[1]
            return res
        except Exception as e:
            print(e)
            return False
