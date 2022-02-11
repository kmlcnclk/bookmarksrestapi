from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from src.constants.http_status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT
import validators
from src.database import User, db
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flasgger import swag_from
from src.errors.custom_error import CustomError

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth.post("/register")
@swag_from("./docs/auth/register.yaml")
def register():
    username = request.json.get(
        "username") if request.json and request.json.get("username") else None
    email = request.json.get(
        "email") if request.json and request.json.get("email") else None
    password = request.json.get(
        "password") if request.json and request.json.get("password") else None

    if username is None:
        raise CustomError("Username is required",
                          HTTP_400_BAD_REQUEST,)

    if email is None:
        return jsonify({"success": False, "message": "Email is required"}), HTTP_400_BAD_REQUEST

    if password is None:
        return jsonify({"success": False, "message": "Password is required"}), HTTP_400_BAD_REQUEST

    if len(password) < 6:
        return jsonify({"success": False,
                        "error": {"message": "Password must be at least 6 characters long", }}), HTTP_400_BAD_REQUEST

    if len(username) < 3:
        return jsonify({"success": False,
                        "error": {
                            "message":
                                "Username must be at least 3 characters long", }}), HTTP_400_BAD_REQUEST

    if not username.isalnum() or " " in username:
        return jsonify({"success": False,
                        "error": {
                            "message":
                                "Username should be alphanumeric, also no spaces", }}), HTTP_400_BAD_REQUEST

    if not validators.email(email):
        return jsonify({"success": False,
                        "error": {
                            "message":
                                "Email is not valid", }}), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"success": False,
                        "error": {
                            "message":
                                "Email is taken", }}), HTTP_409_CONFLICT

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"success": False,
                        "error": {
                            "message":
                                "Username is taken", }}), HTTP_409_CONFLICT

    pwd_hash = generate_password_hash(password)

    user = User(username=username, email=email, password=pwd_hash)
    db.session.add(user)
    db.session.commit()

    return jsonify({"success": True,
                    "message": "User successfully created"}), HTTP_200_OK


@auth.post("/login")
@swag_from("./docs/auth/login.yaml")
def login():
    email = request.json.get(
        "email") if request.json and request.json.get("email") else None
    password = request.json.get(
        "password") if request.json and request.json.get("password") else None

    if email is None:
        return jsonify({"success": False, "message": "Email is required"}), HTTP_400_BAD_REQUEST

    if password is None:
        return jsonify({"success": False, "message": "Password is required"}), HTTP_400_BAD_REQUEST

    user = User.query.filter_by(email=email).first()
    if user:
        is_pass_correct = check_password_hash(user.password, password)
        if is_pass_correct:
            refresh = create_refresh_token(identity=user.id)
            access = create_access_token(identity=user.id)
            out = jsonify(success=True, access=access,
                          refresh=refresh)
            out.set_cookie('access', access)
            out.set_cookie('refresh', refresh)
            return out, HTTP_200_OK
        else:
            return jsonify({"success": False, "message": "Password is not correct"}), HTTP_401_UNAUTHORIZED
    else:
        return jsonify({"success": False, "message": "User does not exist"}), HTTP_401_UNAUTHORIZED


@auth.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()

    user = User.query.filter_by(id=user_id).first()

    if user:
        return jsonify({"success": True, "username": user.username, "email": user.email, }), HTTP_200_OK
    else:
        return jsonify({"success": False, "message": "User does not exist"}), HTTP_401_UNAUTHORIZED


@auth.post("/token/refresh")
@jwt_required(refresh=True)
def refresh_user_token():
    identity = get_jwt_identity()

    access = create_access_token(identity=identity)

    out = jsonify(success=True, access=access)
    out.delete_cookie('access')
    out.delete_cookie('refresh')
    out.set_cookie('access', access)
    return out, HTTP_200_OK
