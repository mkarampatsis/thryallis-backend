import json
import os
from bson import ObjectId,json_util
from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.blueprints.utils import debug_print, dict2string
from src.models.resources.facility import Facility
from src.models.resources.space import Space

facility = Blueprint("facilty", __name__)

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
      organizationalUnit = data["organizationalUnit"],
      organizationalUnitCode = data["organizationalUnitCode"],
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


# Space Methods

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

@facility.route("/<string:id>/space", methods=["GET"])
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

@facility.route("/<string:id>/space", methods=["POST"])
@jwt_required()
def create_space(id):

  try:
    data = request.get_json()
    debug_print("POST SPACE", data)

    newSpace = Space(
      facilityId = ObjectId(data["facilityId"]),
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