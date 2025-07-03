import json
import os
from bson import ObjectId,json_util
from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.blueprints.utils import debug_print, dict2string
from src.models.resources.facility import Facility
from src.models.resources.space import Space
from src.models.psped.change import Change
from src.models.upload import FileUpload 

facility = Blueprint("facility", __name__)

@facility.route("", methods=["GET"])
def get_all_facilities():
  try:
    facilities = Facility.objects()

    return Response(
      questions.to_json(),
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

@facility.route("", methods=["POST"])
@jwt_required()
def create_facility():

  try:
    data = request.get_json()
    debug_print("POST FACILITY", data)

    newFacility = Facility(
      organization = data["organization"],
      organizationCode = data["organizationCode"],
      kaek = data["kaek"],
      belongsTo = data["belongsTo"],
      distinctiveNameOfFacility = data["distinctiveNameOfFacility"],
      useOfFacility =data["useOfFacility"],
      uniqueUserOfFacility = data["uniqueUseOfFacility"],
      coveredPremisesArea = data["coveredPremisesArea"],
      floorsOrLevels = data["floorsOrLevels"],
      floorPlans = data["floorPlans"],
      addressOfFacility = data["addressOfFacility"],
      finalized = True if data["finalized"]=='true' else False 
    ).save()

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
        },
        "spaceName": space.spaceName,
        "spaceUse": space.spaceUse.to_mongo() if space.spaceUse else None,
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
          "uniqueUserOfFacility": 0,
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
      spaceArea = data["spaceArea"],
      spaceLength = data["spaceLength"],
      spaceWidth = data["spaceWidth"],
      entrances = str(data["entrances"]),
      windows = str(data["windows"]),
      floorPlans = data["floorPlans"]
    ).save()

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
  # print(general_info_to_delete)
  Change(action="delete", who=who, what=what, change={"space":space.to_json()}).save()
  return Response(json.dumps({"message": "<strong>Ο χώρος διαγράφηκε</strong>"}), mimetype="application/json", status=201)


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