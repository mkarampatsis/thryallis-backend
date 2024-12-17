import mongoengine as me
from datetime import datetime

class Question(me.EmbeddedDocument):
    questionText = me.StringField(required=True)
    answerText = me.StringField()
    # file?: string | null;
    fromWhom = me.StringField()
    whenAsked = me.DateTimeField()
    whenAnswered = me.DateTimeField()
    answered= me.BooleanField(default=False)

class Helpbox(me.Document):
    meta = {"collection": "helpbox", "db_alias": "psped"}

    email = me.EmailField(required=True)
    firstName = me.StringField(required=True)
    lastName = me.StringField(required=True)
    organizations = me.ListField(me.StringField(), default=[])
    questionTitle = me.StringField(required=True)
    question = me.EmbeddedDocumentListField(Question, required=True)
    toWhom = me.StringField()
    when = me.DateTimeField(default=datetime.now)
    finalized = me.BooleanField(default=False)  
