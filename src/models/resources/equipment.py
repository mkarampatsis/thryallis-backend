import mongoengine as me
from datetime import datetime
from src.models.resources.facility import Facility
from src.models.resources.space import Space
from src.models.upload import FileUpload
from src.models.timestamp import TimeStampedModel

class itemDescription(me.EmbeddedDocument):
  value = me.StringField(required=True)
  description = me.StringField(required=True)
  info = me.StringField(required=True)

class itemQuantity(me.EmbeddedDocument):
  distinctiveNameOfFacility = me.StringField(required=True)
  facilityId = me.ReferenceField(Facility)
  spaceName = me.StringField(required=True)
  spaceId = me.ReferenceField(Space)
  quantity = me.IntField(required=True)
  codes = me.StringField()

class Equipment(TimeStampedModel):
  meta = {
    "collection": "equipments", 
    "db_alias": "resources"
  }

  organization = me.StringField(required=True)
  organizationCode = me.StringField(required=True)
  hostingFacility = me.ReferenceField(Facility)
  spaceWithinFacility =  me.ReferenceField(Space)
  resourceCategory = me.StringField(required=True)
  resourceSubcategory = me.StringField(required=True)
  kind = me.StringField(required=True)
  type = me.StringField(required=True)
  itemDescription = me.ListField(me.EmbeddedDocumentField(itemDescription))
  itemQuantity =  me.ListField(me.EmbeddedDocumentField(itemQuantity))
  acquisitionDate = me.DateTimeField(required=True)
  depreciationDate = me.DateTimeField()
  status = me.StringField(required=True)
  elasticSync = me.BooleanField(default=False)