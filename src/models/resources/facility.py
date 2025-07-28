import mongoengine as me
from datetime import datetime
from src.models.upload import FileUpload
from src.models.timestamp import TimeStampedModel

class FloorPlans(me.EmbeddedDocument):
  level = me.StringField(required=True)
  num = me.StringField(required=True)
  floorArea = me.StringField(required=True)
  floorPlan= me.ListField(me.ReferenceField(FileUpload))

class Address(me.EmbeddedDocument):
  street = me.StringField(required=True)
  number = me.StringField(required=True)
  postcode = me.StringField(required=True)
  area = me.StringField(required=True)
  municipality = me.StringField(required=True)
  geographicRegion = me.StringField(required=True)
  country = me.StringField(required=True)

class Facility(TimeStampedModel):
  meta = {
    "collection": "facilities", 
    "db_alias": "resources",
    "indexes": [
      {"fields": ["organizationCode", "kaek", "useOfFacility"], "unique": True}
    ],
  }

  organization = me.StringField(required=True)
  organizationCode = me.StringField(required=True)
  kaek = me.StringField(required=True)
  belongsTo = me.StringField(required=True)
  distinctiveNameOfFacility = me.StringField(required=True)
  useOfFacility = me.StringField(
    required=True,
    choices=[
      "Κτίριο Γραφείων (Υπηρεσίες)",
      "Εκπαιδευτική Μονάδα",
      "Νοσηλευτική Μονάδα",
      "Κατασκευαστική Μονάδα/Εργοστάσιο",
      "Αποθήκη/χώρος logistics",
      "Parking ",
      "Αθλητική εγκατάσταση",
      "Συνεδριακή/Εκθεσιακή Εγκατάσταση",
      "Πυροσβεστικός σταθμός",
      "Σωφρονιστικό Κατάστημα",
      "Εκκλησία",
      "Νεκροταφείο",
      "Αερολιμένας",
      "Λιμένας",
      "Αιγιαλός",
      "Οικόπεδο (χωρίς ειδικότερη χρήση).",
      "Άλλη χρήση"
    ],
  )
  uniqueUseOfFacility = me.BooleanField(required=True)
  private = me.BooleanField(required=True)
  coveredPremisesArea = me.StringField(required=True)
  floorsOrLevels = me.IntField(required=True)
  floorPlans = me.ListField(me.EmbeddedDocumentField(FloorPlans)) 
  addressOfFacility = me.EmbeddedDocumentField(Address)
  finalized = me.BooleanField()
  elasticSync = me.BooleanField(default=False)