from bson import ObjectId
from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from mongoengine import DoesNotExist

from src.models.psped.legal_act import LegalAct
from src.models.psped.remit import Remit
from src.models.psped.legal_provision import LegalProvision, RegulatedObject
from src.models.psped.change import Change
from src.blueprints.decorators import can_edit
import json

from .utils import debug_print

remit = Blueprint("remit", __name__)


@remit.route("", methods=["POST"])
@jwt_required()
def create_remit():
    curr_change = {}
    try:
        data = request.get_json()
        debug_print("POST REMIT", data)

        organizationalUnitCode = data["organizationalUnitCode"]
        remitText = data["remitText"]
        remitType = data["remitType"]
        cofog = data["cofog"]
        legalProvisions = data["legalProvisions"]

        newRemit = Remit(
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

        legal_provisions_changes_inserts = []

        legal_provisions_docs = LegalProvision.save_new_legal_provisions(legalProvisions, regulatedObject)
        legal_provisions_changes_inserts = [provision.to_mongo() for provision in legal_provisions_docs]

        curr_change["legalProvisions"] = {
            "inserts": legal_provisions_changes_inserts,
        }

        who = get_jwt_identity()
        what = {"entity": "remit", "key": {"organizationalUnitCode": organizationalUnitCode}}
        Change(action="create", who=who, what=what, change=curr_change).save()

        newRemit.legalProvisionRefs = legal_provisions_docs
        newRemit.save()

        return Response(
            json.dumps({"message": "Η αρμοδιότητα δημιουργήθηκε με επιτυχία"}),
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


@remit.route("", methods=["PUT"])
@jwt_required()
def update_remit():
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

        remit = Remit.objects.get(id=remitID)
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


@remit.route("/status/<string:remitID>", methods=["PUT"])
@jwt_required()
def update_remit_status(remitID: str):
    try:
        data = request.get_json()
        debug_print("UPDATE REMIT STATUS", data)

        status = data["status"]
        remit = Remit.objects.get(id=ObjectId(remitID))
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


@remit.route("", methods=["GET"])
# @jwt_required()
def retrieve_all_remit():
    remits = Remit.objects()
    return Response(
        remits.to_json(),
        mimetype="application/json",
        status=200,
    )


@remit.route("/count", methods=["GET"])
@jwt_required()
def count_all_remits():
    count = Remit.objects().count()
    return Response(json.dumps({"count": count}), mimetype="application/json", status=201)


@remit.route("/by_code/<string:code>", methods=["GET"])
# @jwt_required()
def retrieve_remit_by_code(code):
    # print(code)
    remits = Remit.objects(organizationalUnitCode=code)
    # debug_print("GET REMIT BY CODE", remits.to_json())

    remitsToReturn = []
    for remit in remits:
        # print(remit.to_json())
        data = {
            "_id": str(remit.id),
            "organizationalUnitCode": remit.organizationalUnitCode,
            "remitText": remit.remitText,
            "remitType": remit.remitType,
            "cofog": remit.cofog.to_mongo().to_dict(),
            "status": remit.status,
            "legalProvisions": [],
        }
        # legal_provisions = [provision.to_dict() for provision in remit.legalProvisionRefs]
        legal_provisions = [provision for provision in remit.legalProvisionRefs]

        for provision in legal_provisions:
            legalActRef = provision.legalAct
            legalActKey = legalActRef.legalActKey
            legalProvisionSpecs = provision["legalProvisionSpecs"].to_mongo().to_dict()
            legalProvisionText = provision["legalProvisionText"]
            data["legalProvisions"].append(
                {
                    "_id": str(provision.id),
                    "legalActKey": legalActKey,
                    "legalProvisionSpecs": legalProvisionSpecs,
                    "legalProvisionText": legalProvisionText,
                }
            )

        remitsToReturn.append(data)

    # print(remitsToReurn)

    return Response(
        json.dumps(remitsToReturn),
        mimetype="application/json",
        status=200,
    )

@remit.route("/copy/<string:id>", methods=["GET"])
@jwt_required()
def copy_remit(id):
    curr_change = {}
    newLegalProvisions = []
    try:
        remit = Remit.objects(id=ObjectId(id)).first()
        debug_print("COPY REMIT BY ID", remit.to_json())

        organizationalUnitCode = remit.organizationalUnitCode
        remitText = remit.remitText
        remitType = remit.remitType
        cofog = remit.cofog
        legalProvisions = remit.legalProvisionRefs
        
        newRemit = Remit(
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

@remit.route("/<string:id>", methods=["DELETE"])
@jwt_required()
def delete_remit_by_code(id):
    
    try: 
        remit_to_delete = Remit.objects(id=ObjectId(id))
        
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