import mongoengine as me
from datetime import datetime
from src.models.timestamp import TimeStampedModel

class Types(me.EmbeddedDocument):
  name = me.StringField(required=True)
  itemDescription = me.ListField()

class Kind(me.EmbeddedDocument):
  name = me.StringField(required=True)
  type = me.ListField(me.EmbeddedDocumentField(Types))

class EquipmentConfig(TimeStampedModel):
  meta = {
    "collection": "equipment_config", 
    "db_alias": "resources",
  }

  resourceSubcategory = me.StringField(required=True)
  kind = me.ListField(me.EmbeddedDocumentField(Kind)) 
