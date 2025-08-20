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

# @facility.route("/<string:id>", methods=["PUT"])
# @jwt_required()
# def update_facility(id):

#   try:
#     data = request.get_json()
#     debug_print("UPDATE FACILITY", data)
    
#     facility = Facility.objects.get(id=ObjectId(id))

#     serialized_floorPlans = []
#     for floor in data["floorPlans"]:
#       fileObjectIDs = [ObjectId(id_str) for id_str in floor["floorPlan"]]
#       serialized_floorPlan = {
#         "floorArea": floor["floorArea"],
#         "floorPlan": fileObjectIDs,
#         "level": floor["level"],
#         "num": floor["num"]
#       }
#       serialized_floorPlans.append(serialized_floorPlan)

#     facility.update(
#       organization = data["organization"],
#       organizationCode = data["organizationCode"],
#       kaek = data["kaek"],
#       belongsTo = data["belongsTo"],
#       distinctiveNameOfFacility = data["distinctiveNameOfFacility"],
#       useOfFacility =data["useOfFacility"],
#       uniqueUseOfFacility = data["uniqueUseOfFacility"],
#       private = data["private"],
#       coveredPremisesArea = data["coveredPremisesArea"],
#       floorsOrLevels = data["floorsOrLevels"],
#       floorPlans = serialized_floorPlans,
#       addressOfFacility = data["addressOfFacility"],
#       # finalized = True if data["finalized"]=='true' else False 
#       finalized = data["finalized"]
#     )

#     who = get_jwt_identity()
#     what = {"entity": "facility", "key": {"faciltyId": id}}
    
#     Change(action="update", who=who, what=what, change={"old":facility, "new":data}).save()

#     return Response(
#       json.dumps({"message": "Το ακίνητο σας τροποποιήθηκε με επιτυχία"}),
#       mimetype="application/json",
#       status=201,
#     )

#   except Exception as e:
#     print(e)
#     return Response(
#       json.dumps({"message": f"<strong>Αποτυχία τροποποίησης ακίνητου:</strong> {e}"}),
#       mimetype="application/json",
#       status=500,
#     )

# @facility.route("/<string:id>", methods=["DELETE"])
# @jwt_required()
# def delete_facility_by_id(id):
#   try: 
#     facility = Facility.objects.get(id=ObjectId(id))

#     # Delete referenced files of facility
#     for floorPlan in facility.floorPlans:
#       for item in floorPlan.floorPlan:
#         file_doc = FileUpload.objects(id=item["id"]).first()
#         if file_doc:
#           delete_uploaded_file(file_doc)
#           file_doc.delete()
    
#     # Delete all spaces of facility
#     spaces = Space.objects(facilityId=ObjectId(id))
#     for space in spaces:
#       space.delete()
    
#     # Delete the main document
#     facility.delete()
  
#   except DoesNotExist:
#     return Response(json.dumps({"message": "Το ακίνητο δεν υπάρχει"}), mimetype="application/json", status=404)
#   except Exception as e:
#     return Response(json.dumps({"message": f"<strong>Error:</strong> {str(e)}"}), mimetype="application/json", status=500)
  
#   who = get_jwt_identity()
#   what = {"entity": "facility", "key": {"Facility": id}}
  
#   Change(action="delete", who=who, what=what, change={"facility":facility.to_json()}).save()
#   return Response(json.dumps({"message": "<strong>Το ακίνητο διαγράφηκε</strong>"}), mimetype="application/json", status=201)

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