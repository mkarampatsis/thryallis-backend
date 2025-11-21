import mongoengine as me
from datetime import datetime
from src.models.timestamp import TimeStampedModel
from src.config import MONGO_OTA_DB
from src.models.psped.legal_provision import LegalProvision

class PublicPolicyAgency(me.EmbeddedDocument):
  organization = me.StringField(required=True)
  organizationCode = me.StringField(required=True)
  organizationalUnit = me.StringField(required=True)
  organizationalUnitCode = me.StringField(required=True)

class Ota(TimeStampedModel):
  meta = {"collection": "remits", "db_alias": MONGO_OTA_DB}

  remitText = me.StringField(required=True)
  remitCompetence = me.StringField(
    required=True,
    choices=[
      'Περιφέρειες',
      'Δήμοι',
      'Νησιωτικοί Δήμοι',
      'Ορεινοί Δήμοι',
      'Μητροπολιτικές Αρμοδιότητες'
    ]
  )
  remitType = me.StringField(
    required=True,
    choices=[
      'Επιτελική',
      'Εκτελεστική',
      'Υποστηρικτική',
      'Ελεγκτική',
      'Παρακολούθησης αποτελεσματικής πολιτικής και αξιολόγησης αποτελεσμάτων'
    ],
  )
  remitLocalOrGlobal = me.StringField(
    required=True,
    choices=[
      'Αυτοδιοικητική Αρμοδιότητα (Τοπική)',
      'Αρμοδιότητα που συνιστά αποστολή του κράτους (Κρατική)'
    ],
  )
  legalProvisionRefs = me.ListField(me.ReferenceField(LegalProvision))
  instructionProvisionRefs = me.ListField(me.ReferenceField(LegalProvision))
  publicPolicyAgency = me.EmbeddedDocumentField(PublicPolicyAgency)
  status = me.StringField(choices=["ΕΝΕΡΓΗ", "ΑΝΕΝΕΡΓΗ"], default="ΕΝΕΡΓΗ")
  finalized = me.BooleanField()
  elasticSync = me.BooleanField(default=False)

  def to_dict(self):
    return {
      "_id": str(self.id),
      "organizationalUnitCode": self.organizationalUnitCode,
      "remitText": self.remitText,
      "remitCompetence": self.remitCompetence,
      "remitType": self.remitType,
      "remitLocalOrGlobal": self.remitLocalOrGlobal,
      "legalProvisionRefs": [provision for provision in self.legalProvisionRefs.to_mongo()] if self.legalProvisionRefs else [],
      "instructionProvisionRefs": [provision for provision in self.instructionProvisionRefs.to_mongo()] if self.instructionProvisionRefs else [],
      "publicPolicyAgency": self.publicPolicyAgency.to_mongo() if self.publicPolicyAgency else None,
      "status": self.status,
      "finalized": self.finalized,
      "createdAt": self.createdAt,
      "updatedAt": self.updatedAt,
    } 

# [str(ref.id) for ref in self.legalProvisionRefs]
  # self.apografi.foreas.to_mongo() if self.apografi.foreas else None,