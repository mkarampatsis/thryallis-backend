from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.ota.instruction_act import InstructionAct
from src.models.psped.change import Change
from src.models.upload import FileUpload
import json
from bson import ObjectId
from mongoengine.errors import NotUniqueError
from src.blueprints.utils import debug_print

instruction_act = Blueprint("instruction_act", __name__)

@instruction_act.route("", methods=["POST"])
@jwt_required()
def create_instruction_act():
  who = get_jwt_identity()
  
  try:
    data = request.get_json()
    debug_print("POST CREATE INTRUCTION ACT", data)
    instructionActFile = FileUpload.objects.get(id=ObjectId(data["instructionActFile"]))

    del data["instructionActFile"]
    instructionAct = InstructionAct(**data, instructionActFile=instructionActFile)

    instructionActKey = instructionAct.create_key()
    
    what = {"entity": "instructionAct", "key": {"code": instructionActKey}}

    instructionAct.save()
    Change(action="create", who=who, what=what, change=instructionAct.to_mongo()).save()

    return Response(
      json.dumps({"message": f"Επιτυχής δημιουργία εγκύκλιας οδηγίας: <strong>{instructionAct.instructionActKey}</strong>"}),
      mimetype="application/json",
      status=201,
    )
  except NotUniqueError:

    return Response(
      json.dumps({"message": "Απόπειρα δημιουργίας διπλοεγγραφής."}),
      mimetype="application/json",
      status=409,
    )
  except Exception as e:
    return Response(
      json.dumps({"message": "Απόπειρα δημιουργίας διπλοεγγραφής."})
      if "duplicate key error" in str(e)
      else json.dumps({"message": f"Αποτυχία ενημέρωσης εγκύκλιας οδηγίας: {e}"}),
      mimetype="application/json",
      status=500,
    )

@instruction_act.route("/<string:id>", methods=["PUT"])
@jwt_required()
def update_instructionact(id):
    who = get_jwt_identity()
    try:
        data = request.get_json()
        debug_print("INSTRUCTION ACT PUT DATA", data)
        # Find the instructionAct to be updated by its id
        instructionAct = InstructionAct.objects.get(id=ObjectId(id))
        foundinstructionActKey = instructionAct.instructionActKey  # Save the key of the found instructionAct for "what"
        debug_print("FOUND INSTRUCTION ACT", instructionAct.to_mongo().to_dict())
        
        try:
            instructionActFile = FileUpload.objects.get(id=ObjectId(data["instructionActFile"]["$oid"]))
        except Exception:
            instructionActFile = FileUpload.objects.get(id=ObjectId(data["instructionActFile"]))
        
        # Update the found instructionAct with the new data
        for key, value in data.items():
            if hasattr(instructionAct, key):
                if key == "instructionActFile":
                    setattr(instructionAct, key, instructionActFile)
                else:
                    setattr(instructionAct, key, value)
        # Generate a new instructionActKey based on the updated data
        instructionActKey = instructionAct.create_key()
        instructionAct.instructionActKey = instructionActKey
        debug_print("UPDATED INSTRUCTION ACT", instructionAct.to_mongo().to_dict())
        updatedInstructionAct = instructionAct.to_mongo()  # Save the updated instructionAct for "change"
        updatedInstructionActDict = updatedInstructionAct.to_dict()  # Convert the updated instructionAct to a dictionary
        del updatedInstructionActDict["_id"]  # instructionAct to be updated already has an id
        instructionAct.update(**updatedInstructionActDict)  # Update the instructionAct with the new data
        what = {"entity": "instructionAct", "key": {"instructionActKey": foundinstructionActKey}}
        # Save the change in the database
        Change(action="update", who=who, what=what, change=updatedInstructionAct).save()

        return Response(
            json.dumps({"message": "Επιτυχής ενημέρωση εγκύκλιας οδηγίας."}),
            mimetype="application/json",
            status=201,
        )

    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": "Απόπειρα δημιουργίας διπλοεγγραφής."})
            if "duplicate key error" in str(e)
            else json.dumps({"message": f"Αποτυχία ενημέρωσης εγκύκλιας οδηγίας: {e}"}),
            mimetype="application/json",
            status=500,
        )


@instruction_act.route("", methods=["GET"])
# @jwt_required()
def list_all_nomikes_praxeis():
    nomikes_praxeis = InstructionAct.objects()
    return Response(nomikes_praxeis.to_json(), mimetype="application/json", status=200)


@instruction_act.route("/count", methods=["GET"])
@jwt_required()
def count_all_nomikes_praxeis():
    count = InstructionAct.objects().count()
    return Response(json.dumps({"count": count}), mimetype="application/json", status=200)


@instruction_act.route("/by-id/<string:id>", methods=["GET"])
@jwt_required()
def get_nomiki_praxi_by_id(id: str):
    try:
        instructionAct = InstructionAct.objects.get(id=ObjectId(id))
        return Response(instructionAct.to_json(), mimetype="application/json", status=200)
    except InstructionAct.DoesNotExist:
        return Response(
            json.dumps({"message": f"Νομική πράξη με id {id} δεν βρέθηκε"}),
            mimetype="application/json",
            status=404,
        )

@instruction_act.route("/by-act-key/<path:act_id>", methods=["GET"])
# @jwt_required()
def get_nomiki_praxi_act_key(act_id):
    print(act_id)
    try:
        instructionAct = InstructionAct.objects.get(instructionActKey=act_id)
        return Response(instructionAct.to_json(), mimetype="application/json", status=200)
    except InstructionAct.DoesNotExist:
        return Response(
            json.dumps({"message": f"Νομική πράξη με Act-Key {id} δεν βρέθηκε"}),
            mimetype="application/json",
            status=404,
        )