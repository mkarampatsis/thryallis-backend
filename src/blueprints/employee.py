import json
import os
from bson import ObjectId,json_util
from flask import Blueprint, Response, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from src.blueprints.utils import debug_print, dict2string
from src.models.resources.employee import Employee
from src.models.psped.change import Change
from src.models.upload import FileUpload 

employee = Blueprint("employee", __name__)

# Wmployee requests
@employee.route("", methods=["GET"])
def get_all_employees():
  try:
    employees = Employee.objects()

    return Response(
      questions.to_json(),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης προσωπικού:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@employee.route("/<string:id>", methods=["GET"])
def get_employee_by_id(id):
  try:
    employee = Employee.objects.get(id=ObjectId(id))
        
    return Response(
      facility.to_json(),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης προσωπικού:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@employee.route("/organization/<string:code>", methods=["GET"])
def get_employees_by_organization_code(code):
  try:
    employees = Employee.objects(organizationCode=code)

    return Response(
      employees.to_json(),
      mimetype="application/json",
      status=200,
    )
  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία εμφάνισης προσωπικού του φορέα:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@employee.route("", methods=["POST"])
@jwt_required()
def create_employee():

  try:
    data = request.get_json()
    debug_print("POST EMPLOYEE", data)

    newEmployee = Employee(
      organization = data["organization"],
      organizationCode = data["organizationCode"],
      code = data["code"],
      firstname = data["firstname"],
      lastname = data["lastname"],
      fathername = data["fathername"],
      mothername = data["mothername"],
      identity = data["identity"],
      birthday = data["birthday"],
      sex = data["sex"],
      dateAppointment = data["dateAppointment"],
      workStatus = data["workStatus"],
      workCategory = data["workCategory"],
      workSector = data["workSector"],
      organizationalUnit = data["organizationalUnit"],
      building = data["building"],
      office = data["office"],
      phoneWork = data["phoneWork"],
      emailWork = data["emailWork"],
      finalized = data["finalized"],
      qualifications = data["qualifications"],
    ).save()

    who = get_jwt_identity()
    what = {"entity": "employee", "key": {"employee": data}}
    
    Change(action="create", who=who, what=what, change={"employee":data}).save()

    return Response(
      json.dumps({"message": "Το προσωπικό καταχωρήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία καταχώρησης προσωπικού:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@employee.route("/<string:email>", methods=["PUT"])
@jwt_required()
def update_employee(email):

  try:
    data = request.get_json()
    debug_print("UPDATE EMPLOYEE", data)
    
    employee = Employee.objects.get(emailWork=email)

    employee.update(
      organization = data["organization"],
      organizationCode = data["organizationCode"],
      code = data["code"],
      firstname = data["firstname"],
      lastname = data["lastname"],
      fathername = data["fathername"],
      mothername = data["mothername"],
      identity = data["identity"],
      birthday = data["birthday"],
      sex = data["sex"],
      dateAppointment = data["dateAppointment"],
      workStatus = data["workStatus"],
      workCategory = data["workCategory"],
      workSector = data["workSector"],
      organizationalUnit = data["organizationalUnit"],
      building = data["building"],
      office = data["office"],
      phoneWork = data["phoneWork"],
      emailWork = data["emailWork"],
      finalized = data["finalized"],
      qualifications = data["qualifications"],
    )

    who = get_jwt_identity()
    what = {"entity": "employee", "key": {"emailWork": email}}
    
    Change(action="update", who=who, what=what, change={"old":employee, "new":data}).save()

    return Response(
      json.dumps({"message": "Το προσωπικό τροποποιήθηκε με επιτυχία"}),
      mimetype="application/json",
      status=201,
    )

  except Exception as e:
    print(e)
    return Response(
      json.dumps({"message": f"<strong>Αποτυχία τροποποίησης προσωπικού:</strong> {e}"}),
      mimetype="application/json",
      status=500,
    )

@employee.route("/<string:email>", methods=["DELETE"])
@jwt_required()
def delete_employee_by_email(email):
  try: 
    employee = Employee.objects.get(emailWork=email)

    # Delete referenced files of employee
    for q in employee.qualifications:
      file =q.file
      file_doc = FileUpload.objects(id=file["id"]).first()
      if file_doc:
        delete_uploaded_file(file_doc)
        file_doc.delete()
    
    # Delete the main document
    employee.delete()
  
  except DoesNotExist:
    return Response(json.dumps({"message": "Το προσωπικό δεν υπάρχει"}), mimetype="application/json", status=404)
  except Exception as e:
    return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)
  
  who = get_jwt_identity()
  what = {"entity": "employee", "key": {"emailWork": email}}
  
  Change(action="delete", who=who, what=what, change={"employee":employee.to_json()}).save()
  return Response(json.dumps({"message": "<strong>Το προσωπικό διαγράφηκε</strong>"}), mimetype="application/json", status=201)

# Function that deletes all referenced files
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