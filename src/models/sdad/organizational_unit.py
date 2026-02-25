# import mongoengine as me
# from src.models.apografi.embedded import Spatial, Address
# from src.models.apografi.dictionary import Dictionary
# from src.models.apografi.timestamp import TimeStampedModel

# from src.models.utils import JSONEncoder, Error
# import json
# import redis

# r = redis.Redis()

import mongoengine as me
from src.models.sdad.embedded import (
  organizationCodeDoc, supervisorUnitCodeDoc, PurposeDoc, SpatialDoc,
  UnitTypeDoc, MainAddressDoc, SecondaryAddressesDoc
)
from src.models.sdad.timestamp import TimeStampedModel
from src.models.utils import JSONEncoder, Error
import json

# A model for every organizational unit from https://hr.apografi.gov.gr/api.html#genikes-plhrofories-monades


class OrganizationalUnit(TimeStampedModel):
    meta = {
      "collection": "organizational-units",
      "db_alias": "sdad",
      "indexes": ["organizationCode.code", "supervisorUnitCode.code", "preferredLabel"],
    }

    code = me.StringField()
    organizationCode = me.EmbeddedDocumentField(organizationCodeDoc, null=True)
    supervisorUnitCode = me.EmbeddedDocumentField(supervisorUnitCodeDoc, null=True)
    preferredLabel = me.StringField()
    alternativeLabels = me.ListField(me.StringField(max_length=200))
    purpose = me.EmbeddedDocumentListField(PurposeDoc)
    spatial = me.EmbeddedDocumentListField(SpatialDoc)
    identifier = me.StringField(null=True)
    unitType = me.EmbeddedDocumentField(UnitTypeDoc)
    description = me.StringField(null=True)
    email = me.StringField(null=True)
    telephone = me.StringField(null=True)
    url = me.StringField(null=True)
    mainAddress = me.EmbeddedDocumentField(MainAddressDoc,null=True)
    secondaryAddresses = me.EmbeddedDocumentListField(SecondaryAddressesDoc, null=True)
    remitsFinalized = me.BooleanField(default=False)
    elasticSync = me.BooleanField(default=False)
    
    def to_json(self):
      data = self.to_mongo().to_dict()
      data.pop("_id")
      data = {k: v for k, v in data.items() if v}
      return json.dumps(data, cls=JSONEncoder)
