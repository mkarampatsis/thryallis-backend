import mongoengine as me
from datetime import datetime
from bson import ObjectId

class Question(me.EmbeddedDocument):
    id = me.ObjectIdField(default=ObjectId, required=True)
    questionText = me.StringField(required=True)
    answerText = me.StringField()
    # file?: string | null;
    whenAsked = me.DateTimeField(default=datetime.now)
    whenAnswered = me.DateTimeField()
    fromWhom = me.StringField()
    answered= me.BooleanField(default=False)
    published= me.BooleanField(default=False)

class Helpbox(me.Document):
    meta = {"collection": "helpbox", "db_alias": "psped"}

    email = me.EmailField(required=True)
    firstName = me.StringField(required=True)
    lastName = me.StringField(required=True)
    organizations = me.ListField(me.StringField(), default=[])
    questionTitle = me.StringField(required=True)
    questions = me.EmbeddedDocumentListField(Question, required=True)
    toWhom = me.StringField()
    finalized = me.BooleanField(default=False)  
