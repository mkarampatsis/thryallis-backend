import mongoengine as me
from datetime import datetime
from src.models.resources.facility import Facility
from src.models.upload import FileUpload
from src.models.timestamp import TimeStampedModel


class FloorPlans(me.EmbeddedDocument):
  level = me.StringField(required=True)
  num = me.StringField(required=True)

class SpaceUse(me.EmbeddedDocument):
  type = me.StringField(required=True)
  subtype = me.StringField(required=True)
  space = me.StringField(required=True)

class Space(TimeStampedModel):
  meta = {
    "collection": "space", 
    "db_alias": "resources",
  }

  facilityId = me.ReferenceField(Facility)
  spaceName = me.StringField(required=True)
  spaceUse = me.EmbeddedDocumentField(SpaceUse)
  spaceArea = me.StringField(required=False)
  spaceLength = me.StringField(required=False)
  spaceWidth = me.StringField(required=True)
  entrances = me.StringField(required=True)
  windows = me.StringField(required=True)
  floorPlans = me.EmbeddedDocumentField(FloorPlans) 
  elasticSync = me.BooleanField(default=False)
