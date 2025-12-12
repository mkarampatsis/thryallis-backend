from flask import Blueprint, request, Response
from flask_jwt_extended import get_jwt_identity, jwt_required
from mongoengine import DoesNotExist
from src.models.psped.foreas import Foreas
from src.models.psped.remit import Remit
from src.models.apografi.organizational_unit import OrganizationalUnit as Monada
from src.models.psped.legal_act import LegalAct
from src.models.psped.legal_provision import LegalProvision, RegulatedObject
from src.models.ota.instruction_provision import InstructionProvision
from src.models.psped.change import Change
from .utils import debug_print
import json
from src.blueprints.decorators import can_update_delete, can_delete_instruction_provision
from bson import ObjectId


instruction_provision = Blueprint("instruction_provision", __name__)


@instruction_provision.route("/<string:instructionProvisionID>", methods=["DELETE"])
@jwt_required()
@can_delete_instruction_provision
def delete_instruction_provision(instructionProvisionID: str):
  instruction_provision = InstructionProvision.objects.get(id=instructionProvisionID)
  regulatedObject = instruction_provision.regulatedObject

  try:
    existing_instruction_provision = InstructionProvision.objects.get(id=instructionProvisionID)
    existing_instruction_provision.delete()
  except DoesNotExist:
    return Response(json.dumps({"message": "Η επιμέρους ενότητα εγκυκλίου δεν υπάρχει"}), mimetype="application/json", status=404)
  except Exception as e:
    return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)

  if regulatedObject.regulatedObjectType == "ota":
    try:
      remit = Remit.objects.get(id=regulatedObject.regulatedObjectId)
      remit.instructionProvisionRefs = [provision for provision in remit.instructionProvisionRefs if str(provision.id) != instructionProvisionID]
      remit.save()
    except DoesNotExist:
      return Response(json.dumps({"message": "Η αρμοδιότητα δεν υπάρχει"}), mimetype="application/json", status=404)
    except Exception as e:
      return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)

  who = get_jwt_identity()
  what = {"entity": "instructionProvision", "key": {"instructionProvisionID": instructionProvisionID}}
  change = existing_instruction_provision.to_mongo().to_dict()
  Change(action="delete", who=who, what=what, change=change).save()
  return Response(json.dumps({"message": "<strong>H διάταξη διαγράφηκε</strong>"}), mimetype="application/json", status=201)


@instruction_provision.route("", methods=["PUT"])
@jwt_required()
@can_update_delete
def update_instruction_provision():
  data = request.get_json()
  debug_print("UPDATE LEGAL PROVISION", data)

  code = data["code"]
  if data["remitID"]:
    code = ObjectId(data["remitID"])
  instructionProvisionType = data["provisionType"]
  currentProvision = data["currentProvision"]
  updatedProvision = data["updatedProvision"]

  regulatedObject = InstructionProvision.regulated_object(code, instructionProvisionType)
  instructionActKey = currentProvision["instructionActKey"]
  instructionAct = LegalAct.objects.get(instructionActKey=instructionActKey)
  instructionProvisionSpecs = currentProvision["instructionProvisionSpecs"]
  existing_instruction_provision = InstructionProvision.objects(
    instructionAct=instructionAct, instructionProvisionSpecs=instructionProvisionSpecs, regulatedObject=regulatedObject
  ).first()

  try:
    updated_instructionActKey = updatedProvision["instructionActKey"]
    updated_instructionAct = LegalAct.objects.get(instructionActKey=updated_instructionActKey)
    updated_instructionProvisionSpecs = updatedProvision["instructionProvisionSpecs"]
    updated_instructionProvisionText = updatedProvision["instructionProvisionText"]
    existing_instruction_provision.update(
      instructionAct=updated_instructionAct,
      instructionProvisionSpecs=updated_instructionProvisionSpecs,
      instructionProvisionText=updated_instructionProvisionText,
    )

    who = get_jwt_identity()
    what = {
      "entity": "instructionProvision",
      "key": {
        "code": code,
        "instructionProvisionType": instructionProvisionType,
        "instructionActKey": instructionActKey,
        "instructionProvisionSpecs": instructionProvisionSpecs,
      },
    }
    change = {
      "old": currentProvision,
      "new": updatedProvision,
    }
    Change(action="update", who=who, what=what, change=change).save()
    return Response(
      json.dumps(
        {
          "message": "<strong>H διάταξη ανανεώθηκε</strong>",
          "updatedLegalProvision": {
            "instructionActKey": updated_instructionActKey,
            "instructionProvisionSpecs": updated_instructionProvisionSpecs,
            "instructionProvisionText": updated_instructionProvisionText,
          },
        }
      ),
      mimetype="application/json",
      status=201,
    )
  except Exception as e:
    print(e)
    return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)


@instruction_provision.route("/count", methods=["GET"])
@jwt_required()
def count_all_instruction_provisions():
  count = InstructionProvision.objects().count()
  return Response(json.dumps({"count": count}), mimetype="application/json", status=200)
