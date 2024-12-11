import mongoengine as me
from datetime import datetime

class Helpbox(me.Document):
    meta = {"collection": "helpbox", "db_alias": "psped"}

    email = me.EmailField(required=True)
    firstName = me.StringField(required=True)
    lastName = me.StringField(required=True)
    organizations = me.ListField(me.StringField(), default=[])
    questionTitle = me.StringField(required=True)
    questionText = me.StringField(required=True)
    answerText = me.StringField()
    toWhom = me.StringField()
    when = me.DateTimeField(default=datetime.now)
    status = me.BooleanField(default=False)
    
