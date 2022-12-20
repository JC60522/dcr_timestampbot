from hashlib import sha256
import json, requests
import tweepy
import time
from ipfs_interface import Ipfs
from getpass import getpass

api_key_secret = getpass("Enter your api_key_secret:\n")
bearer_token = getpass("Enter your bearer_token:\n")
access_token = getpass("Enter your access_token:\n")
access_secret = getpass("Enter your access_secret:\n")

auth = tweepy.OAuthHandler(api_key_secret, bearer_token)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)


def last_mentioned():
    """
    Method reads csv file to keep track of last mentioned, in order to search from this value onwards for new mentions.
    :return: Returns Latest mentioned user ID.
    """
    with open('last_mentioned.csv', 'r') as f:
        data = f.read()
        data = data.split('\n')
    return data[-2]


def listen():
    """
    Method constructs tweet, timestamps, push content to IPFS and logs tweet ID.
    :return: Nothing.
    """
    # tweet template
    template = {"user": {"id_str": "Undefined", "name": "Undefined", "screen_name": "Undefined"},
                "id_str": "Undefined", "created_at": "Undefined", "text": "Undefined", "repliedid": "Undefined"}
    tweets = []
    # Grab all new mentions and put them in a list, json format
    try:
        [tweets.append(json.dumps(i._json)) for i in api.mentions_timeline(since_id=last_mentioned())]

    except Exception as e:
        print(f'Error making request to twitter api: {e}')
    for i in tweets:
        template["user"]["id_str"] = json.loads(i)["user"]["id_str"]
        template["user"]["name"] = json.loads(i)["user"]["name"]
        template["user"]["screen_name"] = json.loads(i)["user"]["screen_name"]
        template["id_str"] = json.loads(i)["id_str"]
        template["created_at"] = json.loads(i)["created_at"]
        template["text"] = json.loads(i)["text"]
        template["repliedid"] = json.loads(i)["in_reply_to_user_id"]

        # Hash tweet
        hashed_json = sha256(json.dumps(template).encode('utf-8')).hexdigest()
        try:
            # Timestamp tweet
            response = requests.post("https://time.decred.org:49152/v2/timestamp", data={"digest": hashed_json},
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'}).text

            # If successful response from dcr-time server, push to ipfs.
            if json.loads(response)["result"] == 1:
                dcrtime_url = f'https://timestamp.decred.org/results#hashes={hashed_json}'
                cid = Ipfs(template).add()
                if not cid:
                    print('Error adding content to ipfs.')

                # Construct tweet body
                ipfs_url = f'https://dcr-timestampbot.com/ipfs/{cid.decode("utf-8")}'
                reply = f'Hey There @{template["user"]["screen_name"]} :) This tweet is stored on IPFS and will be timestamped within the next hour. Times-stamping status: {dcrtime_url} ~ Saved tweet: {ipfs_url}'
                try:
                    # Tweet reply to mention with ipfs and dcr-time urls, and save ID to csv (last mentioned)
                    api.update_status(status=reply, in_reply_to_status_id=template["id_str"])

                    with open('last_mentioned.csv', 'a') as f:
                        f.write(template["id_str"])
                        f.write("\n")
                except Exception as e:
                    print(f'Error posting tweet: {e}')
        except Exception as e:
            print(f'Error time-stamping content: {e}')


def scheduler():
    """
    Method checks twitter mentions every once every 55 seconds.
    """
    while True:
        time.sleep(55)
        listen()


if __name__ == '__main__':
    scheduler()
