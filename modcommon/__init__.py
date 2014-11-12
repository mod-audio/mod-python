import datetime
from bson.objectid import ObjectId

def json_handler(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    return None

