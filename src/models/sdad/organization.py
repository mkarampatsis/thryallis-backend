import json
import mongoengine as me
from src.models.sdad.embedded import (
  SubOrganizationDoc, OrganizationDoc, 
  ContactDoc, FekDoc, MainAddressDoc
)
from src.models.sdad.timestamp import TimeStampedModel
import redis

from src.models.utils import JSONEncoder, Error


# A model for every organization from https://hr.apografi.gov.gr/api.html#genikes-plhrofories-foreis


class Organization(TimeStampedModel):
  meta = {
    "collection": "organizations",
    "db_alias": "sdad",
    "indexes": ["preferredLabel"],
  }

  code = me.StringField(required=True, unique=True)
  preferredLabel = me.StringField()
  subOrganizationOf = me.EmbeddedDocumentField(SubOrganizationDoc, null=True)
  organizationType  = me.EmbeddedDocumentField(OrganizationDoc)
  description = me.StringField()
  url = me.StringField()
  contactPoint = me.EmbeddedDocumentField(ContactDoc, null=True)
  vatId = me.StringField()
  status = me.StringField()
  foundationDate = me.DateTimeField(null=True)
  terminationDate = me.DateTimeField(null=True)
  mainDataUpdateDate = me.DateTimeField(null=True)
  organizationStructureUpdateDate = me.DateTimeField(null=True)
  foundationFek = me.EmbeddedDocumentField(FekDoc, null=True)
  mainAddress = me.EmbeddedDocumentField(MainAddressDoc, null=True)
  elasticSync = me.BooleanField(default=False)
  pspedSync = me.BooleanField(default=False)

  def to_mongo_dict(self):
    mongo_dict = self.to_mongo().to_dict()
    mongo_dict.pop("_id")
    return mongo_dict

  def to_json(self):
    data = self.to_mongo().to_dict()
    data.pop("_id")
    data = {k: v for k, v in data.items() if v}
    return json.dumps(data, cls=JSONEncoder) 