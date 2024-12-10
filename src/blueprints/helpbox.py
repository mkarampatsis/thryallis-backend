import json
from bson import ObjectId
from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.models.psped.helpbox import Helpbox
from src.blueprints.utils import debug_print, dict2string
from src.blueprints.decorators import can_edit, can_update_delete, can_finalize_remits


helpbox = Blueprint("helpbox", __name__)

@helpbox.route("", methods=["POST"])
@jwt_required()
def create_question():
    curr_change = {}
    try:
        data = request.get_json()
        debug_print("POST HELPBOX", data)

        email = data["email"]
        lastName = data["lastName"]
        firstName = data["firstName"]
        organizations = data["organizations"]
        questionText = data["questionText"]

        newHelpbox = Helpbox(
            email=email,
            lastName=lastName,
            firstName=firstName,
            organizations=organizations,
            questionText=questionText            
        ).save()

        return Response(
            json.dumps({"message": "Η ερώτηση σας καταχωρήθηκε με επιτυχία"}),
            mimetype="application/json",
            status=201,
        )

    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία καταχώρησης ερώτησης:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )