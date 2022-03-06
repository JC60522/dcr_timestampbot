from hashlib import sha256
import json, requests
import tweepy
from apscheduler.schedulers.blocking import BlockingScheduler
from ipfs_interface import Ipfs


auth = tweepy.OAuthHandler('##############', '#########################')
auth.set_access_token('##################-##################', '############################')
api = tweepy.API(auth, wait_on_rate_limit=True)


def last_mentioned():
    """
    csv file to keep track of last mentioned, in order to search from this value onwards for new mentions
    """
    with open('last_mentioned.csv', 'r') as f:
        data = f.read()
        data = data.split('\n')
    return data[-2]


def listen():
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
            response = requests.post("https://time-testnet.decred.org:59152/v2/timestamp", data={"digest": hashed_json},
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'}).text
            # If successful response from dcrtime server, push to ipfs daemon
            if json.loads(response)["result"] == "1":
                dcrtime_url = f'https://timestamp.decred.org/results#hashes={hashed_json}'
                cid = Ipfs(template).add()

                # Construct tweet body
                ipfs_url = f'https://dcr-timestampbot.com/ipfs/{cid}'
                reply = f'''Hey There {template["user"]["name"]} :) This thread is stored on IPFS and it will be timestamped within the next hour.
                            Timestamping status: {dcrtime_url}   IPFS Thread: {ipfs_url}'''
                try:
                    # Tweet reply to mention with ipfs and dcrtime urls, and save ID to csv (last mentioned)
                    #api.update_status(status=reply, in_reply_to_status_id=template["id_str"])
                    with open('last_mentioned.csv', 'a') as f:
                        f.write(template["id_str"])
                        f.write("\n")
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)


def scheduler():
    '''
    Cron-like job to check twitter mentions every once every 15 seconds
    '''
    sched = BlockingScheduler()
    sched.add_job(listen(), 'interval', seconds=15)
    sched.start()


if __name__ == '__main__':
    scheduler()