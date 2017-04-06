import requests
from pprint import pprint



class Bot:
    def __init__(self, id):
        self.id = id
        #try:self.offset = requests.get('https://api.telegram.org/bot{0}/getUpdates'.format(self.id)).json()['result'][-1]['update_id']
        #except:self.offset = 0
        #print self.offset
        
        
# No need, webhooks for updates        
# Get list of diff updates: {type:  type of messgae, meesage: Whole JSON message object}        
"""
    def getUpdates(self):
        messages = []
        res = requests.get('https://api.telegram.org/bot{0}/getUpdates'.format(self.id), data={'offset': self.offset, 'limit': 50, 'timeout': 0})
        for upd in res.json()['result']:
            if not upd: continue
            #pprint(upd)
            if  'message' in  upd:
                #pprint(upd)
                messages.append({'type':'message', 'message': upd['message']})
                self.offset =  upd['update_id'] + 1
            elif 'callback_query' in upd:
                messages.append({'type':'callback_query', 'message': upd['callback_query']})
                self.offset =  upd['update_id'] + 1
            #elif: Join group action, leave group action, etc...
            else : continue
        return messages
"""    
    
    def sendMessage(self, id, textmessage, inline_keyboard = ""):
        resp = requests.get('https://api.telegram.org/bot{0}/sendMessage'.format(self.id), json = {'chat_id': id, 'text': textmessage, 'reply_markup': inline_keyboard})
        return resp.json()

    def updateMessage(self, id, m_id, textmessage, inline_keyboard = ""): 	  #Update some message
        resp = requests.get('https://api.telegram.org/bot{0}/editMessageText'.format(self.id), json = {'chat_id':id, 'text': textmessage,  'message_id': m_id, 'reply_markup': inline_keyboard}).json()
        # No try except on retrieve json obj, only hardcore
        return resp

    def updateMessageInline(self, id, m_id, inline_keyboard = ""):
        resp = requests.get('https://api.telegram.org/bot{0}/editMessageReplyMarkup'.format(self.id), json = {'chat_id':id, 'message_id': m_id, 'reply_markup': inline_keyboard}).json()
        return resp
    
    def answerInline(self, id, call_id, textmessage, show_alert = True):    #Popup notification on some action
        resp = requests.get('https://api.telegram.org/bot{0}/answerCallbackQuery'.format(self.id), json = {'chat_id': id, 'callback_query_id': call_id, 'text': textmessage}).json()
        return resp

