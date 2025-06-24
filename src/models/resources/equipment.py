import mongoengine as me
from datetime import datetime
from src.models.resources.space import Space
from src.models.upload import FileUpload
from src.models.timestamp import TimeStampedModel

class Values(me.EmbeddedDocument):
  value = me.StringField(required=True)
  description = me.StringField(required=True)
  info = me.StringField(required=True)

class Equipment(TimeStampedModel):
  meta = {
    "collection": "equipments", 
    "db_alias": "resources"
  }

  organization = me.StringField(required=True)
  organizationCode = me.StringField(required=True)
  spaceId =  me.ReferenceField(Space)
  type = me.StringField(required=True)
  kind = me.StringField(required=True)
  category = me.StringField(required=True)
  values = me.ListField(me.EmbeddedDocumentField(Values))
  elasticSync = me.BooleanField(default=False)