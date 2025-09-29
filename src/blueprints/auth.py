from flask import Blueprint, request, Response
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.config import GOOGLE_AUDIENCE, CLIENT_ID, CLIENT_PWD, HORIZONTAL_ID, HORIZONTAL_PWD, TOKEN_URL, USER_INFO_URL, REDIRECT_URI, HORIZONTAL_URL
from src.models.user import User
from src.models.userGsis import UserGsis
import json
from src.models.psped.log import PspedSystemLog as Log
from src.models.psped.log import PspedSystemLogGsis as LogGsis
from src.models.apografi.organizational_unit import OrganizationalUnit
import requests as gsisRequest
import xml.etree.ElementTree as ET
import base64
import string
import random
import datetime

auth = Blueprint("auth", __name__)


@auth.route("/google-auth", methods=["POST"])
def google_auth():
  idToken = request.json["idToken"]

  try:
    id_info = id_token.verify_oauth2_token(idToken, requests.Request(), GOOGLE_AUDIENCE)
  except Exception as e:
    print(e)
    return Response({"error": "Invalid user"}, status=401)
  user = User.objects(googleId=id_info["sub"])

  if user:
    user.update(
      email=id_info["email"],
      firstName=id_info["given_name"],
      lastName=id_info["family_name"],
      name=id_info["name"],
      photoUrl=id_info["picture"],
      googleId=id_info["sub"],
    )
  else:
    User(
      email=id_info["email"],
      firstName=id_info["given_name"],
      lastName=id_info["family_name"],
      name=id_info["name"],
      photoUrl=id_info["picture"],
      googleId=id_info["sub"],
    ).save()

  user = User.get_user_by_email(id_info["email"]).to_mongo_dict()
  additional_claims = {"roles": user["roles"]}
  access_token = create_access_token(identity=id_info["email"], additional_claims=additional_claims)

  Log(user_id=id_info["email"], action="login", data={"email": id_info["email"]}).save()

  return Response(json.dumps({"accessToken": access_token, "user": user}), status=200)


