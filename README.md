This is v0.1.0 of dcr-timestampbot. This project is inspired by friendly enquiry of https://github.com/tiagoalvesdulce/dcrtimestamptweet.

The request was to fix some issues as well giving me the opportunity to rebuild & maintain this twitter bot in a language I feel comfortable with. 
For this particular application my current language of choice is Python.

How it works

Every time @dcrtimestampbot is mentioned on twitter, a hash of the JSON-like string of the tweet is timestamped and a file containing this string is stored on IPFS.

Saving the IPFS hash you can get the tweet digest and verify if it has been timestamped on the Decred Blockchain.

In order to run this codebase:

-Setup/run IPFS node/daemon
-Run main.py
-Run dcr_timestampbot.py ~  When prompted enter your API-Keys.
-Optional ~ Host another node and run a routine job that pins the content from the main node to secondary. / Push to service like Web3Storage.

**Make sure the "id_str" of the user who last mentioned the bot is saved in last_mentioned.csv
