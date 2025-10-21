from bson import ObjectId
from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.models.psped.change import Change
from src.models.user import User
from bson import json_util  # handles ObjectId, datetime
import json

from .utils import debug_print

change = Blueprint("change", __name__)


@change.route("/allChangesCodesByType", methods=["get"])
# @jwt_required()
def getOrganizations():
    try:
        pipeline = [
            {"$match": {"what.entity": "organization"}},
            {
                "$group":{
                    "_id":None,
                    "organizations": { "$addToSet": "$what.key.code" }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "organizations": 1
                }
            }
        ]
        resultOrganizations = Change.objects.aggregate(pipeline)
        # Convert the CommandCursor to a list
        result_list_organizations = list(resultOrganizations)
        
        pipeline = [
            {"$match": {"what.entity": "organizationalUnit"}},
            {
                "$group":{
                    "_id":None,
                    "organizationalUnits": { "$addToSet": "$what.key.code" }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "organizationalUnits":1
                }
            }
        ]
        resultOrganizationalUnits = Change.objects.aggregate(pipeline)
        # Convert the CommandCursor to a list
        result_list_organizationalUnits = list(resultOrganizationalUnits)

        pipeline = [
            {"$match": {"what.entity":"remit"}},
            {
                "$project": {
                "_id":1,
                }
            }
        ]
        
        resultRemits = Change.objects.aggregate(pipeline)

        # Convert the CommandCursor to a list
        result_list_remits = list(resultRemits)
        # Convert ObjectIds to strings
        for r in result_list_remits:
            if isinstance(r.get("_id"), ObjectId):
                r["_id"] = str(r["_id"])

        result = {
            "organizations": result_list_organizations[0]['organizations'],
            "organizationalUnits": result_list_organizationalUnits[0]['organizationalUnits'],
            "remits": result_list_remits[0]
        }

        # print(result)
        return Response(
            json.dumps({"data": result}),
            mimetype="application/json",
            status=200,
        )

    except Exception as e:
        print(e)
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία ανάκτησης ιστορικών στοιχείων φορεών:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )

@change.route("/<string:code>", methods=["GET"])
@jwt_required()
def retrieve_change_by_code(code):
    # print(code)
    changes = Change.objects(__raw__={"$or":[
        {"what.key.code":code},
        {"what.key.organizationalUnitCode":code}
    ]}).order_by("when")

    result = []
    for row in changes:
        try: 
            user = User.objects.get(email=row.who)
            who_data = {
                "firstName" : user.firstName,
                "lastName" :user.lastName,
                "email" : user.email
            }
        except User.DoesNotExist:
            who_data = {"email": row.who, "firstName": "", "lastName": ""}
        
        row_dict = row.to_mongo().to_dict()
        row_dict["who"] = who_data  # override string with full object
        result.append(row_dict)
    
    # debug_print("GET CHANGES BY CODE", changes.to_json())

    return Response(
        # changes.to_json(),
        json.dumps(result, default=json_util.default),
        mimetype="application/json",
        status=200,
    )


@change.route("/<string:id>", methods=["GET"])
@jwt_required()
def retrieve_change_by_id(id):
    
    try:
        change = Change.objects.get(id=ObjectId(id))

        return Response(
            change.to_json(),
            mimetype="application/json",
            status=200,
        )    
    except Exception as e:
        return Response(
            json.dumps({"message": f"<strong>Αποτυχία εμφάνισης ιστορικού:</strong> {e}"}),
            mimetype="application/json",
            status=500,
        )

     