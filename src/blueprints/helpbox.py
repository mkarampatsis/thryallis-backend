import json
import os
from bson import ObjectId,json_util
from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.models.psped.helpbox import Helpbox, Question, Whom
from src.models.psped.general_info import GeneralInfo
from src.models.upload import FileUpload 
from src.models.psped.change import Change
from src.models.user import User
from src.models.userGsis import UserGsis
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
        # Step 1: Fetch Helpbox
        helpbox = Helpbox.objects.get(id=ObjectId(id))

        # Step 2: Convert Helpbox to dict and format fields
        helpbox_dict = helpbox.to_mongo().to_dict()
        helpbox_dict['id'] = str(helpbox_dict.pop('_id'))
       
       # Convert and process each question
        enriched_questions = []
        for question in helpbox_dict.get('questions', []):
            question_id = str(question['id'])
            file_ids = [oid for oid in question.get('questionFile', [])]

            # Get all file documents for the question for questionFile
            files = FileUpload.objects(id__in=file_ids)
            question['questionFile'] = [
                {
                    "id": str(file.id),
                    "file_name": file.file_name,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "file_location": file.file_location
                }
                for file in files
            ]

            file_ids = [oid for oid in question.get('answerFile', [])]

            # Get all file documents for the question for answerFile
            files = FileUpload.objects(id__in=file_ids)
            question['answerFile'] = [
                {
                    "id": str(file.id),
                    "file_name": file.file_name,
                    "file_type": file.file_type,
                    "file_size": file.file_size,
                    "file_location": file.file_location
                }
                for file in files
            ]

            # Format ObjectIds and datetime
            question['id'] = str(question['id'])
            if 'whenAsked' in question:
                question['whenAsked'] = question['whenAsked'].isoformat()
            if 'whenAnswered' in question:
                question['whenAnswered'] = question['whenAnswered'].isoformat()

            enriched_questions.append(question)

        # Replace questions with enriched versions
        helpbox_dict['questions'] = enriched_questions
        
        return Response(
            json.dumps(helpbox_dict),
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

  data = request.get_json()
  debug_print("POST HELPBOX", data)
  
  pipeline = [
    {
      "$match":{
        "enableGoogleAuth":data["enableGoogleAuth"]
      }
    },
    {
      "$group":{
        "_id": {"user":"$toWhom.user"},
        "countNumberOfDocuments": {"$count": {}}
      }
    },
    {
      "$project": {
        "_id": 0,
        "user":"$_id.user",
        "countNumberOfDocuments":1,
      }
    }
  ]

  if data["enableGoogleAuth"]:
    users = User.objects(roles__role='HELPDESK').only('email').exclude("id")
  else:
    users = UserGsis.objects(roles__role='HELPDESK').only('taxid').exclude("id")
  
  document_counts = list(Helpbox.objects.aggregate(pipeline))
  
  # Create a lookup for document counts
  count_dict = {entry['user']: entry['countNumberOfDocuments'] for entry in document_counts}
  
  # Assign a default high value (e.g., float('inf')) for user not in document_counts
  if data["enableGoogleAuth"]:
    all_counts = [{'user': email['email'], 'countNumberOfDocuments': count_dict.get(email['email'], 0)} for email in users]
  else:
    all_counts = [{'user': taxid['taxid'], 'countNumberOfDocuments': count_dict.get(taxid['taxid'], 0)} for taxid in users]
  
    # Find the taxid with the lowest countNumberOfDocuments
  user_with_lowest_count = min(all_counts, key=lambda x: x['countNumberOfDocuments'])
  
  if data["enableGoogleAuth"]:
    helpdeskUser = User.objects.get(email=user_with_lowest_count['user'])
  else:
    helpdeskUser = UserGsis.objects.get(taxid=user_with_lowest_count['user'])

  try:
    fileObjectIDs = []

    files = data["question"]['questionFile']
    if files:
      # Convert to ObjectId instances
      fileObjectIDs = [ObjectId(id_str) for id_str in files]

    email = data["email"]
    taxid = data["taxid"]
    lastName = data["lastName"]
    firstName = data["firstName"]
    organizations = data["organizations"]
    questionTitle = data["questionTitle"]
    questionCategory = data["questionCategory"]
    question = [{
      "questionText": data["question"]['questionText'],
      "questionFile": fileObjectIDs
    }]
    toWhom = {
      "user" : helpdeskUser["taxid"] if 'taxid' in helpdeskUser else helpdeskUser["email"],
      "firstName" : helpdeskUser["firstName"],
      "lastName" : helpdeskUser["lastName"]
    }
    enableGoogleAuth = data["enableGoogleAuth"] 

    length = 6
    random_string = ''.join(random.choices(string.digits, k=length))

    newHelpbox = Helpbox(
      key = random_string,
      email=email,
      taxid = taxid,
      lastName=lastName,
      firstName=firstName,
      organizations=organizations,
      questionTitle = questionTitle,
      questionCategory = questionCategory,
      questions = question,
      toWhom = toWhom,
      enableGoogleAuth = enableGoogleAuth     
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
    
    if questionFile:
      # Convert to ObjectId instances
      fileObjectIDs = [ObjectId(id_str) for id_str in questionFile]
    
    new_question = Question(
      questionText = questionText,
      questionFile = fileObjectIDs
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
        # Convert to ObjectId instances
        fileObjectIDs = [ObjectId(id_str) for id_str in answerFile]
        
        # Update the `answered` field
        question_to_update.answered = True
        question_to_update.whenAnswered = datetime.now()
        question_to_update.answerText = answerText
        question_to_update.answerFile = fileObjectIDs 
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
        infos = GeneralInfo.objects.order_by('-when')
        output = []
        
        for info in infos:
            data = info.to_mongo().to_dict()
            
            # Manually replace the 'file' field with the actual file document(s)
            data['file'] = [
                f.to_mongo().to_dict() for f in info.file if f is not None
            ]

            output.append(data)

        return Response(
            json_util.dumps(output),  # Handles ObjectId and datetime serialization
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
        category = data["category"]

        newInfo = GeneralInfo(
            email=email,
            lastName=lastName,
            firstName=firstName,
            title = title,
            text = text,
            file = file,
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
@helpbox.route("/general-info/<string:generalInfoId>", methods=["PUT"])
@jwt_required()
def update_general_info(generalInfoId):

    try:
        data = request.get_json()
        debug_print("PUT GENERAL INFO", data)

        email = data["email"]
        lastName = data["lastName"]
        firstName = data["firstName"]
        title = data["title"]
        text = data["text"]
        file = data["file"]
        category = data["category"]

        # Convert to ObjectId instances
        fileObjectIDs = [ObjectId(id_str) for id_str in file]
        # print(fileObjectIDs)
        
        generalInfo = GeneralInfo.objects.get(id=ObjectId(generalInfoId))

        generalInfo.update(
          email = email,
          lastName = lastName,
          firstName = firstName,
          title = title,
          text = text,
          file = fileObjectIDs,
          category = category,
        )

        curr_change = {
          "old": {
            "email": generalInfo.email,
            "lastName": generalInfo.lastName,
            "firstName": generalInfo.firstName,
            "title": generalInfo.title,
            "text": generalInfo.text,
            "file": generalInfo.file,
            "category": generalInfo.category,
          },
          "new": {
            "email": email,
            "lastName": lastName,
            "firstName": firstName,
            "title": title,
            "text": text,
            "file": file,
            "category": category,
          },
        }
        who = get_jwt_identity()
        what = {"entity": "generalInfo", "key": {"generalInfoId": generalInfoId}}
        Change(action="update", who=who, what=what, change=curr_change).save()

        return Response(
            json.dumps({"message": "Η πληροφορία ενημερώθηκε με επιτυχία"}),
            mimetype="application/json",
            status=201,
        )

    except Exception as e:
        print("UPDATE GENERAL INFO EXCEPTION", e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία ενημέρωσης πληροφορίας:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )


@helpbox.route("/general-info/<string:id>", methods=["DELETE"])
@jwt_required()
def delete_general_info_by_id(id):

    try: 
        general_info_to_delete = GeneralInfo.objects(id=ObjectId(id))
        
        # Delete referenced files
        for general_info in general_info_to_delete:
            for item in general_info.file:
                file_doc = FileUpload.objects(id=item["id"]).first()
                if file_doc:
                    # print (file_doc.to_json())
                    delete_uploaded_file(file_doc)
                    file_doc.delete()
        # Delete the main document
        general_info_to_delete.delete()
    
    except DoesNotExist:
        return Response(json.dumps({"message": "Η πληροφορία δεν υπάρχει"}), mimetype="application/json", status=404)
    except Exception as e:
        return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)
    
    who = get_jwt_identity()
    what = {"entity": "generalInfo", "key": {"GeneralInfo": id}}
    # print(general_info_to_delete)
    Change(action="delete", who=who, what=what, change={"general_info":general_info_to_delete.to_json()}).save()
    return Response(json.dumps({"message": "<strong>H πληροφορία διαγράφηκε</strong>"}), mimetype="application/json", status=201)

@helpbox.route("/general-info/<string:infoId>/file/<string:fileId>", methods=["DELETE"])
@jwt_required()
def delete_file_from_general_info(infoId,fileId):

    try: 
        general_info_to_delete = GeneralInfo.objects.get(id=ObjectId(infoId))
        
        file_doc = FileUpload.objects.get(id=ObjectId(fileId))
        if file_doc:
          delete_uploaded_file(file_doc)
          file_doc.delete()
          # Remove the file ObjectId from the `file` list
          general_info_to_delete.update(pull__file=ObjectId(fileId))
          
          # Refresh the instance so it has the updated file list
          general_info_to_delete.reload()
          
          data = general_info_to_delete.to_mongo().to_dict()
          # Manually replace the 'file' field with the actual file document(s)
          data['file'] = [
            f.to_mongo().to_dict() for f in general_info_to_delete.file if f is not None
          ]

    except FileUpload.DoesNotExist:
        return Response(json.dumps({"message": "Η πληροφορία δεν υπάρχει"}), mimetype="application/json", status=404)
    except Exception as e:
        return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)
    
    who = get_jwt_identity()
    what = {"entity": "generalInfo", "key": {"GeneralInfo": infoId}}
    
    Change(action="delete", who=who, what=what, change={"general_info":file_doc.to_json()}).save()
    return Response(json_util.dumps({
      "message": "<strong>Το αρχείο διαγράφηκε</strong>", 
      "data":data
      }), 
      mimetype="application/json", 
      status=201
    )

def custom_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # Convert datetime to ISO 8601 format
    raise TypeError("Type not serializable")

def delete_uploaded_file(file_doc):
  try:
    # Combine path and filename
    file_path = os.path.join(file_doc["file_location"], file_doc["file_id"])

    # Check if file exists
    if os.path.exists(file_path):
      os.remove(file_path)
      print(f"Deleted: {file_path}")
      return True
    else:
      print(f"File not found: {file_path}")
      return False

  except Exception as e:
    print(f"Error deleting file: {e}")
    return False