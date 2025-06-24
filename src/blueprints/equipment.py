import json
import os
from bson import ObjectId,json_util
from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.blueprints.utils import debug_print, dict2string
from src.models.resources.equipment_config import EquipmentConfig
from src.models.resources.equipment import Equipment

from src.models.psped.change import Change
from src.models.upload import FileUpload 

equipment = Blueprint("equipment", __name__)

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

@equipment.route("", methods=["POST"])
@jwt_required()
def create_equipment():

  try:
    data = request.get_json()
    debug_print("POST EQUIPMENT", data)
    
    spaceObjectIDs = [ObjectId(id_str) for id_str in data['spaceId']]
    
    newEquipment = Equipment(
      organization = data['organization'],
      organizationCode = data['organizationCode'],
      spaceId = spaceObjectIDs,
      type = data['type'],
      kind = data['kind'],
      category = data['category'],
      values = data['values'],
    ).save()

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