@auth.route("/gsisUser/<string:code>", methods=["GET"])
def gsis_login(code: str):
      
  try: 
    clientId = CLIENT_ID
    clientSecret = CLIENT_PWD
    redirectUri = REDIRECT_URI
    tokenUrl = TOKEN_URL
    userInfoUrl = USER_INFO_URL

    payload = {
      "grant_type": "authorization_code",
      "client_id": clientId,
      "client_secret": clientSecret,
      "redirect_uri": redirectUri,
      "code": code,
      "scope":"read"
    }
    # Send request to GSIS token endpoint
    response = gsisRequest.post(tokenUrl, data=payload)
    
    if response.status_code == 200:
      access_token_gsis = response.json()
      
      # Ensure token is correctly formatted as "Bearer <token>"
      access_token_bearer = f"Bearer {access_token_gsis['access_token']}"
      
      gsis_header = {
        "Authorization": access_token_bearer  # Should be in format "Bearer <token>"
      }

      userRequest = gsisRequest.get(userInfoUrl, headers=gsis_header)
      # print(userRequest.text)
      gsisUser = xml_to_json(userRequest.text)

      # Procedures to get details from OPSDD
      if userRequest.status_code == 200:
        try:
          # client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
          # host_ip = request.host
          
          opsddRoles = getOpsdRoles()
          opsddUser = getOpsddUser(gsisUser['taxid'])
          print("aaaaaaa")
          # Create Users Object
          role_lookup = { (role["roleId"], role["hid"]): role["roleName"] for role in opsddRoles }

          # Enrich authorisations with roleName
          for user in opsddUser:
            for auth in user["authorisations"]:
              roleId = auth["role"]["roleId"]
              hid = auth["role"]["hid"]
              roleName = role_lookup.get((roleId, hid))
              if roleName:
                auth["role"]["roleName"] = roleName
            
          roles = []
          for user in opsddUser:
            for auth in user["authorisations"]:
              role ={
                "role": auth["role"]["roleName"],
                "active": True,
                "foreas":[auth["userOrgCode"]],
                "monades": get_ouUnit_codes(auth["userOrgCode"])
              }
              roles.append(role)
          
          print("Roles", roles, gsisUser)
          userGsis = UserGsis.objects(taxid=gsisUser['taxid'])

          if userGsis:
            print("1>>>>",userGsis)
            userGsis.update(
              firstname = gsisUser["firstname"],
              lastname = gsisUser["lastname"],
              fathername = gsisUser["fathername"],
              mothername = gsisUser["mothername"],
              name = gsisUser["firstname"] + ' ' + gsisUser["lastname"],
              taxid = gsisUser["taxid"],
              gsisUserid = gsisUser["userid"],
              empOrgUnitTexts = opsddUser[0]["empOrgUnitTexts"],
              employeeId = opsddUser[0]["employeeId"],
              roles = roles
            )
          else:
            print("2>>>>",userGsis)
            UserGsis(
              firstname = gsisUser["firstname"],
              lastname = gsisUser["lastname"],
              fathername = gsisUser["fathername"],
              mothername = gsisUser["mothername"],
              name = gsisUser["firstname"] + ' ' + gsisUser["lastname"],
              taxid = gsisUser["taxid"],
              gsisUserid = gsisUser["userid"],
              empOrgUnitTexts = opsddUser[0]["empOrgUnitTexts"],
              employeeId = opsddUser[0]["employeeId"],
              roles = roles
            ).save()

          print(userGsis, roles)
          additional_claims = {"roles": roles}
          access_token = create_access_token(identity=gsisUser['taxid'], additional_claims=additional_claims)
          user = {
            "firstname": gsisUser["firstname"],
            "lastname": gsisUser["lastname"],
            "fathername": gsisUser["fathername"],
            "mothername": gsisUser["mothername"],
            "name": gsisUser["firstname"] + ' ' + gsisUser["lastname"],
            "taxid": gsisUser["taxid"],
            "gsisUserid": gsisUser["userid"],
            "empOrgUnitTexts": opsddUser[0]["empOrgUnitTexts"],
            "employeeId": opsddUser[0]["employeeId"],
            "roles":roles
          }

          print("User>>", user)

          LogGsis(user_id=gsisUser["taxid"], action="login", data=user).save()

          return Response(json.dumps({
            "accessToken": access_token, 
            "user": user,
          }), status=200)


        except Exception as err:
          print(err)
          return Response(
            json.dumps({"message": "Πρόβλημα στην εξαγωγή στοιχείων για το οριζόντιο ΠΣ", "details":err}),
            mimetype="application/json",
            status=404,
          )
      else:
        return Response(json.dumps({"message": "Πρόβλημα στη εξαγωγή του χρήστη", "details": userRequest.text }), status=userRequest.status_code)
      
    else:
      return Response(json.dumps({"message": "Πρόβλημα στη εξαγωγή του token", "details": response.text }), status=response.status_code) 
          
  except Exception as err:
    print(err)
    return Response(
      json.dumps({"message": "Πρόβλημα στην εξαγωγή του code, προσπαθήστε ξανά.", "details":err}),
      mimetype="application/json",
      status=404,
    )
    
@auth.route("/gsisRole/<string:role>", methods=["GET"])
def gsis_create_role(role: str):
  print("OPSDD Create Role")
  
  try:
    
    OPSDD_ROLE = HORIZONTAL_URL + "/padRoleManagement"
    
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    host_ip = request.host
    
    data = f"{HORIZONTAL_ID}:{HORIZONTAL_PWD}".encode('utf-8')
    encoded_data = base64.b64encode(data).decode('utf-8')
    basic_auth = f"Basic { encoded_data }"
    horizontal_header = {
      "Authorization": basic_auth,
      "Content-Type": "application/json"
    }

    opsdd_create_role = {
      "auditRecord": {
        "auditTransactionId": randomString(),
        "auditTransactionDate": datetime.datetime.now().isoformat(),
        "auditUnit": "ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ",
        "auditProtocol": randomString(),
        "auditUserId": "markos.karampatsis",
        "auditUserIp": client_ip
      },
      "padRoleManagementInputRecord": {
        "lang": "el",
        "source": {
          "roles": [
            { "roleName": role }
          ]
        }
      }
    }

    roleOPSDD = gsisRequest.post(OPSDD_ROLE, headers=horizontal_header, json=opsdd_create_role)
    
    return Response(json.dumps({
      "roleOPSDD": roleOPSDD.json(), 
      "client": client_ip, 
      "host":host_ip, 
      "timestamp": datetime.datetime.now().isoformat(),
    }), status=200)

  except Exception as err:
    print(err)
    return Response(
      json.dumps({"message": "Πρόβλημα στην δημιουργία του ρόλου", "details":err}),
      mimetype="application/json",
      status=404,
    )

