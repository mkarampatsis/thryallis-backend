from flask import Flask, jsonify, make_response

from flask_jwt_extended import JWTManager

from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from mongoengine import connect
from datetime import timedelta

from src.blueprints.auth import auth
from src.blueprints.user import user
from src.blueprints.apografi import apografi
from src.blueprints.psped import psped
from src.blueprints.stats import stats
from src.blueprints.cofog import cofog
from src.blueprints.log import log

from src.blueprints.remit import remit
from src.blueprints.legal_provision import legal_provision
from src.blueprints.legal_act import legal_act

from src.blueprints.upload import upload
from src.blueprints.change import change

from src.blueprints.helpbox import helpbox
from src.blueprints.facility import facility
from src.blueprints.equipment import equipment

from src.config import (
    MONGO_HOST,
    MONGO_PORT,
    MONGO_APOGRAFI_DB,
    MONGO_PSPED_DB,
    MONGO_RESOURCES_DB,
    MONGO_USERNAME,
    MONGO_PASSWORD,
    MONGO_AUTHENTICATION_SOURCE,
    MONGO_URI,
    JWT_SECRET_KEY,
    UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH,
)


app = Flask(__name__)

jwt = JWTManager(app)
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


@app.errorhandler(413)
def too_large(e):
    return make_response(jsonify(message="File is too large"), 413)

connect(host=MONGO_URI)
connect(
    host=MONGO_URI,
    # port=MONGO_PORT,
    # username=MONGO_USERNAME,
    # password=MONGO_PASSWORD,
    # authentication_source=MONGO_AUTHENTICATION_SOURCE,
    db=MONGO_APOGRAFI_DB,
    alias=MONGO_APOGRAFI_DB,
)

connect(
    host=MONGO_URI,
    #host=MONGO_URI_ATLAS,
    # port=MONGO_PORT,
    # username=MONGO_USERNAME,
    # password=MONGO_PASSWORD,
    # authentication_source=MONGO_AUTHENTICATION_SOURCE,
    db=MONGO_PSPED_DB,
    alias=MONGO_PSPED_DB,
)

connect(
    host=MONGO_URI,
    #host=MONGO_URI_ATLAS,
    # port=MONGO_PORT,
    # username=MONGO_USERNAME,
    # password=MONGO_PASSWORD,
    # authentication_source=MONGO_AUTHENTICATION_SOURCE,
    db=MONGO_RESOURCES_DB,
    alias=MONGO_RESOURCES_DB,
)

# CORS configuration
cors = CORS(
    app,
    resources={r"*": {"origins": ["http://localhost:4200", "https://ypes.ddns.net", "https://thryallis.ypes.gov.gr"]}},
)

# Register blueprints
app.register_blueprint(auth, url_prefix="/auth")
app.register_blueprint(user, url_prefix="/user")
app.register_blueprint(apografi, url_prefix="/apografi")
app.register_blueprint(stats, url_prefix="/apografi/stats")
app.register_blueprint(psped, url_prefix="/psped")
app.register_blueprint(cofog, url_prefix="/cofog")
app.register_blueprint(log, url_prefix="/log")
app.register_blueprint(upload, url_prefix="/upload")
app.register_blueprint(remit, url_prefix="/remit")
app.register_blueprint(legal_provision, url_prefix="/legal_provision")
app.register_blueprint(legal_act, url_prefix="/legal_act")
app.register_blueprint(change, url_prefix="/change")
app.register_blueprint(helpbox, url_prefix="/helpbox")
app.register_blueprint(facility, url_prefix="/facility")
app.register_blueprint(equipment, url_prefix="/equipment")