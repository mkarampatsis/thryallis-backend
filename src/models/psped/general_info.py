import mongoengine as me
from datetime import datetime
from src.models.upload import FileUpload

class GeneralInfo(me.Document):
  meta = {"collection": "general_info", "db_alias": "psped"}

  email = me.StringField(required=True)
  taxid = me.StringField(required=True)
  firstName = me.StringField(required=True)
  lastName = me.StringField(required=True)
  title = me.StringField(required=True)
  text = me.StringField(required=True)
  when = me.DateTimeField(default=datetime.now)
  file = me.ListField(me.ReferenceField(FileUpload))
  category = me.StringField(required=True)
  enableGoogleAuth = me.BooleanField(required=True, default=False) 
