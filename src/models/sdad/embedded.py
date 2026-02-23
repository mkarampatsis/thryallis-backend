import mongoengine as me

class CountryDoc(me.EmbeddedDocument):
  id = me.IntField()
  description = me.StringField()

class CityDoc(me.EmbeddedDocument):
  id = me.IntField()
  description = me.StringField()
  parentId = me.IntField(null=True)

class OrganizationDoc(me.EmbeddedDocument):
  id = me.IntField()
  description = me.StringField()

class SubOrganizationDoc(me.EmbeddedDocument):
  code = me.StringField()
  preferredLabel = me.StringField()  
  
class FekDoc(me.EmbeddedDocument):
  year = me.IntField(null=True)
  number = me.IntField(null=True)
  issue = me.StringField(null=True)

class ContactDoc(me.EmbeddedDocument):
  email = me.StringField(null=True)
  telephone = me.StringField(null=True)
 
class MainAddressDoc(me.EmbeddedDocument):
  fullAddress = me.StringField()
  postCode = me.StringField()
  country = me.EmbeddedDocumentField(CountryDoc, null=True)  
  city = me.EmbeddedDocumentField(CityDoc, null=True)

class SecondaryAddressesDoc(me.EmbeddedDocument):
  fullAddress = me.StringField()
  postCode = me.StringField()
  country = me.EmbeddedDocumentField(CountryDoc, null=True)  
  city = me.EmbeddedDocumentField(CityDoc, null=True)  

class PurposeDoc(me.EmbeddedDocument):
  id = me.IntField()
  description = me.StringField()

class UnitTypeDoc(me.EmbeddedDocument):
  id = me.IntField()
  description = me.StringField()

class supervisorUnitCodeDoc(me.EmbeddedDocument):
  code = me.StringField()
  preferredLabel = me.StringField()

class organizationCodeDoc(me.EmbeddedDocument):
  code = me.StringField()
  preferredLabel = me.StringField()
  
class SpatialDoc(me.EmbeddedDocument):
  country = me.EmbeddedDocumentField(CountryDoc, null=True)
  city = me.EmbeddedDocumentField(CityDoc, null=True)