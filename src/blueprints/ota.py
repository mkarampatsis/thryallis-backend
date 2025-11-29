from bson import ObjectId
from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from mongoengine import DoesNotExist

from src.models.psped.legal_act import LegalAct
from src.models.ota.ota import Ota
from src.models.psped.legal_provision import LegalProvision, RegulatedObject
from src.models.psped.change import Change
from src.blueprints.decorators import can_edit
import json

from .utils import debug_print

ota = Blueprint("ota", __name__)

@ota.route("", methods=["GET"])
def retrieve_all_ota():
  otaData = Ota.objects().select_related()

  result = [ota.to_dict() for ota in otaData]

  return Response(
    json.dumps(result, default=str),
    mimetype="application/json",
    status=200
  )

@ota.route("/by_id/<string:id>", methods=["GET"])
def retrieve_ota_by_id(id):
  otaData = Ota.objects.get(id=ObjectId(id))
  
  return Response(
     json.dumps({
      otaData
    }, default=str),
    mimetype="application/json",
    status=200,
  )

@ota.route("", methods=["POST"])
@jwt_required()
def create_ota():
  curr_change = {}
  
  try:
    data = request.get_json()
    debug_print("POST OTA", data)

    remitText = data["remitText"]
    remitCompetence = data["remitCompetence"]
    remitType = data["remitType"]
    remitLocalOrGlobal = data["remitLocalOrGlobal"]
    legalProvisions = data["legalProvisions"]
    instructionProvisions = data["instructionProvisions"]
    publicPolicyAgency = data["publicPolicyAgency"]
    status = data.get("status", "ΕΝΕΡΓΗ")
    finalized = data.get("finalized", False)

    newRemit = Ota(
      remitText=remitText,
      remitCompetence=remitCompetence,
      remitType=remitType,
      remitLocalOrGlobal=remitLocalOrGlobal,
      publicPolicyAgency=publicPolicyAgency,
      status=status,
      finalized=finalized,
    ).save()

    newRemitID = newRemit.id
    regulatedObject = RegulatedObject(
      regulatedObjectType="ota",
      regulatedObjectId=newRemitID,
    )

    legal_provisions_changes_inserts = []
    legal_provisions_docs = LegalProvision.save_new_legal_provisions(legalProvisions, regulatedObject)
    legal_provisions_changes_inserts = [provision.to_mongo() for provision in legal_provisions_docs]

    curr_change["legalProvisions"] = {
      "inserts": legal_provisions_changes_inserts,
    }

    instruction_provisions_changes_inserts = []
    instruction_provisions_docs = LegalProvision.save_new_legal_provisions(instructionProvisions, regulatedObject)
    instruction_provisions_changes_inserts = [provision.to_mongo() for provision in instruction_provisions_docs]

    curr_change["instructionProvisions"] = {
      "inserts": instruction_provisions_changes_inserts,
    }

    who = get_jwt_identity()
    what = {"entity": "ota", "key": {"organization": publicPolicyAgency["organization"], "organizationCode": publicPolicyAgency["organizationCode"]}}
    Change(action="create", who=who, what=what, change=curr_change).save()

    newRemit.legalProvisionRefs = legal_provisions_docs
    newRemit.instructionProvisionRefs = instruction_provisions_docs
    newRemit.save()

    return Response(
      json.dumps({"message": "Η αρμοδιότητα του ΟΤΑ δημιουργήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία δημιουργίας αρμοδιότητας ΟΤΑ:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )


@ota.route("", methods=["PUT"])
@jwt_required()
def update_ota():
  curr_change = {}
  try:
      data = request.get_json()
      debug_print("UPDATE REMIT", data)

      remitID = ObjectId(data["_id"])
      organizationalUnitCode = data["organizationalUnitCode"]
      remitText = data["remitText"]
      remitType = data["remitType"]
      cofog = data["cofog"]
      legalProvisions = data["legalProvisions"]
      regulatedObject = RegulatedObject(
        regulatedObjectType="remit",
        regulatedObjectId=remitID,
      )
      legalProvisionDocs = LegalProvision.save_new_legal_provisions(legalProvisions, regulatedObject)

      remit = Ota.objects.get(id=remitID)
      existingLegalProvisions = remit.legalProvisionRefs
      updatedLegalProvisions = existingLegalProvisions + legalProvisionDocs

      remit.update(
          organizationalUnitCode=organizationalUnitCode,
          remitText=remitText,
          remitType=remitType,
          cofog=cofog,
          legalProvisionRefs=updatedLegalProvisions,
      )

      curr_change = {
          "old": {
              "organizationalUnitCode": remit.organizationalUnitCode,
              "remitText": remit.remitText,
              "remitType": remit.remitType,
              "cofog": remit.cofog.to_mongo().to_dict(),
              "legalProvisions": [provision.to_mongo().to_dict() for provision in existingLegalProvisions],
          },
          "new": {
              "organizationalUnitCode": organizationalUnitCode,
              "remitText": remitText,
              "remitType": remitType,
              "cofog": cofog,
              "legalProvisions": [provision.to_mongo().to_dict() for provision in updatedLegalProvisions],
          },
      }
      who = get_jwt_identity()
      what = {"entity": "remit", "key": {"organizationalUnitCode": organizationalUnitCode}}
      Change(action="update", who=who, what=what, change=curr_change).save()

      return Response(
          json.dumps({"message": "Η αρμοδιότητα ενημερώθηκε με επιτυχία"}),
          mimetype="application/json",
          status=201,
      )

  except Exception as e:
      print("UPDATE REMIT EXCEPTION", e)
      return Response(
          json.dumps({"message": f"<strong>Αποτυχία ενημέρωσης αρμοδιότητας:</strong> {e}"}),
          mimetype="application/json",
          status=500,
      )


@ota.route("/status/<string:remitID>", methods=["PUT"])
@jwt_required()
def update_ota_status(remitID: str):
    try:
        data = request.get_json()
        debug_print("UPDATE REMIT STATUS", data)

        status = data["status"]
        remit = Ota.objects.get(id=ObjectId(remitID))
        remit.update(status=status)

        who = get_jwt_identity()
        what = {"entity": "remit", "key": {"remitID": remitID}}
        Change(action="update", who=who, what=what, change={"status": status}).save()

        return Response(
            json.dumps({"message": f"Η αρμοδιότητα είναι πλέον {status}"}),
            mimetype="application/json",
            status=201,
        )

    except Exception as e:
        print("UPDATE REMIT STATUS EXCEPTION", e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία ενημέρωσης κατάστασης αρμοδιότητας:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )

@ota.route("/copy/<string:id>", methods=["GET"])
@jwt_required()
def copy_ota(id):
    curr_change = {}
    newLegalProvisions = []
    try:
        remit = Ota.objects(id=ObjectId(id)).first()
        debug_print("COPY REMIT BY ID", remit.to_json())

        organizationalUnitCode = remit.organizationalUnitCode
        remitText = remit.remitText
        remitType = remit.remitType
        cofog = remit.cofog
        legalProvisions = remit.legalProvisionRefs
        
        newRemit = Ota(
            organizationalUnitCode=organizationalUnitCode,
            remitText=remitText,
            remitType=remitType,
            cofog=cofog,
        ).save()
        newRemitID = newRemit.id
        regulatedObject = RegulatedObject(
            regulatedObjectType="remit",
            regulatedObjectId=newRemitID,
        )
        for legalProvision in legalProvisions:

            newLegalProvisions.append({
                "legalActKey": legalProvision.legalAct.legalActKey,
                "legalProvisionSpecs" : legalProvision.legalProvisionSpecs,
                "legalProvisionText" : legalProvision.legalProvisionText,
                'isNew': True
            })
        legal_provisions_changes_inserts = []

        legal_provisions_docs = LegalProvision.save_new_legal_provisions(newLegalProvisions, regulatedObject)
        legal_provisions_changes_inserts = [provision.to_mongo() for provision in legal_provisions_docs]
        newRemit.legalProvisionRefs = legal_provisions_docs
        newRemit.save()
        
        data = {
            "_id": str(newRemit.id),
            "organizationalUnitCode": newRemit.organizationalUnitCode,
            "remitText": newRemit.remitText,
            "remitType": newRemit.remitType,
            "cofog": newRemit.cofog.to_mongo().to_dict(),
            "status": newRemit.status,
            "legalProvisions": []
        }
        
        for provision in legal_provisions_docs:
            legalActKey = LegalAct.objects(id=ObjectId(str(provision.legalAct.id))).only('legalActKey').exclude('id').first()
            data["legalProvisions"].append(
                    {
                        "_id": str(provision.id),
                        "legalActKey": legalActKey.legalActKey,
                        "legalProvisionSpecs": provision["legalProvisionSpecs"].to_mongo().to_dict(),
                        "legalProvisionText": provision["legalProvisionText"]
                    }
                )
        
        curr_change["legalProvisions"] = {
            "inserts": legal_provisions_changes_inserts,
        }
        
        who = get_jwt_identity()
        what = {"entity": "remit", "key": {"organizationalUnitCode": organizationalUnitCode}}
        Change(action="create", who=who, what=what, change=curr_change).save()
        
        return Response(
            # json.dumps({"message": "Η αρμοδιότητα αντιγράφηκε με επιτυχία", "remit":newRemit.to_dict()}),
            json.dumps({"message": "Η αρμοδιότητα αντιγράφηκε με επιτυχία", "remit":data}),
            mimetype="application/json",
            status=201,
        )

    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία δημιουργίας αρμοδιότητας:</strong> {e}"}),
            mimetype="application/json",
            status=500,
    )

@ota.route("/<string:id>", methods=["DELETE"])
@jwt_required()
def delete_ota_by_code(id):
    
    try: 
        remit_to_delete = Ota.objects(id=ObjectId(id))
        
        # Delete referenced legal provisions
        for remit in remit_to_delete:
            for item in remit.legalProvisionRefs:
                legal_provision = LegalProvision.objects(id=item["id"]).first()
                if legal_provision:
                    # print (legal_provision.to_json())
                    legal_provision.delete()
        # Delete the main document
        remit_to_delete.delete()
    
    except DoesNotExist:
        return Response(json.dumps({"message": "Η διάταξη δεν υπάρχει"}), mimetype="application/json", status=404)
    except Exception as e:
        return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)
    
    who = get_jwt_identity()
    what = {"entity": "remit", "key": {"RemitID": id}}
    # print(remit_to_delete.to_json())
    Change(action="delete", who=who, what=what, change={"remit":remit_to_delete.to_json()}).save()
    return Response(json.dumps({"message": "<strong>H Αρμοδιότητα διαγράφηκε</strong>"}), mimetype="application/json", status=201)