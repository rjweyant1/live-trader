#python btce_price_daemon.py &
screen -dmS over /usr/bin/python overlord-manager.py -d parameters-lists 2> logs/overlord.err
screen -dmS grand /usr/bin/python grand_observer-work.py  --param-file=parameter-file.txt --live --api=btce-api-key.txt --email=email_credentials.txt 2> logs/grandobserver.err
