import mongoengine as me
from datetime import datetime
from src.models.timestamp import TimeStampedModel

class Spaces(me.EmbeddedDocument):
  type = me.StringField(required=True)
  spaces = me.ListField(me.StringField(required=True))

class FacilityConfig(TimeStampedModel):
  meta = {
    "collection": "facility_config", 
    "db_alias": "resources",
  }

  type = me.StringField(required=True)
  spaces = me.ListField(me.EmbeddedDocumentField(Spaces)) 