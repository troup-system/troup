from uuid import uuid4 as uuid4
import json

class Message:
    def __init__(self):
        self.id = None
        self.headers = {}
        self.data = None
    
    def __str__(self):
        return '<Message>(%s): Headers: %s; Data: %s;'%(self.id, self.headers, self.data)
    
    def __repr__(self):
        return self.__str__()

class MessageBuilder:
    def __init__(self):
        self.message = Message()
    
    def id(self, message_id):
        self.message.id = message_id
        return self
    
    def data(self, message_data):
        self.message.data = message_data
        return self
    
    def value(self, key, value):
        if not self.message.data:
            self.message.data = {}
        self.message.data[key] = value
        return self
    
    def header(self, name, value):
        self.message.headers[name] = value
        return self
    
    def build(self):
        if self.message.id is None:
            self.message.id = '%s'%uuid4()
        return self.message

def message(id=None, data=None):
    return MessageBuilder().id(id).data(data)



def serialize(msg, indent=None):
    return json.dumps(msg, indent=indent)


def deserialize(smsg, as_type=None, strict=False):
    msg_type = as_type or Message
    dmsg = json.reads(smsg)
    
    msg = msg_type()
    
    for name, value in msg.items():
        if hasattr(msg, name):
            setattr(msg, name, value)
        elif strict:
            raise Error('No such property %s' % name)
    
    return msg 


