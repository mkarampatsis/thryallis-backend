import json
import os
from bson import ObjectId,json_util
from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.blueprints.utils import debug_print, dict2string
from src.models.resources.facility import Facility

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

    facility_dict = facility.to_mongo().to_dict()
        
    return Response(
      json.dumps(facility_dict),
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
    facility = Facility.objects.get(organizationCode=code)

    facility_dict = facility.to_mongo().to_dict()
        
    return Response(
      json.dumps(facility_dict),
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

    print (">>>",data["finalized"])

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
      # finalized = data["finalized"],
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