@auth.route("/gsisRole", methods=["PUT"])
def gsis_update_role():
    print("OPSDD Update Role")
    
    try:
      
      data = request.get_json()
      roleName = data["roleName"]
      roleId = data["roleId"]
      hid = data["hid"]

      OPSDD_ROLE = HORIZONTAL_URL + "/padRoleManagement"
      
      client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
      host_ip = request.host
      
      data = f"{HORIZONTAL_ID}:{HORIZONTAL_PWD}".encode('utf-8')
      encoded_data = base64.b64encode(data).decode('utf-8')
      basic_auth = f"Basic { encoded_data }"
      horizontal_header = {
        "Authorization": basic_auth,
        "Content-Type": "application/json"
      }

      opsdd_create_role = {
        "auditRecord": {
          "auditTransactionId": randomString(),
          "auditTransactionDate": datetime.datetime.now().isoformat(),
          "auditUnit": "ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ",
          "auditProtocol": randomString(),
          "auditUserId": "markos.karampatsis",
          "auditUserIp": client_ip
        },
        "padRoleManagementInputRecord": {
          "lang": "el",
          "source": {
            "roles": [
              { 
                "roleId": roleId,
                "roleName": roleName,
                "hid": hid
              }
            ]
          }
        }
      }

      roleOPSDD = gsisRequest.post(OPSDD_ROLE, headers=horizontal_header, json=opsdd_create_role)
      
      return Response(json.dumps({
        "roleOPSDD": roleOPSDD.json(), 
        "client": client_ip, 
        "host":host_ip, 
        "timestamp": datetime.datetime.now().isoformat(),
      }), status=200)

    except Exception as err:
      print(err)
      return Response(
        json.dumps({"message": "Πρόβλημα στην δημιουργία του ρόλου", "details":err}),
        mimetype="application/json",
        status=404,
      )

def getOpsddUser(vat: str):
  print("GET OPSDD User", vat)
      
  try:
    OPSDD_EMP_LIST = HORIZONTAL_URL + "/padEmplList"

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    data = f"{HORIZONTAL_ID}:{HORIZONTAL_PWD}".encode('utf-8')
    encoded_data = base64.b64encode(data).decode('utf-8')
    basic_auth = f"Basic { encoded_data }"
    horizontal_header = {
      "Authorization": basic_auth,
      "Content-Type": "application/json"
    }

    horizontal_emp_list_payload = {
      "auditRecord": {
        "auditTransactionId": randomString(),
        "auditTransactionDate": datetime.datetime.now().isoformat(),
        "auditUnit": "ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ",
        "auditProtocol": randomString(),
        "auditUserId": "markos.karampatsis",
        "auditUserIp": client_ip
      },
      "padEmplListInputRecord": {
        "page": "1",
        "size": "15",
        "lang": "el",
        "source": {
          # "employee":  { "employeeVatNo":  vat}
          "employee":  { "employeeVatNo": "065733009" }
        }
      }
    }

    listOPSDD = gsisRequest.post(OPSDD_EMP_LIST, headers=horizontal_header, json=horizontal_emp_list_payload).json()
    
    return listOPSDD["padEmplListOutputRecord"]["pageModel"]["pubAuthDoc"]["employeesList"]["employees"]
  
  except Exception as err:
    print(err)
    return Response(
      json.dumps({"message": "Πρόβλημα στην εξαγωγή χρήστη για το οριζόντιο ΠΣ", "details":err}),
      mimetype="application/json",
      status=404,
    )

