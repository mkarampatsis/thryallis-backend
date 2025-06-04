import mongoengine as me
from datetime import datetime
from src.models.upload import FileUpload

class FloorPlans(me.EmbeddedDocument):
  level = me.StringField(required=True)
  num = me.IntField(required=True)
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

class Facility(me.Document):
  meta = {
    "collection": "facilities", 
    "db_alias": "resources",
    "indexes": [
      {"fields": ["organizationCode", "kaek", "useOfFacility"], "unique": True}
    ],
  }

  organization = me.StringField(required=True)
  organizationCode = me.StringField(required=True)
  organizationalUnit = me.StringField(required=False)
  organizationalUnitCode = me.StringField(required=False)
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
  uniqueUserOfFacility = me.StringField(required=True)
  coveredPremisesArea = me.StringField(required=True)
  floorsOrLevels = me.IntField(required=True)
  floorPlans = me.ListField(me.EmbeddedDocumentField(FloorPlans)) 
  addressOfFacility = me.EmbeddedDocumentField(Address)
  finalized = me.BooleanField(default=False),
  elasticSync = me.BooleanField(default=False)