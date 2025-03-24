from flask import Blueprint, request, Response
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.config import GOOGLE_AUDIENCE, CLIENT_ID, CLIENT_PWD, HORIZONTAL_ID, HORIZONTAL_PWD
from src.models.user import User
import json
from src.models.psped.log import PspedSystemLog as Log
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
    print("GSIS")
    try: 
        clientId = CLIENT_ID,
        clientSecret = CLIENT_PWD,
        redirectUri = 'https://ypes.ddns.net/login',
        scope = 'openid profile email offline_access roles',
        TOKEN_URL = 'https://test.gsis.gr/oauth2servergov/oauth/token'
        USER_INFO_URL = "https://test.gsis.gr/oauth2servergov/userinfo?format=xml"

        HORIZONTAL_SYSTEM_INFO = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padInfoSystemAll"
        HORIZONTAL_EMP_COUNT = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padEmplListCount"
        HORIZONTAL_EMP_LIST = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padEmplList"
        HORIZONTAL_ROLE = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padRoleManagement"

        payload = {
            "grant_type": "authorization_code",
            "client_id": clientId,
            "client_secret": clientSecret,
            "redirect_uri": redirectUri,
            "code": code,
            "scope":"read"
        }

        # Send request to GSIS token endpoint
        response = gsisRequest.post(TOKEN_URL, data=payload)
        print("1>>", response.json())
        
        if response.status_code == 200:
            access_token = response.json()
            
            # Ensure token is correctly formatted as "Bearer <token>"
            access_token_bearer = f"Bearer {access_token['access_token']}"
            
            headers = {
                "Authorization": access_token_bearer  # Should be in format "Bearer <token>"
            }

            userRequest = gsisRequest.get(USER_INFO_URL, headers=headers)
            print("2>>", userRequest.text)
            json_user = xml_to_json(userRequest.text)
            
            if userRequest.status_code == 200:
                ip_addr = request.remote_addr
                data = f"{HORIZONTAL_ID}:{HOSRIZONTAL_PWD}".encode('utf-8')
                encoded_data = base64.b64encode(data).decode('utf-8')

                horizontal_header = f"Basic {data}"
            
                headers = { "Authorization": horizontal_header }

                horizontal_system_info_payload = {
                    "auditRecord": {
                    "auditTransactionId": "1",
                    "auditTransactionDate": "2022-09-05T12:09:10Z",
                    "auditUnit": "GSIS",
                    "auditProtocol": "1",
                    "auditUserId": "user",
                    "auditUserIp": "0.0.0.0"
                    },
                    "padInfoSystemAllInputRecord": {
                        "lang": "el"
                    }
                }

                horizontal_emp_list_payload = {
                    "auditRecord": {
                    "auditTransactionId": "1",
                    "auditTransactionDate": "2022-09-05T12:09:10Z",
                    "auditUnit": "GSIS",
                    "auditProtocol": "1",
                    "auditUserId": "user",
                    "auditUserIp": "0.0.0.0"
                    },
                    "padEmplListInputRecord": {
                        "page": "1",
                        "size": "15",
                        "lang": "el",
                        "source": {
                            "employee": {}
                        }
                    }
                }

                system_info = gsisRequest.post(HORIZONTAL_SYSTEM_INFO, headers=horizontal_header, data=horizontal_system_info_payload)
                print("3>>", system_info.json())
                
                emp_list = gsisRequest.post(HORIZONTAL_SYSTEM_EMP_LIST, headers=horizontal_header, data=horizontal_emp_list_payload)
                print("4>>", emp_list.json())

                return Response(json.dumps({"accessToken": access_token, "user": json_user }), status=200)
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
@auth.route("/gsisHorizontal", methods=["GET"])
def gsis_horizontal():
    print("GSIS Horizontal")
    try: 
        
        HORIZONTAL_SYSTEM_INFO = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padInfoSystemAll"
        HORIZONTAL_EMP_COUNT = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padEmplListCount"
        HORIZONTAL_EMP_LIST = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padEmplList"
        HORIZONTAL_ROLE = "https://test.gsis.gr/esbpilot/pubAuthDocManagementRestService/padRoleManagement"
        
        # ip_addr = request.remote_addr
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        host_ip = request.host
        print(client_ip, host_ip, randomString())
             
        data = f"{HORIZONTAL_ID}:{HORIZONTAL_PWD}".encode('utf-8')
        encoded_data = base64.b64encode(data).decode('utf-8')
      
        basic_auth = f"Basic { encoded_data }"
            
        header = {
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
                    "employee": {}
                }
            }
        }

        horizontal_emp_2525_payload = {
            "auditRecord": {
            "auditTransactionId": randomString(),
            "auditTransactionDate": datetime.datetime.now().isoformat(),
            "auditUnit": "ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ",
            "auditProtocol": randomString(),
            "auditUserId": "2529",
            "auditUserIp": client_ip
            },
            "padEmplListInputRecord": {
                "page": "1",
                "size": "15",
                "lang": "el",
                "source": {
                    "employee": {"employeeVatNo": "037450866"}
                }
            }
        }

        horizontal_emp_count_payload = {
          "auditRecord": {
            "auditTransactionId": randomString(),
            "auditTransactionDate": datetime.datetime.now().isoformat(),
            "auditUnit": "ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ",
            "auditProtocol": randomString(),
            "auditUserId": "markos.karampatsis",
            "auditUserIp": client_ip
            },
            "padEmplListCountInputRecord": {
              "lang": "el",
              "source": {
                  "employee": {}
              }
            }
        }

        horizontal_role_payload = {
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
                            "roleId": 2320,
                            "roleName": "Help Desk",
                            "hid": 2268
                        }
                    ]
                }
            }
        }

        # print(horizontal_system_info_payload, horizontal_emp_list_payload, horizontal_emp_count_payload)

        system_info = gsisRequest.post(HORIZONTAL_SYSTEM_INFO, headers=header, json=horizontal_system_info_payload)
        # if system_info.status_code == 200:
        #     print("Response 1:", system_info.json())
        # else:
        #     print(f"Error 1: {system_info.status_code}: {system_info.text}")
        emp_list = gsisRequest.post(HORIZONTAL_EMP_LIST, headers=header, json=horizontal_emp_list_payload)
        emp_2525 = gsisRequest.post(HORIZONTAL_EMP_LIST, headers=header, json=horizontal_emp_2525_payload)
        emp_count = gsisRequest.post(HORIZONTAL_EMP_COUNT, headers=header, json=horizontal_emp_count_payload)
        emp_role = gsisRequest.post(HORIZONTAL_ROLE, headers=header, json=horizontal_role_payload)
      

        return Response(json.dumps({
            "system_info": system_info.json(),
            "emp_list": emp_list.json(), 
            "emp_2525": emp_2525.json(), 
            "emp_count": emp_count.json(), 
            "emp_role": emp_role.json(), 
            "ip_address":{
              "client": client_ip, 
              "host":host_ip, 
              "timestamp": datetime.datetime.now().isoformat(),
              "horizontal_system_info_payload": horizontal_system_info_payload,
              "horizontal_emp_list_payload": horizontal_emp_list_payload,
              "horizontal_emp_2525_payload": horizontal_emp_2525_payload,
              "horizontal_emp_count_payload": horizontal_emp_count_payload,
              "horizontal_role_payload": horizontal_role_payload
            } 
          }), status=200)
            
    except Exception as err:
        print(err)
        return Response(
            json.dumps({"message": "Πρόβλημα στην εξαγωγή στοιχείων για το οριζόντιο ΠΣ.", "details":err}),
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

# @auth.route("/profile", methods=["PATCH"])
# @jwt_required()
# def update_profile():
#     user = User.get_user_by_email(get_jwt_identity())
#     data = request.json
#     user.update(demoSite=data["demoSite"])
#     user.reload()
#     user = user.to_mongo_dict()

#     return Response(json.dumps({"user": user, "msg": f"Your demo site is updated to: {user['demoSite']}"}), status=200)


# # Endpoint to retrieve all users
# @auth.route("/users", methods=["GET"])
# @jwt_required()
# def get_users():
#     users = User.objects()
#     users = [user.to_mongo_dict() for user in users]
#     return Response(json.dumps(users), status=200)


# @auth.route("/user", methods=["GET"])
# @jwt_required()
# def get_user():
#     user = User.get_user_by_email(get_jwt_identity())
#     return Response(json.dumps(user.to_mongo_dict()), status=200)
