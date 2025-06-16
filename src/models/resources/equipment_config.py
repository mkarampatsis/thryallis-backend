import mongoengine as me
from datetime import datetime
from src.models.timestamp import TimeStampedModel

class Values(me.EmbeddedDocument):
  category = me.StringField(required=True)
  values = me.ListField()

class Kind(me.EmbeddedDocument):
  type = me.StringField(required=True)
  category = me.ListField(required=True)
  values = me.ListField(me.EmbeddedDocumentField(Values))

class EquipmentConfig(TimeStampedModel):
  meta = {
    "collection": "equipment_config", 
    "db_alias": "resources",
  }

  type = me.StringField(required=True)
  kind = me.ListField(me.EmbeddedDocumentField(Kind)) 