def getOpsdRoles():
  print("GET OPSDD Roles")
      
  try:
    OPSDD_SYSTEM_INFO = HORIZONTAL_URL + "/padInfoSystemAll"

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    data = f"{HORIZONTAL_ID}:{HORIZONTAL_PWD}".encode('utf-8')
    encoded_data = base64.b64encode(data).decode('utf-8')
    basic_auth = f"Basic { encoded_data }"
    horizontal_header = {
      "Authorization": basic_auth,
      "Content-Type": "application/json"
    }

    horizontal_system_info_payload = {
      "auditRecord": {
      "auditTransactionId": randomString(),
      "auditTransactionDate": datetime.datetime.now().isoformat(),
      "auditUnit": "ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ",
      "auditProtocol": randomString(),
      "auditUserId": "markos.karampatsis",
      "auditUserIp": client_ip
      },
      "padInfoSystemAllInputRecord": {
          "lang": "el"
      }
    }

    rolesOPSDD = gsisRequest.post(OPSDD_SYSTEM_INFO, headers=horizontal_header, json=horizontal_system_info_payload).json()
    return rolesOPSDD['padInfoSystemAllOutputRecord']['pageModel']['pubAuthDoc']['informationSystem']['roles']

  except Exception as err:
    print(err)
    return Response(
      json.dumps({"message": "Πρόβλημα στην εξαγωγή ρόλων για το οριζόντιο ΠΣ", "details":err}),
      mimetype="application/json",
      status=404,
    )
       

def xml_to_json(xml_str):
  """Convert XML string to JSON."""
  root = ET.fromstring(xml_str)
  user_info = root.find("userinfo")  # Find the <userinfo> element

  if user_info is None:
    return {"error": "Invalid XML format"}

  return {
    "userid": user_info.get("userid", "").strip(),
    "taxid": user_info.get("taxid", "").strip(),
    "lastname": user_info.get("lastname", "").strip(),
    "firstname": user_info.get("firstname", "").strip(),
    "fathername": user_info.get("fathername", "").strip(),
    "mothername": user_info.get("mothername", "").strip(),
    "birthyear": user_info.get("birthyear", "").strip()
  }

def randomString():
  length = 6
  random_string = ''.join(random.choices(string.digits, k=length))
  return random_string


def get_ouUnit_codes(org_code: str):
  units = OrganizationalUnit.objects(organizationCode=org_code)
  codes = [unit.code for unit in units]
  return codes

# @auth.route("/gsisHorizontal", methods=["GET"])
# def test_horizontal():
#     print("GSIS TEST Horizontal")
#     try:
        
#         HORIZONTAL_SYSTEM_INFO = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padInfoSystemAll"
#         HORIZONTAL_EMP_COUNT = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padEmplListCount"
#         HORIZONTAL_EMP_LIST = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padEmplList"
#         HORIZONTAL_ROLE = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padRoleManagement"
        
#         # ip_addr = request.remote_addr
#         client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
#         host_ip = request.host
#         print(client_ip, host_ip, randomString())
             
#         data = f"{HORIZONTAL_ID}:{HORIZONTAL_PWD}".encode('utf-8')
#         encoded_data = base64.b64encode(data).decode('utf-8')
      
#         basic_auth = f"Basic { encoded_data }"
            
#         header = {
#             "Authorization": basic_auth,
#             "Content-Type": "application/json"
#         }

#         users = [
#           ["2525","037450866"],
#           ["2526","056177410"],
#           ["2527","070522760"],
#           ["2528","069851540"],
#           ["2529","161808050"],
#         ]

#         result = []
#         for i in users: 
#             horizontal_system_info_payload = {
#                 "auditRecord": {
#                 "auditTransactionId": randomString(),
#                 "auditTransactionDate": datetime.datetime.now().isoformat(),
#                 "auditUnit": "ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ",
#                 "auditProtocol": randomString(),
#                 "auditUserId": "markos.karampatsis",
#                 "auditUserIp": client_ip
#                 },
#                 "padInfoSystemAllInputRecord": {
#                     "lang": "el"
#                 }
#             }

#             horizontal_emp_list_payload = {
#                 "auditRecord": {
#                 "auditTransactionId": randomString(),
#                 "auditTransactionDate": datetime.datetime.now().isoformat(),
#                 "auditUnit": "ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ",
#                 "auditProtocol": randomString(),
#                 "auditUserId": "markos.karampatsis",
#                 "auditUserIp": client_ip
#                 },
#                 "padEmplListInputRecord": {
#                     "page": "1",
#                     "size": "15",
#                     "lang": "el",
#                     "source": {
#                         "employee": {}
#                     }
#                 }
#             }

