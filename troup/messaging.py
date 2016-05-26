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


class DictEncoder(json.JSONEncoder):
    
    def default(self, o):
        return o.__dict__


def serialize(msg, indent=None):
    return json.dumps(msg, indent=indent, cls=DictEncoder)


def deserialize(smsg, as_type=None, strict=False):
    msg_type = as_type or Message
    dmsg = json.loads(smsg)
    
    msg = msg_type()
    
    for name, value in dmsg.items():
        if hasattr(msg, name):
            setattr(msg, name, value)
        elif strict:
            raise Exception('No such property %s' % name)
    
    return msg 


def deserialize_dict(dval, as_type, strict=None):
    val = as_type()
    
    for name, value in dval.items():
        if hasattr(val, name):
            setattr(val, name, value)
        elif strict:
            raise Exception('No such property %s' % name)
    
    return val

