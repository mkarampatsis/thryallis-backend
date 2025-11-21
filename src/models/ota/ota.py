import mongoengine as me
from datetime import datetime
from src.models.timestamp import TimeStampedModel
from src.config import MONGO_PSPED_DB
from src.models.psped.legal_provision import LegalProvision

class PublicPolicyAgency(me.EmbeddedDocument):
  organization = me.StringField(required=True)
  organizationCode = me.StringField(required=True)
  organizationalUnit = me.StringField(required=True)
  organizationalUnitCode = me.StringField(required=True)
  subOrganizationOf = me.StringField(required=True)
  supervisorUnitCode = me.StringField(required=True)
  unitType = me.IntField(required=True)

class Ota(TimeStampedModel):
  meta = {"collection": "ota", "db_alias": MONGO_PSPED_DB}

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
  finalized = me.BooleanField(default=False)
  elasticSync = me.BooleanField(default=False)

  def to_dict(self):
    def provision_to_dict(provision: LegalProvision):
      if not provision:
          return None

      return {
        "_id": str(provision.id),
        "regulatedObject": provision.regulatedObject.to_mongo(),
        "legalAct": (
            provision.legalAct.to_mongo()
            if provision.legalAct else None
        ),
        "legalProvisionSpecs": provision.legalProvisionSpecs.to_mongo(),
        "legalProvisionText": provision.legalProvisionText,
        "abolition": provision.abolition.to_mongo() if provision.abolition else None
      }

    # Convert legalProvisionRefs (ObjectIds) → actual docs
    legal_provisions = []
    for ref in self.legalProvisionRefs:
      provision = LegalProvision.objects(id=ref.id).first()
      if provision:
          legal_provisions.append(provision_to_dict(provision))

    instruction_provisions = []
    for ref in self.instructionProvisionRefs:
      provision = LegalProvision.objects(id=ref.id).first()
      if provision:
          instruction_provisions.append(provision_to_dict(provision))

    return {
      "_id": str(self.id),
      "remitText": self.remitText,
      "remitCompetence": self.remitCompetence,
      "remitType": self.remitType,
      "remitLocalOrGlobal": self.remitLocalOrGlobal,
      "legalProvisionRefs": legal_provisions,
      "instructionProvisionRefs": instruction_provisions,
      "publicPolicyAgency": self.publicPolicyAgency.to_mongo() if self.publicPolicyAgency else None,
      "status": self.status,
      "finalized": self.finalized,
      "elasticSync": self.elasticSync,
      "createdAt": self.createdAt,
      "updatedAt": self.updatedAt,
    }

# [str(ref.id) for ref in self.legalProvisionRefs]
  # self.apografi.foreas.to_mongo() if self.apografi.foreas else None,