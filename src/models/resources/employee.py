import mongoengine as me
from datetime import datetime
from src.models.upload import FileUpload
from src.models.timestamp import TimeStampedModel

class Qualification(me.EmbeddedDocument):
  qualification = me.StringField()
  qualificationTitle = me.StringField()
  qualificationOrganization = me.StringField()
  date = me.DateField()
  file = me.ReferenceField(FileUpload)  # store file name or path

class Employee(TimeStampedModel):
  meta = {
    "collection": "employees", 
    "db_alias": "resources",
    "indexes": [
      {"fields": ["firstname", "lastname", "identity"], "unique": True}
    ],
  }

  organization = me.StringField(required=True)
  organizationCode = me.StringField(required=True)
  code = me.StringField(required=True)
  firstname = me.StringField()
  lastname = me.StringField(required=True)
  fathername = me.StringField(required=True)
  mothername = me.StringField(required=True)
  identity = me.StringField(required=True)
  birthday = me.DateField()
  sex = me.StringField(choices=['Male', 'Female'])
  dateAppointment = me.DateField()
  workStatus = me.StringField()
  workCategory = me.StringField()
  workSector = me.StringField()
  organizationalUnit = me.StringField()
  building = me.StringField()
  office = me.StringField()
  phoneWork = me.StringField()
  emailWork = me.EmailField()
  finalized = me.BooleanField(default=False)
  qualifications = me.ListField(me.EmbeddedDocumentField(Qualification))