from flask import Flask, render_template, redirect, request, flash
from bot_api import Bot
import Queue
import threading
from handler import *
from pprint import pprint
from tools import handle_response

application = Flask(__name__)      
bot = Bot("bot-api-key")
oneshot_queue = Queue.Queue()
inline_queue = Queue.Queue()


for n in range(6):
    regular_thread = threading.Thread(target=handle_regular_message, args = [oneshot_queue, bot])
    inline_thread = threading.Thread(target=handle_inline_keyboard_message, args = [inline_queue, bot])
    #...
    #Define other workers to handle another type of events
    #...
    regular_thread.daemon = True
    inline_thread.daemon = True
    regular_thread.start()
    inline_thread.start()

@application.route("/bot-api-key-as-path", methods = ['GET', 'POST'])
def get_zab_updates():
    try: data = request.get_json()
    except: return json.dumps({"Status": "Query Failed"})
    if not data: return json.dumps({"Status": "Empty Data"})
    if  'message' in  data:
        oneshot_queue.put(data)
    elif 'callback_query' in data:
        inline_queue.put(data)
    else:
        pass
    handle_response(data)
    return json.dumps({'Status': "Query Succeed"})


#Another bot
#@application.route("/BotKey", methods = ['GET', 'POST'])
#def get_botname_updates():
#    ...
#    return True    

if __name__ == '__main__':
  application.secret_key = 'knfjnfdndf fudn'
  application.run(host = '127.0.0.1', debug=True)
