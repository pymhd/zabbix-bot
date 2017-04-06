import os, sys, time
import Queue
from pprint import pprint
import json
from pprint import pprint
from tools import *


def handle_regular_message(q, bot_instance):
    #define actions to handle regular messages
    # nobody used it last time, no need
    return False
        


def handle_inline_keyboard_message(q, bot_instance):
    while True:
        obj = q.get()
        q.task_done()
        message = obj[callback_query]
        chat_id = message["message"]["chat"]["id"]
        vote_from_id = message["from"]["id"]
        callback_id = message["id"]
        message_to_update = message["message"]["message_id"]
        button_data = json.loads(message["data"])
        alert_txt, new_inline_keyboard = get_action_response(button_data, vote_from_id)
        if new_inline_keyboard:
            resp_update = bot_instance.updateMessageInline(chat_id, message_to_update, new_inline_keyboard)
        resp_alert = bot_instance.answerInline(chat_id, callback_id, alert_txt, True)
