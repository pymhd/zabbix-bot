#!/usr/bin/python

import os
import sys
import requests
import json
import re
import logging
from datetime import datetime
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import pymongo

#  send_telegram_message.py "reportsrv.2com.net; 46178; PROBLEM; test item fro api; 1 item;Reportsrv;file exists" 

class Bot:
    def __init__(self):
        self.__message_url = "https://api.telegram.org/bot[key]/sendMessage"
        self.__photo_url = "https://api.telegram.org/bot[key]/sendPhoto"
        self.__chat_id = "-98562467"  #it etesh
        #self.__chat_id = "93999207"   # aram
    
    def send_message(self, Message, reply_murkup, replyid):
        res =requests.get(self.__message_url, json = {'chat_id': self.__chat_id, 'text': Message, 'reply_to_message_id': replyid, "reply_markup": reply_murkup})          
        return res.json()

    def send_colorized_problem(self, picture, Message, reply_murkup, replyid):
        pic = open(picture,'rb')
        img = {'photo': pic} 
        res =requests.get(self.__photo_url,  data={'chat_id': self.__chat_id, 'caption': Message, "reply_markup": reply_murkup}, files = img)
        return res.json()


class MyMongo:
    def __init__(self):
        __client = pymongo.MongoClient('mongodb://user:password@mongodb.example.com:27017')
        self.__db = __client.zabbix_notification
    
    def exclude(self, itemid):
        resp = self.__db.excluded.insert_one({"itemid": itemid, "added": datetime.now(), "till": "forever"})
        if a.inserted_id: return True
        else: return False
        
    def is_excluded(self, itemid):
        count = self.__db.excluded.find({"itemid": itemid}).count()
        if count != 0: return True
        else: return False
        
    def add_event(self, message_id, itemid, last_value, state):
        if self.__db.item_state.find({"itemid": itemid}).count() == 0:  # first time itemid was met
            self.__db.item_state.insert_one({"itemid": itemid, "state": state, "message_id": message_id, "last_value": last_value})
        else:
            self.__db.item_state.update_one({"itemid": itemid}, {"$set": {"state": state, "message_id": message_id, "last_value": last_value}})
        return True
    
    def update_event(self, itemid, last_value, state):
        self.__db.item_state.update_one({"itemid": itemid}, {"$set": {"state": state, "last_value": last_value}})    
        return True
        
    def get_event_replyid(self, itemid):
        item = self.__db.item_state.find_one({"itemid": itemid, "state": "PROBLEM"}, {"_id": 0, "message_id": 1}) 
        if item: return item["message_id"]
        else: return False
        
    def lastvalue_changed(self, itemid, lastvalue):
        try: cur_val = self.__db.item_state.find_one({"itemid": itemid}, {"_id": 0, "last_value": 1} )["last_value"]
        except: return False
        if cur_val == lastvalue:
            return False
        else:
            return True
    
  
    
    
if __name__ == "__main__":
    os.chdir("/usr/local/comcom/zabbix")
    
    # Classes init
    m = MyMongo()
    bot = Bot()
    
    # Logging section
    logging.basicConfig(
                        filename = "notification.log", 
                        filemode = 'a', 
                        format = '%(asctime)s, %(levelname)s, %(message)s', 
                        datefmt = '%Y-%m-%d %H:%M:%S', 
                        level = logging.DEBUG
                        )
    
    # HardCoded Values
    trigger_status = sys.argv[-1].split(';')[2]
    itemid = int(sys.argv[-1].split(';')[1])
    key_name = sys.argv[-1].split(';')[3]
    last_value =  sys.argv[-1].split(';')[-4].strip()
    host_name = sys.argv[-1].split(';')[0]
    event_id = sys.argv[-1].split(';')[-1]
    trigger_name =  sys.argv[-1].split(';')[-2]
    host_descr =  sys.argv[-1].split(';')[-3]

    logging.info('Starting procedure for host {0}'.format(host_name))
    logging.debug('Got param "itemid" = {0}'.format(itemid))
    logging.debug('Got param "trigger status" = {0}'.format(trigger_status))
    logging.debug('Got param "key name" = {0}'.format(key_name))
    logging.debug('Got param "last value" = {0}'.format(last_value))
    logging.debug('Got param "Trigger name" = {0}'.format(trigger_name))
    logging.debug('Got param "Visible name " = {0}'.format(host_descr))
    logging.debug("Got param EventId = {0}".format(event_id))
    
        
    sw_pattern = re.compile(r".*has changed to (DOWN|UP).*")
    if sw_pattern.match(trigger_name): is_sw = True
    else: is_sw = False
    
    #Kondrat deserves the unique code block
    EXCLUDE_KEYWORDS = ['Sybil']
    for item in EXCLUDE_KEYWORDS:
        if item in trigger_name.split():
            logging.info("This is  TRASH item, won't send any message, exiting")
            sys.exit()
    # End of Kondrat block :)                                                
   
    # skip excluded items
    if m.is_excluded(itemid): 
        logging.info("Excluded item, skipping...")
        sys.exit()
    
    if trigger_status.strip() == 'PROBLEM':
        if is_sw:  # Check if it is one of status has changed to UP|DOWN triggers
            message_to_reply = m.get_event_replyid(itemid)
            if  message_to_reply and "UP" in trigger_name:
                print "got mes to reply"
                Message  = "Changed to UP state"
                result = bot.send_message(Message, "", message_to_reply)
                m.update_event(itemid, last_value, "OK")
                sys.exit()
            elif "UP" in trigger_name:
                sys.exit()
            else: 
                pass 
        if host_descr: name = host_descr
        else: name = host_name
        Message = '"{0}": {1} ({2})'.format(name, trigger_name, last_value)
        #print "Regular process"
        #Inline keyboard structure
        #return [ [1 line with buttons], [2 line with buttons],..., [n line with buttons]]
        #{"callback_data": "Hidden data", "text": "text to show"}  # one button example
        # final view:
        #[[{"callback_data": "data", "text": "txt"}, {"callback_data": "data2", "text": "txt2"}], [...]
        reply_markup = {"inline_keyboard": 
                        [
                         [{"callback_data": """{{"action": "ack", "itemid": {0}, "eventid": {1}}}""".format(itemid, event_id), "text": u"\U0001f4ac"}, \
                          {"callback_data": """{{"action": "exclude", "itemid": {0}, "eventid": {1}}}""".format(itemid, event_id), "text": u"\u274c"}, \
                          {"callback_data": """{"action": "register"}""", "text": u"\U0001f6e0"}, \
                          {"callback_data": """{"action": "call"}""", "text": u"\U0001f4de"}
                         ]
                       ]
                      } 
        print reply_markup
        response = bot.send_message(Message, reply_markup, "")
        print response
        msgid = response['result']['message_id']
        m.add_event(msgid, itemid, last_value, "PROBLEM")
    elif trigger_status.strip() == "OK":
        if is_sw:
            if m.lastvalue_changed(itemid, last_value):
                Message  = "Changed to UP state"
                message_to_reply = m.get_event_replyid(itemid)
                if not message_to_reply: 
                    sys.exit(550)
                result = bot.send_message(Message, "", message_to_reply)
                m.update_event(itemid, last_value, "OK")
            else:
                logging.info("Last value is the same, won't send Restored message")
        else:
            message_to_reply = m.get_event_replyid(itemid)    
            print message_to_reply
            if not message_to_reply: sys.exit(550)
            Message  = "Restored"        
            result = bot.send_message(Message, "", message_to_reply)
            print result
            m.update_event(itemid, "OK")


