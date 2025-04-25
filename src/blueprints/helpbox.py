import json
from bson import ObjectId
from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.models.psped.helpbox import Helpbox, Question, Whom
from src.models.psped.general_info import GeneralInfo
# from src.models.psped.change import Change
from src.models.user import User
from src.blueprints.utils import debug_print, dict2string
from src.blueprints.decorators import can_edit, can_update_delete, can_finalize_remits
from datetime import datetime
import string
import random

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
    
@helpbox.route("/all/published", methods=["GET"])
@jwt_required()
def retrieve_all_published_questions():

    pipeline = [
        {
            "$unwind": "$questions"
        },
        {
            "$match": {
                "questions.published": True
            }
        },
        {
            "$project": {
                "_id":0,
                "questionTitle":1,
                "questions.questionText":1,
                "questions.answerText":1,
                "questions.whenAsked":1,
                "questions.whenAnswered":1,
            }
        },
        { 
            "$sort" : { 
                "questions.whenAnswered" : -1 
            } 
        }
    ]

    try:
        pubished = list(Helpbox.objects.aggregate(pipeline))

        return Response(
            json.dumps({"data": pubished}, default=custom_serializer),
            # jsonify(json.loads(json.dumps(pubished, default=custom_serializer))),
            mimetype="application/json",
            status=200,
        )
    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία εμφάνισης απαντημένων ερωτημάτων:</strong> {e}"}),
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
                "_id": {"email":"$toWhom.email"},
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
    helpdeskUser = User.objects.get(email=email_with_lowest_count['email'])

    # print("Email with lowest countNumberOfDocuments:", email_with_lowest_count['email'])

    try:
        data = request.get_json()
        debug_print("POST HELPBOX", data)

        email = data["email"]
        lastName = data["lastName"]
        firstName = data["firstName"]
        organizations = data["organizations"]
        questionTitle = data["questionTitle"]
        questionCategory = data["questionCategory"]
        question = [data["question"]]
        toWhom = {
          "email" : helpdeskUser["email"],
          "firstName" : helpdeskUser["firstName"],
          "lastName" : helpdeskUser["lastName"]
        }

        length = 6
        random_string = ''.join(random.choices(string.digits, k=length))

        newHelpbox = Helpbox(
            key = random_string,
            email=email,
            lastName=lastName,
            firstName=firstName,
            organizations=organizations,
            questionTitle = questionTitle,
            questionCategory = questionCategory,
            questions = question,
            toWhom = toWhom         
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
        questionFile = data["question"]['questionFile']

        helpbox = Helpbox.objects.get(id=ObjectId(helpboxID))
        # print (helpbox.to_json())
  
        new_question = Question(
            questionText = questionText,
            questionFile = questionFile
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
        answerFile = data["answerFile"]
        fromWhom = data["fromWhom"]

        helpbox = Helpbox.objects.get(id=ObjectId(helpboxId))

        if helpbox:
            # Locate the specific Question in the questions list
            question_to_update = next((q for q in helpbox.questions if str(q.id) == questionId), None)
            
            if question_to_update:
                # Update the `answered` field
                question_to_update.answered = True
                question_to_update.whenAnswered = datetime.now()
                question_to_update.answerText = answerText
                question_to_update.answerFile = ObjectId(answerFile) 
                question_to_update.fromWhom = Whom(**fromWhom)
                
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

# GENERAL INFO API
@helpbox.route("/general-info", methods=["GET"])
@jwt_required()
def retrieve_all_general_info():
    try:
        infos = GeneralInfo.objects().order_by('-when')
        # print(infos.to_json())
        return Response(
            infos.to_json(),
            mimetype="application/json",
            status=200,
        )
    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία εμφάνισης ενημερώσεων:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )    
    
@helpbox.route("/general-info", methods=["POST"])
@jwt_required()
def create_general_info():

    try:
        data = request.get_json()
        debug_print("POST GENERAL INFO", data)

        email = data["email"]
        lastName = data["lastName"]
        firstName = data["firstName"]
        title = data["title"]
        text = data["text"]
        file = data["file"]
        # tags = data["tags"]
        category = data["category"]

        newInfo = GeneralInfo(
            email=email,
            lastName=lastName,
            firstName=firstName,
            title = title,
            text = text,
            file = file,
            # tags = tags
            category = category
        ).save()

        return Response(
            json.dumps({"message": "Η ενημέρωση σας καταχωρήθηκε με επιτυχία"}),
            mimetype="application/json",
            status=201,
        )

    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία καταχώρησης ενημέρωσης:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )

def custom_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # Convert datetime to ISO 8601 format
    raise TypeError("Type not serializable")