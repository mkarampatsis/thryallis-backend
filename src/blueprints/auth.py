from flask import Blueprint, request, Response
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.config import GOOGLE_AUDIENCE, CLIENT_ID, CLIENT_PWD
from src.models.user import User
import json
from src.models.psped.log import PspedSystemLog as Log
import requests
import xml.etree.ElementTree as ET


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
        clientId = CLIENT_ID,
        clientSecret = CLIENT_PWD,
        redirectUri = 'https://ypes.ddns.net',
        scope = 'openid profile email offline_access roles',
        TOKEN_URL = 'https://test.gsis.gr/oauth2servergov/oauth/token'
        USER_INFO_URL = "https://test.gsis.gr/oauth2servergov/userinfo?format=xml"

        # URL of the login, logout, and silent refresh endpoints
        loginUrl = 'https://test.gsis.gr/oauth2servergov/oauth/authorize',
        logoutUrl = 'https://test.gsis.gr/oauth2servergov/logout',
        tokenEndpoint = 'https://test.gsis.gr/oauth2servergov/oauth/token',
        userinfoEndpoint = 'https://test.gsis.gr/oauth2servergov/userinfo?format=xml',
        
        payload = {
            "grant_type": "authorization_code",
            "client_id": clientId,
            "client_secret": clientSecret,
            "redirect_uri": redirectUri,
            "code": code,
            "scope":"read"
        }


        # Send request to GSIS token endpoint
        response = requests.post(TOKEN_URL, data=payload)
        
        if response.status_code == 200:
            access_token = response.json()
            
            # Ensure token is correctly formatted as "Bearer <token>"
            access_token_bearer = f"Bearer {access_token['access_token']}"
            
            headers = {
                "Authorization": access_token_bearer  # Should be in format "Bearer <token>"
            }

            userRequest = requests.get(USER_INFO_URL, headers=headers)
            json_user = xml_to_json(userRequest.text)
            
            if userRequest.status_code == 200:
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
