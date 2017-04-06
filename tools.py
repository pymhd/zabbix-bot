import os
import sys
import requests
from datetime import datetime
from pymongo import MongoClient
import logging
from uuid import uuid4
from bson.objectid import ObjectId
import requests

def get_logger(name, logfile):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('/usr/local/comcom/Zabbix_Bot/log/{0}.log'.format(logfile))
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger

# Move it to mongo
_ADMINS = ["List of admin ids"]
_PRIVILEGED_USERS = ["list of priviliged users ] 
_PHONES = {} #Dict of id: phone items
_NAMES = {} #Dict of id: Name items to Zabbix Acknowledge events

_client = MongoClient('mongodb://user:password@mongohostname:27017')
_db = _client.zabbix_notification
_logger = get_logger(__name__, "main")

def _ack_event(eventid, who):
    url = "https://zabbixurl"
    auth_payload = {"jsonrpc": "2.0",
                    "method": "user.login",
                      "params": {
                      "user": "api_user",
                      "password": "api_password"
                       },
                    "id": 1
                    }
    try: token = requests.post(url, json=auth_payload).json()['result']
    except: return False
    ack_payload = {
                    "jsonrpc": "2.0",
                    "method": "event.acknowledge",
                    "params": {
                               "eventids": eventid,
                               "message": "Acknowledged by " + who,
                              },
                    "auth": token,
                    "id": 1
                   }
    res = requests.post(url, json = ack_payload).json()
    return res

def _check_ack(eventid):
    url = "https://zabbixurl"
    auth_payload = {"jsonrpc": "2.0",
                    "method": "user.login",
                      "params": {
                      "user": "api_user",
                      "password": "api_password"
                        },
                    "id": 1
                    }
    try: token = requests.post(url, json=auth_payload).json()['result']
    except: return False
    payload = { "jsonrpc": "2.0",
                "method": "event.get",
                "params": {
                 "output": "extend",
                 "eventids": eventid
               },
               "auth": token,
               "id": 1
              }
    try: res = requests.post(url, json = payload).json()['result'][0]['acknowledged']
    except: return False           
    if res == "1": return True
    else: return False


def _generate_new_inline_keyboard(eventid, itemid, status, ack = "", host_excluded = ""):
    if status == "original":
        emodji = u"\u274c"
    elif status == "excluded":
        emodji = u"\u2714\ufe0f"
    else: 
        emodji = u'\U0001f615'
    if ack:
        emodji_ack = u"\U0001f44c\U0001f3fb"
    else:
        emodji_ack = u"\U0001f4ac"
    if host_excluded:
        emodki_host = "True"
    else:
        emodki_host = "False"
    reply_markup = { "inline_keyboard":
                             [
                              [ {"callback_data": """{{"action": "ack", "eventid": {0}, "itemid": {1} }}""".format(eventid, itemid), "text": emodji_ack}, \
                                {"callback_data": """{{"action": "exclude", "eventid": {1}, "itemid": {0}}}""".format(itemid, eventid), "text": emodji}, \
                                {"callback_data": """{"action": "exclude_host", }""", "text": u"\U0001f6e0"}, \
                                {"callback_data": """{"action": "call"}""", "text": u"\U0001f4de"}
                              ]
                             ]
                            }
    return reply_markup


def _generate_buttons(**kwargs):
    itemid, eventid, hostname = (kwargs["itemid"], kwargs["eventid"], kwargs["hostname"])
    if "item_status" in kwargs: emodji_item = u"\u274c"
    else: emodji_item = u"\u2714\ufe0f"
    if "ack" in kwargs: emodji_ack = u"\U0001f44c\U0001f3fb"
    else: emodji_ack = u"\U0001f4ac" 
    pass

def handle_response(resp):
    result = _db.raw_data.insert_one(resp)
    insert_id = result.inserted_id
    _logger.info("Inserting response {0}".format(insert_id))
    return True
                

def get_action_response(data, user_id):
    if user_id == 132680583:   # Martinov
        return (u"Try to CRACK another NET, pal \U0001f604", False)
    action = data["action"]
    if action == "ack":
        if user_id in _NAMES:
            username = _NAMES[user_id]
        else: 
            username = "Unknown User"
        eventid = int(data["eventid"])
        itemid = int(data["itemid"])
        z_resp = _ack_event(eventid, username)
        if not z_resp:
            return (u"\u2639\ufe0f An Error Occurred \u2639\ufe0f", False)
        else:
            if _check_excluded(itemid):
                return (u"Item acknowledged \U0001f44c\U0001f3fb", _generate_new_inline_keyboard(eventid, itemid, "excluded", True))
            else:
                return (u"Item acknowledged \U0001f44c\U0001f3fb", _generate_new_inline_keyboard(eventid, itemid, "original", True))
    elif action == "exclude":
        if user_id not in _ADMINS: 
            return (u"\u2639\ufe0f You are not allowed to exclude items \u2639\ufe0f", False) 
        else:
            itemid = int(data["itemid"])
            eventid = int(data["eventid"])
            ack = _check_ack(eventid)
            if _check_excluded(itemid):
                _delist_item(itemid)
                return (u"Item delisted \U0001f44d\U0001f3fb", _generate_new_inline_keyboard(eventid, itemid, "original", ack))
            else:
                _exclude_item(itemid)
                return (u"Item excluded \U0001f44d\U0001f3fb", _generate_new_inline_keyboard(eventid, itemid, "excluded", ack))
    elif action == "host_exclude":
        if user_id not in _ADMINS:
            return (u"\u2639\ufe0f You are not allowed to exclude items \u2639\ufe0f", False)
        else:
            itemid = int(data["itemid"])
            eventid = int(data["eventid"])
            ack = _check_ack(eventid)
            hostname = data["hostname"]
            if _check_host_excluded(hostname): #Host already excluded, will delist it
                _delist_host(hostname)	
                return (u"Item delisted \U0001f44d\U0001f3fb", _generate_new_inline_keyboard(eventid, itemid, "original", ack, True))
            else: #Host not excluded, will do it
                _exclude_host(hostname)
                return (u"Item delisted \U0001f44d\U0001f3fb", _generate_new_inline_keyboard(eventid, itemid, "original", ack, False))
    elif action == "call":
        phone_to = "10105" # duty 
        if user_id in _PHONES:
            phone_from = _PHONES[user_id]
        else:
            return (u"\u2639\ufe0f Don't know your phone number \u2639\ufe0f", False)
        payload = {"event":"call",
                   "login": "wf_api_user", 
                   "password": "password",
                   "phone1": phone_from,
                   "phone2": phone_to
                  }
        wf_resp = requests.get("https://wfurl.example.com/phone_api.php", json = payload)
        try: 
            if wf_resp.json()[u'message'] == 'Call success':
                return (u"Call Started \U0001f44c\U0001f3fb", False)
            else:
                return (u"\u2639\ufe0f An error occured \u2639\ufe0f", False)
        except:
            return (u"\u2639\ufe0f An error occured \u2639\ufe0f", False)
    elif action == "register":
        return (u"\u2639\ufe0f Not implemented yet \u2639\ufe0f", False)
    else: 
        return (u"\u2639\ufe0f ERROR \u2639\ufe0f", False)


def _exclude_item(item_id):
    result = _db.excluded.insert_one({"itemid": item_id, 
                                     "till": "forever", 
                                     "added": datetime.now()}) 
    insert_id = result.inserted_id
    _logger.info("Inserting response {0}".format(insert_id))
    return True


    
def _delist_item(item_id):
    result = _db.excluded.delete_one({"itemid": item_id})
    return True
  
def _exclude_host(hostname):
    result = _db.excluded_host.insert_one({"till": "forever", "hostname": hostname, "added": datetime.now()})
    insert_id = result.inserted_id
    _logger.info("Inserting response {0}".format(insert_id))
    return True

def _delist_host(hostname):
    result = _db.excluded_host.delete_one({"hostname": hostname})
    return True


def _check_excluded(item_id):
    result = _db.excluded.find({"itemid": item_id}).count()
    if result == 0: return False
    else: return True

def _check_host_excluded(hostname):
    result = _db.excluded_hots.find({"hostname": hostname}).count()
    if result == 0: return False
    else: return True
