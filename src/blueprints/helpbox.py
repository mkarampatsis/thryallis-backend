import json
from bson import ObjectId
from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.models.psped.helpbox import Helpbox
from src.models.user import User
from src.blueprints.utils import debug_print, dict2string
from src.blueprints.decorators import can_edit, can_update_delete, can_finalize_remits


helpbox = Blueprint("helpbox", __name__)

@helpbox.route("", methods=["GET"])
@jwt_required()
def retrieve_all_questions():
    try:
        questions = Helpbox.objects()

        return Response(
            questions.to_json(),
            mimetype="application/json",
            status=200,
        )
    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία εμφάνθσης ερωτημάτων:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )    


@helpbox.route("", methods=["POST"])
@jwt_required()
def create_question():

    emails = User.objects(roles__role='HELPDESK').only('email').exclude("id")
    print (emails.to_json())

    pipeline = [
        {
            "$group":{
                "_id": {"email":"$toWhom"},
                "countNumberOfDocuments": {"$count": {}}
            }
        },
        {
            "$project": {
                "_id": 0,
                "email":"$_id.email",
                "countNumberOfDocuments":1,
            }
        }
    ]

    document_counts = list(Helpbox.objects.aggregate(pipeline))
    print (document_counts)

    # Create a lookup for document counts
    count_dict = {entry['email']: entry['countNumberOfDocuments'] for entry in document_counts}

    # Assign a default high value (e.g., float('inf')) for emails not in document_counts
    all_counts = [{'email': email['email'], 'countNumberOfDocuments': count_dict.get(email['email'], 0)} for email in emails]

    # Find the email with the lowest countNumberOfDocuments
    email_with_lowest_count = min(all_counts, key=lambda x: x['countNumberOfDocuments'])

    print("Email with lowest countNumberOfDocuments:", email_with_lowest_count['email'])

    try:
        data = request.get_json()
        debug_print("POST HELPBOX", data)

        email = data["email"]
        lastName = data["lastName"]
        firstName = data["firstName"]
        organizations = data["organizations"]
        questionTitle = data["questionTitle"]
        questionText = data["questionText"]

        newHelpbox = Helpbox(
            email=email,
            lastName=lastName,
            firstName=firstName,
            organizations=organizations,
            questionTitle=questionTitle,
            questionText=questionText,
            toWhom=email_with_lowest_count['email']            
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