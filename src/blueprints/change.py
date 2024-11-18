from bson import ObjectId
from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.models.psped.change import Change
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
            {"$group": 
                { 
                    "_id": 0, 
                    "organizationalUnits":  { "$addToSet": "$what.key.organizationalUnitCode" },
                }
            },
            {
                "$project": {
                    "organizationalUnits": 1,
                    "_id":0,
                }
            }
        ]
        
        resultRemits = Change.objects.aggregate(pipeline)

        # Convert the CommandCursor to a list
        result_list_remits = list(resultRemits)

        result = {
            "organizations": result_list_organizations[0]['organizations'],
            "organizationalUnits": result_list_organizationalUnits[0]['organizationalUnits'],
            "remits": result_list_remits[0]['organizationalUnits']
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
    print(code)
    changes = Change.objects(__raw__={"$or":[
        {"what.key.code":code},
        {"what.key.organizationalUnitCode":code}
    ]}).order_by("when")

    # debug_print("GET CHANGES BY CODE", changes.to_json())

    return Response(
        changes.to_json(),
        mimetype="application/json",
        status=200,
    )
