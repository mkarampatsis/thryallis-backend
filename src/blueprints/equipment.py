import json
import os
from bson import ObjectId,json_util
from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.blueprints.utils import debug_print, dict2string
from datetime import datetime

from src.models.resources.equipment_config import EquipmentConfig
from src.models.resources.equipment import Equipment
from src.models.psped.change import Change
from src.models.upload import FileUpload 
from mongoengine.base import BaseDocument

equipment = Blueprint("equipment", __name__)

# Equipment Config
@equipment.route("/config", methods=["GET"])
def get_equipment_config():
  try:
    equipment_config = EquipmentConfig.objects()

    return Response(
      equipment_config.to_json(),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης config εξοπλισμού:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@equipment.route('/config', methods=['POST'])
@jwt_required()
def create_equipment_config():
  data = request.get_json()
  debug_print("CREATE EQUIPMENT CONFIG", data)

  try:
    for d in data:
      if d['resourceSubcategory'] and len(d["kind"])>0:
        print(d)
                
        newConfig = EquipmentConfig(
          resourceSubcategory = d["resourceSubcategory"],
          kind = d["kind"]
        ).save()

        who = get_jwt_identity()
        what = {"entity": "equipment", "key": {"equipment_config": newConfig}}
        
        Change(action="create", who=who, what=what, change={"equipment_config":newConfig}).save()
    
    return Response(
      json.dumps({"message": "Ο νέος εξοπλισμός καταχωρήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εξοπλισμού:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@equipment.route('/config', methods=['PUT'])
@jwt_required()
def update_equipment_config():
  data = request.get_json()
  debug_print("UPDATE EQUIPMENT CONFIG", data)
  
  try:
    for d in data:
      equipmentConfig = EquipmentConfig.objects.get(id=ObjectId(d["_id"]))
   
      if d["kind"] !=  mongo_to_dict(equipmentConfig.kind):
        # print(">>>", d)
        
        equipmentConfig.update(
          resourceSubcategory = d["resourceSubcategory"],
          kind = d["kind"]
        )
      
        who = get_jwt_identity()
        what = {"entity": "equipment", "key": {"equipment_config": d}}
          
        Change(action="update", who=who, what=what, change={"old":equipmentConfig, "new":d}).save()
        
    return Response(
      json.dumps({"message": "Ο εξοπλισμός τροποποιήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία τροποποίησης εξοπλισμού:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )
    
# #####################

@equipment.route("/organization/<string:code>", methods=["GET"])
def get_equipments_by_organization_code(code):
  try:

    pipeline = [
      {
        "$match": {
          "organizationCode":code
        }
      },
      {
        "$lookup": {
          "from": "space",
          "localField": "spaceWithinFacility",
          "foreignField": "_id", 
          "as": "spaces"
        }
      }
    ]
    equipments = Equipment.objects.aggregate(pipeline)
    equipment_list = list(equipments)

    return Response(
      json_util.dumps({"data": equipment_list}),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης config εξοπλισμού:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@equipment.route("", methods=["POST"])
@jwt_required()
def create_equipment():

  try:
    data = request.get_json()
    debug_print("POST EQUIPMENT", data)
    
    for item in data:
      facilityObjectID = ObjectId(item['hostingFacility'])
      spaceObjectID = ObjectId(item['spaceWithinFacility'])
      acquisitionDate = datetime.strptime(item['acquisitionDate'], "%Y-%m-%d")
            
      equipmentDoc = {
        'organization': item['organization'],
        'organizationCode': item['organizationCode'],
        'hostingFacility': facilityObjectID,
        'spaceWithinFacility': spaceObjectID,
        'resourceCategory': item['resourceCategory'],
        'resourceSubcategory': item['resourceSubcategory'],
        'kind': item['kind'],
        'type': item['type'],
        'itemDescription': item['itemDescription'],
        'itemQuantity': [{
          'distinctiveNameOfFacility': item["itemQuantity"][0]['distinctiveNameOfFacility'],
          'facilityId': ObjectId(item["itemQuantity"][0]['facilityId']),
          'spaceName': item["itemQuantity"][0]['spaceName'],
          'spaceId': ObjectId(item["itemQuantity"][0]['spaceId']),
          'quantity':item["itemQuantity"][0]['quantity'],
          'codes': item["itemQuantity"][0]["codes"],
        }],
        'acquisitionDate': acquisitionDate,
        'status': item['status'],
      }
      newEquipment = Equipment(**equipmentDoc).save()

    who = get_jwt_identity()
    what = {"entity": "equipment", "key": {"newEquipment": True}}
    
    Change(action="create", who=who, what=what, change={"equipment":data}).save()

    return Response(
      json.dumps({"message": "Ο εξοπλισμός καταχωρήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
      )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία καταχώρησης εξοπλισμου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@equipment.route("/<string:id>", methods=["DELETE"])
@jwt_required()
def delete_equipment_by_id(id):
  try: 
    equipment = Equipment.objects(id=ObjectId(id))
    equipment.delete()
  
  except DoesNotExist:
    return Response(json.dumps({"message": "Ο εξοπλισμός δεν υπάρχει"}), mimetype="application/json", status=404)
  except Exception as e:
    return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)
  
  who = get_jwt_identity()
  what = {"entity": "equipment", "key": {"Equipment": id}}

  Change(action="delete", who=who, what=what, change={"equipment":equipment.to_json()}).save()
  return Response(json.dumps({"message": "<strong>Ο εξοπλισμός διαγράφηκε</strong>"}), mimetype="application/json", status=201)

@equipment.route("", methods=["PUT"])
@jwt_required()
def update_equipment():

  try:
    data = request.get_json()
    debug_print("UPDATE EQUIPMENT", data)
    
    id = data["_id"]
    equipment = Equipment.objects.get(id=ObjectId(id))

    hostingFacility = ObjectId(data['hostingFacility'])
    spaceWithinFacility = ObjectId(data['spaceWithinFacility'])
    acquisitionDate = datetime.strptime(data['acquisitionDate'], "%Y-%m-%d")
    
    itemQuantities = []
    for item in data['itemQuantity']:
      itemQuantity = item
      itemQuantity['facilityId'] = ObjectId(item['facilityId'])
      itemQuantity['spaceId'] = ObjectId(item['spaceId'])
      itemQuantities.append(itemQuantity)
    
    equipment.update(
      organization = data['organization'],
      organizationCode = data['organizationCode'],
      hostingFacility = hostingFacility,
      spaceWithinFacility = spaceWithinFacility,
      resourceCategory = data['resourceCategory'],
      resourceSubcategory = data['resourceSubcategory'],
      kind = data['kind'],
      type = data['type'],
      itemDescription = data['itemDescription'],
      itemQuantity = itemQuantities,
      acquisitionDate = acquisitionDate,
      status = data['status'],
      elasticSync = False
    ) 
    
    who = get_jwt_identity()
    what = {"entity": "equipment", "key": {"Equipment": id}}
    
    Change(action="update", who=who, what=what, change={"old":equipment, "new":data}).save()

    return Response(
      json.dumps({"message": "Ο εξοπλισμός τροποποιήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία καταχώρησης εξοπλισμου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@equipment.route("/<string:id>/details", methods=["GET"])
def get_equipment_details_by_id(id):
  try:
    
    if not id:
      return Response(
        json.dumps({"message": "Δεν έχετε δώσει id εξοπλισμού"}),
        mimetype="application/json",
        status=400,
      )

    equipment = Equipment.objects.get(id=ObjectId(id))
    
    return Response(
      equipment.to_json(),
      mimetype="application/json",
      status=200,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης στοιχείων εξοπλισμού:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

def mongo_to_dict(obj):
  """Convert MongoEngine Document or EmbeddedDocument to plain dict."""
  if isinstance(obj, list):
    return [mongo_to_dict(o) for o in obj]
  elif isinstance(obj, BaseDocument):
    return {k: mongo_to_dict(v) for k, v in obj._data.items()}
  else:
    return obj