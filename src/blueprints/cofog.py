from flask import Blueprint, request, Response
from src.models.cofog import Cofog
import json
from bson import json_util

cofog = Blueprint("cofog", __name__)


@cofog.route("")
def get_cofog():
    try:
      cofog = Cofog.objects.aggregate([
        {
          "$addFields": {
              "codeInt": { "$toInt": "$code" }
          }
        },
        {
          "$sort": { "codeInt": 1 }
        }
      ]) 
      cofog_list = list(cofog)
      return Response(
        json_util.dumps({"data": cofog_list}),
        mimetype="application/json",
        status=200,
    )
    except Cofog.DoesNotExist:
      return Response(
          json.dumps({"error": "Δεν βρέθηκαν δεδομένα COFOG"}),
          mimetype="application/json",
          status=404,
      )
