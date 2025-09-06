import json
import os
from bson import ObjectId,json_util
from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.blueprints.utils import debug_print, dict2string
from src.models.resources.facility import Facility
from src.models.resources.equipment import Equipment
from src.models.resources.space import Space
from src.models.psped.change import Change
from src.models.resources.facility_config import FacilityConfig
from src.models.upload import FileUpload 
from mongoengine.base import BaseDocument

facility = Blueprint("facility", __name__)

# Facility Config
@facility.route("/config", methods=["GET"])
def get_facility_config():
  try:
    facility_config = FacilityConfig.objects()

    return Response(
      facility_config.to_json(),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης config ακινήτων:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route('/config', methods=['POST'])
@jwt_required()
def create_facility_config():
  data = request.get_json()
  debug_print("CREATE FACILITY CONFIG", data)

  try:
    for d in data:
      if d['type'] and len(d["spaces"])>0:
        print(d)
        serialized_spaces = []
        for space in d["spaces"]:
          serialized_space = {
            "type": space["type"],
            "spaces": [item["value"] for item in space["spaces"]]
          }
          serialized_spaces.append(serialized_space)
        
        newFacilityConfig = FacilityConfig(
          type = d["type"],
          spaces = serialized_spaces
        ).save()

        who = get_jwt_identity()
        what = {"entity": "facility", "key": {"facility_config": newFacilityConfig}}
        
        Change(action="create", who=who, what=what, change={"facility_config":newFacilityConfig}).save()
    
    return Response(
      json.dumps({"message": "Ο νέος χωρος ακινήτου καταχωρήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία καταχώρησης χώρου ακίνητου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route('/config', methods=['PUT'])
@jwt_required()
def update_facility_config():
  data = request.get_json()
  debug_print("UPDATE FACILITY CONFIG", data)
  
  try:
    for d in data:
      doc = clean_facility_data(d)
      doc = flatten_spaces(doc)

      facilityConfig = FacilityConfig.objects.get(id=ObjectId(doc["_id"]))
      
      if doc["spaces"] !=  mongo_to_dict(facilityConfig.spaces):
        
        facilityConfig.update(
          type = doc["type"],
          spaces = doc["spaces"],
        )
      
        who = get_jwt_identity()
        what = {"entity": "facility", "key": {"facility_config": doc}}
          
        Change(action="update", who=who, what=what, change={"old":facilityConfig, "new":doc}).save()
        
    return Response(
      json.dumps({"message": "Ο χωρος ακινήτου τροποποιήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία τροποποίησης χώρου ακίνητου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )
    
# #####################

# Facility requests
@facility.route("", methods=["GET"])
def get_all_facilities():
  try:
    facilities = Facility.objects()

    return Response(
      facilities.to_json(),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης Ακινήτων:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/<string:id>", methods=["GET"])
def get_facility_by_id(id):
  try:
    facility = Facility.objects.get(id=ObjectId(id))
        
    return Response(
      facility.to_json(),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης ακινήτου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/organization/<string:code>", methods=["GET"])
def get_facilities_by_organization_code(code):
  try:
    facilities = Facility.objects(organizationCode=code)

    return Response(
      facilities.to_json(),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης ακινήτων του φορέα:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/organizations", methods=["GET"])
def get_facilities_list_by_organization_codes():
  try:
    
    codes = request.args.get("codes")
    
    if not codes:
      return Response(
        json.dumps({"message": "Δεν έχετε δώσει κωδικούς φορέα"}),
        mimetype="application/json",
        status=400,
      )

    codes_list = codes.split(",")  # ["22", "33"]

    facilities = Facility.objects(organizationCode__in=codes_list)

    return Response(
      facilities.to_json(),
      mimetype="application/json",
      status=200,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης ακινήτων του φορέα:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("", methods=["POST"])
@jwt_required()
def create_facility():

  try:
    data = request.get_json()
    debug_print("POST FACILITY", data)

    serialized_floorPlans = []
    for floor in data["floorPlans"]:
      fileObjectIDs = [ObjectId(id_str) for id_str in floor["floorPlan"]]
      serialized_floorPlan = {
        "floorArea": floor["floorArea"],
        "floorPlan": fileObjectIDs,
        "level": floor["level"],
        "num": floor["num"]
      }
      serialized_floorPlans.append(serialized_floorPlan)

    newFacility = Facility(
      organization = data["organization"],
      organizationCode = data["organizationCode"],
      kaek = data["kaek"],
      belongsTo = data["belongsTo"],
      distinctiveNameOfFacility = data["distinctiveNameOfFacility"],
      useOfFacility =data["useOfFacility"],
      uniqueUseOfFacility = data["uniqueUseOfFacility"],
      private = data["private"],
      coveredPremisesArea = data["coveredPremisesArea"],
      floorsOrLevels = data["floorsOrLevels"],
      floorPlans = serialized_floorPlans,
      addressOfFacility = data["addressOfFacility"],
      # finalized = True if data["finalized"]=='true' else False 
      finalized = data["finalized"]
    ).save()

    who = get_jwt_identity()
    what = {"entity": "facility", "key": {"distinctiveNameOfFacility": data["distinctiveNameOfFacility"]}}
    
    Change(action="create", who=who, what=what, change={"facility":data}).save()

    return Response(
      json.dumps({"message": "Το ακίνητο σας καταχωρήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία καταχώρησης ακίνητου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/<string:id>", methods=["PUT"])
@jwt_required()
def update_facility(id):

  try:
    data = request.get_json()
    debug_print("UPDATE FACILITY", data)
    
    facility = Facility.objects.get(id=ObjectId(id))

    serialized_floorPlans = []
    for floor in data["floorPlans"]:
      fileObjectIDs = [ObjectId(id_str) for id_str in floor["floorPlan"]]
      serialized_floorPlan = {
        "floorArea": floor["floorArea"],
        "floorPlan": fileObjectIDs,
        "level": floor["level"],
        "num": floor["num"]
      }
      serialized_floorPlans.append(serialized_floorPlan)

    facility.update(
      organization = data["organization"],
      organizationCode = data["organizationCode"],
      kaek = data["kaek"],
      belongsTo = data["belongsTo"],
      distinctiveNameOfFacility = data["distinctiveNameOfFacility"],
      useOfFacility =data["useOfFacility"],
      uniqueUseOfFacility = data["uniqueUseOfFacility"],
      private = data["private"],
      coveredPremisesArea = data["coveredPremisesArea"],
      floorsOrLevels = data["floorsOrLevels"],
      floorPlans = serialized_floorPlans,
      addressOfFacility = data["addressOfFacility"],
      # finalized = True if data["finalized"]=='true' else False 
      finalized = data["finalized"]
    )

    who = get_jwt_identity()
    what = {"entity": "facility", "key": {"faciltyId": id}}
    
    Change(action="update", who=who, what=what, change={"old":facility, "new":data}).save()

    return Response(
      json.dumps({"message": "Το ακίνητο σας τροποποιήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία τροποποίησης ακίνητου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/<string:id>", methods=["DELETE"])
@jwt_required()
def delete_facility_by_id(id):
  try: 
    facility = Facility.objects.get(id=ObjectId(id))

    # Delete referenced files of facility
    for floorPlan in facility.floorPlans:
      for item in floorPlan.floorPlan:
        file_doc = FileUpload.objects(id=item["id"]).first()
        if file_doc:
          delete_uploaded_file(file_doc)
          file_doc.delete()
    
    # Delete all spaces of facility
    spaces = Space.objects(facilityId=ObjectId(id))
    for space in spaces:
      space.delete()
    
    # Delete the main document
    facility.delete()
  
  except DoesNotExist:
    return Response(json.dumps({"message": "Το ακίνητο δεν υπάρχει"}), mimetype="application/json", status=404)
  except Exception as e:
    return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)
  
  who = get_jwt_identity()
  what = {"entity": "facility", "key": {"Facility": id}}
  
  Change(action="delete", who=who, what=what, change={"facility":facility.to_json()}).save()
  return Response(json.dumps({"message": "<strong>Το ακίνητο διαγράφηκε</strong>"}), mimetype="application/json", status=201)

@facility.route("/file/<string:id>", methods=["DELETE"])
@jwt_required()
def delete_facility_file(id):
  print(id)
  try: 
    file_doc = FileUpload.objects.get(id=ObjectId(id))
    if file_doc:
      delete_uploaded_file(file_doc)
      file_doc.delete()

      facility_file = Facility.objects(floorPlans__floorPlan=ObjectId(id)).update(
          __raw__={
            '$pull': {
              'floorPlans.$[].floorPlan': ObjectId(id)
            }
          }
        )

  except FileUpload.DoesNotExist:
    return Response(json.dumps({"message": "Η πληροφορία δεν υπάρχει"}), mimetype="application/json", status=404)
  except Exception as e:
    return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)
  
  who = get_jwt_identity()
  what = {"entity": "facility", "key": {"file": id}}
  
  Change(action="delete", who=who, what=what, change={"file_uploads":file_doc.to_json()}).save()
  return Response(json_util.dumps({
    "message": "<strong>Το αρχείο διαγράφηκε</strong>"
    }), 
    mimetype="application/json", 
    status=201
  )

#####################
# Space Methods
#####################

@facility.route("/<string:id>", methods=["GET"])
def get_space_by_id(id):
  try:
    space = space.objects.get(id=ObjectId(id))
        
    return Response(
      space.to_json(),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης χώρου ακινήτου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/<string:id>/spaces", methods=["GET"])
def get_spaces_by_facility_id(id):
  try:
    spaces = Space.objects(facilityId=ObjectId(id))

    serialized_spaces = []
    for space in spaces:
      serialized_space = {
        "id": str(space.id),
        "facilityId": {
          "id": str(space.facilityId.id),
          "organization": space.facilityId.organization,
          "organizationCode": space.facilityId.organizationCode,
          "distinctiveNameOfFacility":space.facilityId.distinctiveNameOfFacility
        },
        'organizationalUnit': [{
            "organizationalUnit": ou.organizationalUnit,
            "organizationalUnitCode": ou.organizationalUnitCode
          } for ou in space.organizationalUnit],
        "spaceName": space.spaceName,
        "spaceUse": space.spaceUse.to_mongo() if space.spaceUse else None,
        "auxiliarySpace":space.auxiliarySpace,
        "spaceArea": space.spaceArea,
        "spaceLength": space.spaceLength,
        "spaceWidth": space.spaceWidth,
        "entrances": space.entrances,
        "windows": space.windows,
        "floorPlans": space.floorPlans.to_mongo() if space.floorPlans else None,
        "elasticSync": space.elasticSync,
        "createdAt": space.created_at.isoformat() if hasattr(space, "created_at") else None,
        "updatedAt": space.updated_at.isoformat() if hasattr(space, "updated_at") else None,
      }
      serialized_spaces.append(serialized_space)

    return Response(
      json_util.dumps(serialized_spaces),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης χώρων του ακινήτου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

# Get Space
@facility.route("/organization/<string:code>/spaces", methods=["GET"])
def get_all_spaces_by_organization_code(code):
  try:
    pipeline = [
      {
        "$match": {
          "organizationCode": code
        }
      },
      {
        "$lookup": {
          "from": "space",
          "localField": "_id",
          "foreignField": "facilityId",
          "as": "spaces"
        }
      },
      { "$unwind": "$spaces" },
      {
        "$project": {
          "createdAt": 0,
          "updatedAt": 0,
          "kaek": 0,
          "belongsTo": 0,
          "uniqueUseOfFacility": 0,
          "coveredPremisesArea": 0,
          "floorPlans": 0,
          "floorsOrLevels": 0,
          "addressOfFacility": 0,
          "finalized": 0,
          "elasticSync": 0,
        }
      }
    ]

    spaces = Facility.objects.aggregate(pipeline)
    spaces_list = list(spaces)

    return Response(
      json_util.dumps({"data": spaces_list}),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης χώρων ακινήτου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/<string:id>/space", methods=["POST"])
@jwt_required()
def create_space(id):

  try:
    data = request.get_json()
    debug_print("POST SPACE", data)

    newSpace = Space(
      facilityId = ObjectId(data["facilityId"]),
      organizationalUnit = data["organizationalUnit"],
      spaceName = data["spaceName"],
      spaceUse = data["spaceUse"],
      auxiliarySpace = data["auxiliarySpace"],
      spaceArea = data["spaceArea"],
      spaceLength = data["spaceLength"],
      spaceWidth = data["spaceWidth"],
      entrances = str(data["entrances"]),
      windows = str(data["windows"]),
      floorPlans = data["floorPlans"]
    ).save()

    who = get_jwt_identity()
    what = {"entity": "space", "key": {"spaceName": data["spaceName"]}  }
    
    Change(action="create", who=who, what=what, change={"space":data}).save()

    return Response(
      json.dumps({"message": "Ο χώρος καταχωρήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία καταχώρησης χώρου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/<string:id>/space", methods=["PUT"])
@jwt_required()
def update_space(id):

  try:
    data = request.get_json()
    debug_print("UPDATE SPACE", data)

    id = data["id"]
    space = Space.objects.get(id=ObjectId(id))

    space.update(
      facilityId = ObjectId(data["facilityId"]),
      organizationalUnit = data["organizationalUnit"],
      spaceName = data["spaceName"],
      spaceUse = data["spaceUse"],
      auxiliarySpace = data["auxiliarySpace"],
      spaceArea = data["spaceArea"],
      spaceLength = data["spaceLength"],
      spaceWidth = data["spaceWidth"],
      entrances = str(data["entrances"]),
      windows = str(data["windows"]),
      floorPlans = data["floorPlans"],
      elasticSync = False
    )

    who = get_jwt_identity()
    what = {"entity": "space", "key": {"Space": id}}
    
    Change(action="update", who=who, what=what, change={"old":space, "new":data}).save()

    return Response(
      json.dumps({"message": "Ο χώρος τροποποιήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία τροποποίησης χώρου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/space/<string:id>", methods=["DELETE"])
@jwt_required()
def delete_space_by_id(id):
  try: 
    space = Space.objects(id=ObjectId(id))
    space.delete()
  
  except DoesNotExist:
    return Response(json.dumps({"message": "Ο χώρος δεν υπάρχει"}), mimetype="application/json", status=404)
  except Exception as e:
    return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)
  
  who = get_jwt_identity()
  what = {"entity": "space", "key": {"Space": id}}

  Change(action="delete", who=who, what=what, change={"space":space.to_json()}).save()
  return Response(json.dumps({"message": "<strong>Ο χώρος διαγράφηκε</strong>"}), mimetype="application/json", status=201)

###################
# Report Requests
###################

@facility.route("/report1", methods=["GET"])
def get_report1():
  try:
    
    codes = request.args.get("codes")
    
    if not codes:
      return Response(
        json.dumps({"message": "Δεν έχετε δώσει κωδικούς φορέα"}),
        mimetype="application/json",
        status=400,
      )

    codes_list = codes.split(",")  # ["22", "33"]

    facilities = Facility.objects(organizationCode__in=codes_list)
    equipments = Equipment.objects(organizationCode__in=codes_list)

    facilities_with_spaces = []
    for facility in facilities:
      facility_dict = json.loads(facility.to_json())  # Convert MongoEngine object to dict
      # Query spaces for this facility
      spaces = Space.objects(facilityId=facility.id)
      facility_dict["spaces"] = json.loads(spaces.to_json())
      facilities_with_spaces.append(facility_dict)


    result = {
      "facilities": facilities_with_spaces,
      "equipments": json.loads(equipments.to_json())
    }

    return Response(
      json.dumps(result, ensure_ascii=False),
      mimetype="application/json",
      status=200,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης ακινήτων του φορέα:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/organizations/details", methods=["GET"])
def get_facility_details_by_organizations():
  try:
    
    codes = request.args.get("codes")
    
    if not codes:
      return Response(
        json.dumps({"message": "Δεν έχετε δώσει κωδικούς φορέα"}),
        mimetype="application/json",
        status=400,
      )

    codes_list = codes.split(",")  # ["22", "33"]

    facilities = Facility.objects(organizationCode__in=codes_list)
    
    facilities_with_spaces = []
    for facility in facilities:
      facility_dict = json.loads(facility.to_json())  # Convert MongoEngine object to dict
      # Query spaces for this facility
      spaces = Space.objects(facilityId=facility.id)
         
      # Query equipments for this space
      spaces_with_equipments = []
      for space in spaces:
        space_dict = json.loads(space.to_json())  # Convert MongoEngine object to dict
        # Query equipments for this space
        equipments = Equipment.objects(spaceWithinFacility=space.id)
        space_dict["equipments"] = json.loads(equipments.to_json())
        spaces_with_equipments.append(space_dict)
      
      facility_dict["spaces"] = spaces_with_equipments

      facilities_with_spaces.append(facility_dict)
    
    return Response(
      json.dumps(facilities_with_spaces, ensure_ascii=False),
      mimetype="application/json",
      status=200,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης ακινήτων του φορέα:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/organizationalUnits/details", methods=["GET"])
def get_facility_details_by_organizationalUnits():
  try:
    
    codes = request.args.get("codes")
    
    if not codes:
      return Response(
        json.dumps({"message": "Δεν έχετε δώσει κωδικούς μονάδας"}),
        mimetype="application/json",
        status=400,
      )

    codes_list = codes.split(",")  # ["22", "33"]
    
    spaces = Space.objects(organizationalUnit__organizationalUnitCode__in=codes_list)
    
    fileObjectIDs = list(dict.fromkeys([str(space.facilityId.id) for space in spaces if space.facilityId]))
    facilities = Facility.objects(id__in=fileObjectIDs)

    facilities_with_spaces = []
    for facility in facilities:
      facility_dict = json.loads(facility.to_json())  # Convert MongoEngine object to dict
      # Query spaces for this facility
      spaces = Space.objects(facilityId=facility.id)
         
      # Query equipments for this space
      spaces_with_equipments = []
      for space in spaces:
        space_dict = json.loads(space.to_json())  # Convert MongoEngine object to dict
        # Query equipments for this space
        equipments = Equipment.objects(spaceWithinFacility=space.id)
        space_dict["equipments"] = json.loads(equipments.to_json())
        spaces_with_equipments.append(space_dict)
      
      facility_dict["spaces"] = spaces_with_equipments

      facilities_with_spaces.append(facility_dict)
    
    return Response(
      json.dumps(facilities_with_spaces, ensure_ascii=False),
      mimetype="application/json",
      status=200,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης ακινήτων της μονάδας:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/facilities/details", methods=["GET"])
def get_facility_details_by_ids():
  try:
    
    codes = request.args.get("codes")
    
    if not codes:
      return Response(
        json.dumps({"message": "Δεν έχετε δώσει κωδικούς ακινήτου"}),
        mimetype="application/json",
        status=400,
      )

    codes_list = codes.split(",")  # ["22", "33"]
    print(codes_list)
    
    facilities = Facility.objects(id__in=codes_list)

    facilities_with_spaces = []
    for facility in facilities:
      facility_dict = json.loads(facility.to_json())  # Convert MongoEngine object to dict
      # Query spaces for this facility
      spaces = Space.objects(facilityId=facility.id)
         
      # Query equipments for this space
      spaces_with_equipments = []
      for space in spaces:
        space_dict = json.loads(space.to_json())  # Convert MongoEngine object to dict
        # Query equipments for this space
        equipments = Equipment.objects(spaceWithinFacility=space.id)
        space_dict["equipments"] = json.loads(equipments.to_json())
        spaces_with_equipments.append(space_dict)
      
      facility_dict["spaces"] = spaces_with_equipments

      facilities_with_spaces.append(facility_dict)
    
    return Response(
      json.dumps(facilities_with_spaces, ensure_ascii=False),
      mimetype="application/json",
      status=200,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης ακινήτων:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@facility.route("/<string:id>/details", methods=["GET"])
def get_facility_details_by_id(id):
  try:
    
    if not id:
      return Response(
        json.dumps({"message": "Δεν έχετε δώσει id ακινήτου"}),
        mimetype="application/json",
        status=400,
      )

    facility = Facility.objects.get(id=ObjectId(id))
    spaces = Space.objects(facilityId=ObjectId(id))

    spaces_with_equipments = []
    for space in spaces:
      space_dict = json.loads(space.to_json())  # Convert MongoEngine object to dict
      # Query equipments for this space
      equipments = Equipment.objects(spaceWithinFacility=space.id)
      space_dict["equipments"] = json.loads(equipments.to_json())
      spaces_with_equipments.append(space_dict)


    result = {
      "facility": json.loads(facility.to_json()),
      "spaces": spaces_with_equipments
    }

    return Response(
      json.dumps(result, ensure_ascii=False),
      mimetype="application/json",
      status=200,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης στοιχείων ακινήτου:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

# Function that deletes all referenced files
def delete_uploaded_file(file_doc):
  try:
    # Combine path and filename
    file_path = os.path.join(file_doc["file_location"], file_doc["file_id"])

    # Check if file exists
    if os.path.exists(file_path):
      os.remove(file_path)
      print(f"Deleted: {file_path}")
      return True
    else:
      print(f"File not found: {file_path}")
      return False

  except Exception as e:
    print(f"Error deleting file: {e}")
    return False  

def clean_facility_data(obj):
  """
  Recursively:
  - Remove 'readonly' fields
  - Remove empty/invalid space groups
  """
  if isinstance(obj, dict):
    obj.pop('readonly', None)  # Remove readonly if present
    
    # Process children
    for key, value in list(obj.items()):
      obj[key] = clean_facility_data(value)

    # Special handling for 'spaces' in a group
    if 'spaces' in obj and isinstance(obj['spaces'], list):
      obj['spaces'] = [
        clean_facility_data(sg)
        for sg in obj['spaces']
        if not (
          isinstance(sg, dict) and
          isinstance(sg.get('spaces'), list) and
          (
            len(sg['spaces']) == 0 or  # empty list
            all(isinstance(item, dict) and item.get('value', '').strip() == '' for item in sg['spaces'])  # only empty strings
          )
        )
      ]
  elif isinstance(obj, list):
    return [clean_facility_data(item) for item in obj]

  return obj

def flatten_spaces(doc):
  """
  Convert 'spaces': [{'value': '...'}, ...] into
  'spaces': ['...', ...] for all levels in the structure.
  """
  if "spaces" in doc and isinstance(doc["spaces"], list):
    # Check if these are space objects (with "value") or subcategories
    if doc["spaces"] and isinstance(doc["spaces"][0], dict) and "value" in doc["spaces"][0]:
      # Flatten only the values
      doc["spaces"] = [s["value"] for s in doc["spaces"] if s.get("value")]
    else:
      # Recursively process nested space groups
      for sub in doc["spaces"]:
        flatten_spaces(sub)
  return doc


def mongo_to_dict(obj):
  """Convert MongoEngine Document or EmbeddedDocument to plain dict."""
  if isinstance(obj, list):
    return [mongo_to_dict(o) for o in obj]
  elif isinstance(obj, BaseDocument):
    return {k: mongo_to_dict(v) for k, v in obj._data.items()}
  else:
    return obj