#             horizontal_emp_count_payload = {
#             "auditRecord": {
#                 "auditTransactionId": randomString(),
#                 "auditTransactionDate": datetime.datetime.now().isoformat(),
#                 "auditUnit": "ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ",
#                 "auditProtocol": randomString(),
#                 "auditUserId": "markos.karampatsis",
#                 "auditUserIp": client_ip
#                 },
#                 "padEmplListCountInputRecord": {
#                 "lang": "el",
#                 "source": {
#                     "employee": {}
#                 }
#                 }
#             }

#             horizontal_role_payload = {
#                 "auditRecord": {
#                 "auditTransactionId": randomString(),
#                 "auditTransactionDate": datetime.datetime.now().isoformat(),
#                 "auditUnit": "ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ",
#                 "auditProtocol": randomString(),
#                 "auditUserId": "markos.karampatsis",
#                 "auditUserIp": client_ip
#                 },
#                 "padRoleManagementInputRecord": {
#                     "lang": "el",
#                     "source": {
#                         "roles": [
#                             {
#                                 "roleId": 2320,
#                                 "roleName": "Help Desk",
#                                 "hid": 2268
#                             }
#                         ]
#                     }
#                 }
#             }

#             horizontal_emp_2525_payload = {
#                 "auditRecord": {
#                     "auditTransactionId": randomString(),
#                     "auditTransactionDate": datetime.datetime.now().isoformat(),
#                     "auditUnit": "ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ",
#                     "auditProtocol": randomString(),
#                     "auditUserId": i[0],  # Insert user ID
#                     "auditUserIp": client_ip
#                 },
#                 "padEmplListInputRecord": {
#                     "page": "1",
#                     "size": "15",
#                     "lang": "el",
#                     "source": {
#                         "employee": {"employeeVatNo": i[1]}  # Insert VAT number
#                     }
#                 }
#             }
            
#             print (i[0], i[1], horizontal_emp_2525_payload)
#             system_info = gsisRequest.post(HORIZONTAL_SYSTEM_INFO, headers=header, json=horizontal_system_info_payload)
#             # if system_info.status_code == 200:
#             #     print("Response 1:", system_info.json())
#             # else:
#             #     print(f"Error 1: {system_info.status_code}: {system_info.text}")
#             emp_list = gsisRequest.post(HORIZONTAL_EMP_LIST, headers=header, json=horizontal_emp_list_payload)
#             emp_2525 = gsisRequest.post(HORIZONTAL_EMP_LIST, headers=header, json=horizontal_emp_2525_payload)
#             emp_count = gsisRequest.post(HORIZONTAL_EMP_COUNT, headers=header, json=horizontal_emp_count_payload)
#             emp_role = gsisRequest.post(HORIZONTAL_ROLE, headers=header, json=horizontal_role_payload)
            
#             result.append({
#                 "client": client_ip, 
#                 "host":host_ip, 
#                 "timestamp": datetime.datetime.now().isoformat(),
#                 "horizontal_system_info_payload": horizontal_system_info_payload,
#                 "horizontal_emp_list_payload": horizontal_emp_list_payload,
#                 "horizontal_emp_2525_payload": horizontal_emp_2525_payload,
#                 "horizontal_emp_count_payload": horizontal_emp_count_payload,
#                 "horizontal_role_payload": horizontal_role_payload
#                 })
        
#         # print(result[0])
        
#         return Response(json.dumps({
#             # "system_info": system_info.json(),
#             # "emp_list": emp_list.json(), 
#             # "emp_2525": emp_2525.json(), 
#             # "emp_count": emp_count.json(), 
#             # "emp_role": emp_role.json(), 
#             # "ip_address":{
#               # "client": client_ip, 
#               # "host":host_ip, 
#               # "timestamp": datetime.datetime.now().isoformat(),
#               # "horizontal_system_info_payload": horizontal_system_info_payload,
#               # "horizontal_emp_list_payload": horizontal_emp_list_payload,
#               # "horizontal_emp_2525_payload": horizontal_emp_2525_payload,
#               # "horizontal_emp_count_payload": horizontal_emp_count_payload,
#               # "horizontal_role_payload": horizontal_role_payload
#             # } 
#             "result": result
#           }), status=200)
            
#     except Exception as err:
#         print(err)
#         return Response(
#             json.dumps({"message": "Πρόβλημα στην εξαγωγή στοιχείων για το οριζόντιο ΠΣ.", "details":err}),
#             mimetype="application/json",
#             status=404,
#         )