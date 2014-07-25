#python btce_price_daemon.py &
screen -dmS over /usr/bin/python overlord-manager.py --param-file=parameters-lists/params_1112012040401101010050051015015101011.pkl 2> logs/overlord.err
screen -dmS grand /usr/bin/python grand_observer-work.py  --param-file=parameters-lists/params_1112012040401101010050051015015101011.pkl --live --api=btce-api-key.txt --email=email_credentials.txt 2> logs/grandobserver.err
