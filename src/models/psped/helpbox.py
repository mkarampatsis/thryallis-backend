import mongoengine as me
from datetime import datetime
from bson import ObjectId
from src.models.upload import FileUpload

class Question(me.EmbeddedDocument):
    id = me.ObjectIdField(default=ObjectId, required=True)
    questionText = me.StringField(required=True)
    answerText = me.StringField()
    questionFile = me.ReferenceField(FileUpload)
    answerFile = me.ReferenceField(FileUpload)
    whenAsked = me.DateTimeField(default=datetime.now)
    whenAnswered = me.DateTimeField()
    fromWhom = me.StringField()
    answered= me.BooleanField(default=False)
    published= me.BooleanField(default=False)

class Helpbox(me.Document):
    meta = {"collection": "helpbox", "db_alias": "psped"}

    key = me.StringField(required=True)
    email = me.EmailField(required=True)
    firstName = me.StringField(required=True)
    lastName = me.StringField(required=True)
    organizations = me.ListField(me.StringField(), default=[])
    questionTitle = me.StringField(required=True)
    questions = me.EmbeddedDocumentListField(Question, required=True)
    toWhom = me.StringField()
    finalized = me.BooleanField(default=False)  
