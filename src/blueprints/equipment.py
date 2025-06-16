import json
import os
from bson import ObjectId,json_util
from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.blueprints.utils import debug_print, dict2string
from src.models.resources.equipment_config import EquipmentConfig

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