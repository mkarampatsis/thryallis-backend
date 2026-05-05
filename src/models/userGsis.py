from src.config import MONGO_PSPED_DB
import mongoengine as me


class UserRoleGSIS(me.EmbeddedDocument):
  role = me.StringField(required=True, choices=[
    'EDITOR', 
    'HELPDESK', 
    'ADMIN', 
    'FACILITY_EDITOR', 
    'FACILITY_ADMIN', 
    'EQUIPMENT_EDITOR', 
    'EQUIPMENT_ADMIN', 
    'OTA_EDITOR', 
    'OTA_ADMIN', 
    'USER_RESOURCES_EDITOR', 
    'USER_RESOURCES_ADMIN',
    "READER",
    "ROOT", 
  ], default="READER")
  active = me.BooleanField(required=True, default=True)
  foreas = me.ListField(me.StringField(), default=[])
  monades = me.ListField(me.StringField(), default=[])

class UserGsis(me.Document):
  email = me.EmailField()
  firstName = me.StringField(required=True)
  lastName = me.StringField(required=True)
  name = me.StringField(required=True)
  fatherName = me.StringField()
  motherName = me.StringField()
  taxid = me.StringField(required=True, unique=True)
  gsisUserid = me.StringField(required=True)
  empOrgUnitTexts = me.ListField(me.StringField(), default=[])
  employeeId = me.IntField(required=True)
  roles = me.EmbeddedDocumentListField(UserRoleGSIS, default=[UserRoleGSIS(role="READER")])
  
  meta = {
    "collection": "users_gsis", 
    "db_alias": MONGO_PSPED_DB,
    "indexes": [
      {"fields": ["taxid"], "unique": True}
    ],
  }

  def to_mongo_dict(self):
    mongo_dict = self.to_mongo().to_dict()
    mongo_dict.pop("_id")
    return mongo_dict

  @staticmethod
  def get_user_by_taxid(taxid: str) -> "UserGsis":
    return UserGsis.objects(taxid=taxid).first()

  @staticmethod
  def get_user_by_email(email: str) -> "UserGsis":
    return UserGsis.objects(email=email).first()
