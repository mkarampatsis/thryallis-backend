import json
from bson import ObjectId
from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.models.psped.helpbox import Helpbox, Question
from src.models.psped.change import Change
from src.models.user import User
from src.blueprints.utils import debug_print, dict2string
from src.blueprints.decorators import can_edit, can_update_delete, can_finalize_remits
from datetime import datetime


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
            json.dumps({"message": f"<strong>Αποτυχία εμφάνισης ερωτημάτων:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )    

@helpbox.route("/id/<string:id>", methods=["GET"])
@jwt_required()
def retrieve_question_by_id(id):
    try:
        questions = Helpbox.objects(id=id)

        return Response(
            questions.to_json(),
            mimetype="application/json",
            status=200,
        )
    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία εμφάνισης ερωτημάτων:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )   

@helpbox.route("", methods=["POST"])
@jwt_required()
def create_question():

    emails = User.objects(roles__role='HELPDESK').only('email').exclude("id")
    # print (emails.to_json())

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
                "count": {"$size":"$questions"}
            }
        }
    ]

    document_counts = list(Helpbox.objects.aggregate(pipeline))
    # print (document_counts)

    # Create a lookup for document counts
    count_dict = {entry['email']: entry['countNumberOfDocuments'] for entry in document_counts}

    # Assign a default high value (e.g., float('inf')) for emails not in document_counts
    all_counts = [{'email': email['email'], 'countNumberOfDocuments': count_dict.get(email['email'], 0)} for email in emails]

    # Find the email with the lowest countNumberOfDocuments
    email_with_lowest_count = min(all_counts, key=lambda x: x['countNumberOfDocuments'])

    # print("Email with lowest countNumberOfDocuments:", email_with_lowest_count['email'])

    try:
        data = request.get_json()
        debug_print("POST HELPBOX", data)

        email = data["email"]
        lastName = data["lastName"]
        firstName = data["firstName"]
        organizations = data["organizations"]
        questionTitle = data["questionTitle"]
        question = [data["question"]]

        newHelpbox = Helpbox(
            email=email,
            lastName=lastName,
            firstName=firstName,
            organizations=organizations,
            questionTitle = questionTitle,
            questions = question,
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

@helpbox.route("/<string:id>", methods=["PUT"])
@jwt_required()
def update_question(id):
    try:
        data = request.get_json()
        debug_print("INSERT NEW QUESTION TO HELPBOX", data)

        helpboxID = id
        questionText = data["question"]["questionText"]

        helpbox = Helpbox.objects.get(id=ObjectId(helpboxID))
        # print (helpbox.to_json())

        new_question = Question(
            questionText=questionText,
        )
        
        # Add the new question to the 'questions' field
        helpbox.questions.append(new_question)
        
        # Save the updated Helpbox document
        helpbox.save()

        return Response(
            json.dumps({"message": "Η απάντηση σας καταχωρήθηκε με επιτυχία"}),
            mimetype="application/json",
            status=201,
        )

    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία καταχώρησης απάντησης:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )


@helpbox.route("", methods=["PUT"])
@jwt_required()
def answer_question():
    try:
        data = request.get_json()
        debug_print("ANSWER HELPBOX", data)

        helpboxId = data["helpBoxId"]
        questionId = data["questionId"]
        answerText = data["answerText"]
        fromWhom = data["fromWhom"]

        helpbox = Helpbox.objects.get(id=ObjectId(helpboxId))
        print (helpbox.to_json())
        if helpbox:
            # Locate the specific Question in the questions list
            question_to_update = next((q for q in helpbox.questions if str(q.id) == questionId), None)
            
            if question_to_update:
                # Update the `answered` field
                question_to_update.answered = True
                question_to_update.whenAnswered = datetime.now()
                question_to_update.answerText = answerText 
                question_to_update.fromWhom = fromWhom
                
                # Save the document to persist changes
                helpbox.save()

        return Response(
            json.dumps({"message": "Η απάντηση σας καταχωρήθηκε με επιτυχία"}),
            mimetype="application/json",
            status=201,
        )

    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία καταχώρησης απάντησης:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )

@helpbox.route("/publish", methods=["PUT"])
@jwt_required()
def publish_question():
    try:
        data = request.get_json()
        debug_print("PUBLISH HELPBOX", data)

        helpboxId = data["helpBoxId"]
        questionId = data["questionId"]
        published = data["published"]

        helpbox = Helpbox.objects.get(id=ObjectId(helpboxId))
        print (helpbox.to_json())
        
        if helpbox:
            # Locate the specific Question in the questions list
            question_to_update = next((q for q in helpbox.questions if str(q.id) == questionId), None)
            
            if question_to_update:
                # Update the `answered` field
                question_to_update.published = published
                                
                # Save the document to persist changes
                helpbox.save()

        return Response(
            json.dumps({"message": "Η απάντηση σας καταχωρήθηκε με επιτυχία"}),
            mimetype="application/json",
            status=201,
        )

    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία καταχώρησης απάντησης:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )

@helpbox.route("/finalize", methods=["PUT"])
@jwt_required()
def finalize_question():
    try:
        data = request.get_json()
        debug_print("FINALIZE HELPBOX", data)

        helpboxId = data["id"]
        finalized = data["finalized"]

        helpbox = Helpbox.objects.get(id=ObjectId(helpboxId))
        print (helpbox.to_json())
        
        helpbox.update(finalized=finalized)

        helpbox.save()

        return Response(
            json.dumps({"message": "Η απάντηση σας καταχωρήθηκε με επιτυχία"}),
            mimetype="application/json",
            status=201,
        )

    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία καταχώρησης απάντησης:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )