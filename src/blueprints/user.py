from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from wtforms.validators import email
from src.models.user import User, UserRole
from src.models.userGsis import UserGsis, UserRoleGSIS
from src.models.psped.change import Change
from src.blueprints.decorators import has_admin_role
import json
import re

user = Blueprint("user", __name__)

@user.route("/myaccesses")
@jwt_required()
def get_my_organizations():

  regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
  if(re.fullmatch(regex, get_jwt_identity())):
    print("Email",get_jwt_identity())
    user = User.get_user_by_email(get_jwt_identity())
  else:
    print("Vat Id",get_jwt_identity())
    user = UserGsis.objects.get(taxid=get_jwt_identity())

  roles = user.roles
  organizationCodesListofLists = [role.foreas for role in roles if role.active and role.role in ["ADMIN", "EDITOR"]]
  organizationCodes = [item for sublist in organizationCodesListofLists for item in sublist]
  monadesCodesListofLists = [role.monades for role in roles if role.active and role.role in ["ADMIN", "EDITOR"]]
  monadesCodes = [item for sublist in monadesCodesListofLists for item in sublist]

  return Response(json.dumps({"organizations": organizationCodes, "organizational_units": monadesCodes}), status=200)

@user.route("/<string:category>/<string:id>", methods=["GET"])
@jwt_required()
@has_admin_role
def get_user(category: str, id: str):

  try:
    if category == "google":
      user = User.objects.get(email=id)
    elif category == "gsis":
      user = UserGsis.objects.get(taxid=id)
    else:
      return Response(
        json.dumps({"message": f"<strong>Αποτυχία εμφάνισης χρήστη:</strong> Άγνωστη κατηγορία χρήστη {category}"}),
        mimetype="application/json",
        status=400,
      ) 
    
    return Response(
      json.dumps({"user": json.loads(user.to_json())}),
      mimetype="application/json",
      status=200,
    )
  
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης χρήστη:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@user.route("/all")
@jwt_required()
@has_admin_role
def get_all_users():
  googleUsers = User.objects()
  gsisUsers = UserGsis.objects()

  try:
    users = {
      "googleUsers": json.loads(googleUsers.to_json()),
      "gsisUsers": json.loads(gsisUsers.to_json())
    }

    return jsonify(users), 200
  except Exception as e:
    print(e)
    return Response(
        json.dumps({"message": f"<strong>Αποτυχία εμφάνισης χρηστών:</strong> {e}"}),
        mimetype="application/json",
        status=500,
    )

@user.route("/<string:email>", methods=["PUT"])
@jwt_required()
@has_admin_role
def set_user_accesses(email: str):

  try:
    
    data = request.get_json()

    roles_data = data["roles"]
    # Convert dicts to UserRole embedded documents
    roles = [UserRole(**r) for r in roles_data]

    user = User.objects.get(email=email)

    user.roles = roles
    user.save()

    who = get_jwt_identity()
    what = {"entity": "user", "key": {"email": email}}
    Change(action="update", who=who, what=what, change={"roles": roles}).save()

    return Response(
      json.dumps({"message": "<strong>Ο χρηστης ενημερώθηκε</strong>"}),
      mimetype="application/json",
      status=201,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία τροποποίησης του χρήστη:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@user.route("/gsis/<string:taxid>", methods=["PUT"])
@jwt_required()
@has_admin_role
def set_user_accesses_gsis(taxid: str):

  try:
    
    data = request.get_json()
    roles_data = data["roles"]

    # Convert dicts to UserRole embedded documents
    roles = [UserRoleGSIS(**r) for r in roles_data]

    user = UserGsis.objects.get(taxid=taxid)
    user.roles = roles
    user.save()

    who = get_jwt_identity()
    what = {"entity": "user", "key": {"taxid": taxid}}
    Change(action="update", who=who, what=what, change={"roles": roles}).save()

    return Response(
      json.dumps({"message": "<strong>Ο χρηστης ενημερώθηκε</strong>"}),
      mimetype="application/json",
      status=201,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία τροποποίησης του χρήστη:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )