import mongoengine as me
from src.models.psped.foreas import Foreas
from src.models.ota.instruction_act import InstructionAct
from src.models.apografi.organizational_unit import OrganizationalUnit as Monada


class RegulatedObject(me.EmbeddedDocument):
  regulatedObjectType = me.StringField(required=True, choices=["organization", "organizationalUnit", "remit", "ota"])
  # regulatedObjectCode = me.StringField(required=True)
  regulatedObjectId = me.ObjectIdField(required=True)
  # regulatedObjectObjectId = me.StringField()


class Abolition(me.EmbeddedDocument):
  abolishingInstructionProvisionCode = me.StringField(required=True)
  entryDate = me.DateTimeField(required=True)
  userCode = me.StringField(required=True)


class InstructionProvisionSpecs(me.EmbeddedDocument):
  meros = me.StringField()
  kefalaio = me.StringField()
  arthro = me.StringField()
  paragrafos = me.StringField()
  edafio = me.StringField()
  pararthma = me.StringField()

  def validate(self, clean=True):
    super(InstructionProvisionSpecs, self).validate(clean)
    fields = [self.meros, self.kefalaio, self.arthro, self.paragrafos, self.edafio, self.pararthma]
    if not any(fields):
      raise me.ValidationError("Κάποιο πεδίο της Διάταξης πρέπει να συμπληρωθεί")


class InstructionProvision(me.Document):
  meta = {
    "collection": "instruction_provisions",
    "db_alias": "psped",
    "indexes": [
      { "fields": [
        "regulatedObject.regulatedObjectType", "regulatedObject.regulatedObjectId", 
        "instructionAct",
        "instructionProvisionSpecs.meros", "instructionProvisionSpecs.arthro", "instructionProvisionSpecs.paragrafos", "instructionProvisionSpecs.edafio", "instructionProvisionSpecs.pararthma"
      ], "unique": True, "name":"regulatedObject_instructionAct_instructionProvisionSpecs" }
  ],
    # From index I have removed instructionProvisionSpecs.kefalaio
  }

  # regulatedObject = me.EmbeddedDocumentField(RegulatedObject, required=True, unique_with=["instructionAct", "instructionProvisionSpecs"])
  regulatedObject = me.EmbeddedDocumentField(RegulatedObject, required=True)
  instructionAct = me.ReferenceField(InstructionAct, required=True)
  instructionProvisionSpecs = me.EmbeddedDocumentField(InstructionProvisionSpecs, required=True)
  instructionProvisionText = me.StringField(required=True)
  abolition = me.EmbeddedDocumentField(Abolition)

  def to_dict(self):
    return {
      "_id": str(self.id),
      "regulatedObject": self.regulatedObject.to_mongo() if self.regulatedObject else None,
      "instructionAct": self.instructionAct.to_dict() if hasattr(self.instructionAct, "to_dict") else {
        "_id": str(self.instructionAct.id),
        **self.instructionAct.to_mongo().to_dict()
      },
      "instructionProvisionSpecs": self.instructionProvisionSpecs.to_mongo() if self.instructionProvisionSpecs else None,
      "instructionProvisionText": self.instructionProvisionText,
      "abolition": self.abolition.to_mongo() if self.abolition else None
    }

  # A static method that receives an array of new instruction provisions and saves them to the database
  @staticmethod
  def save_new_instruction_provisions(instruction_provisions, regulatedObject):
    instruction_provisions_docs = []
    for provision in instruction_provisions:
      instructionActKey = provision["instructionActKey"]
      instructionAct = InstructionAct.objects.get(instructionActKey=instructionActKey)
      instructionProvisionSpecs = provision["instructionProvisionSpecs"]
      instructionProvisionText = provision["instructionProvisionText"]
      instructionProvision = InstructionProvision(
        regulatedObject=regulatedObject,
        instructionAct=instructionAct,
        instructionProvisionSpecs=instructionProvisionSpecs,
        instructionProvisionText=instructionProvisionText,
      ).save()
      instruction_provisions_docs.append(instructionProvision)
    return instruction_provisions_docs

  @staticmethod
  def regulated_object(code, instructionProvisionType):
    if instructionProvisionType == "organization":
      foreas = Foreas.objects.get(code=code)
      return RegulatedObject(regulatedObjectType=instructionProvisionType, regulatedObjectId=foreas.id)
    elif instructionProvisionType == "organizationalUnit":
      monada = Monada.objects.get(code=code)
      return RegulatedObject(regulatedObjectType=instructionProvisionType, regulatedObjectId=monada.id)
    elif instructionProvisionType == "remit":
      return RegulatedObject(regulatedObjectType=instructionProvisionType, regulatedObjectId=code)
    else:
      raise ValueError("Invalid instructionProvisionType")
