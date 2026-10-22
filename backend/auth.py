
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error

from db import get_db_connection

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not all(isinstance(v, str) and v.strip()
               for v in (name, email, password)):
        return jsonify({
            "message": "Name, email and password are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "message": "Password must be at least 8 characters"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id FROM users WHERE email = %s",
            (email.strip(),)
        )

        if cursor.fetchone():
            return jsonify({
                "message": "User already exists"
            }), 409

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (name.strip(), email.strip(), password_hash)
        )

        conn.commit()

        return jsonify({
            "message": "Registration successful",
            "user_id": cursor.lastrowid
        }), 201

    except Error:
        if conn is not None:
            conn.rollback()
        return jsonify({
            "message": "Database operation failed"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not email.strip() or \
       not isinstance(password, str) or not password:
        return jsonify({
            "message": "Email and password are required"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT user_id, name, email, password_hash
            FROM users
            WHERE email = %s
            """,
            (email.strip(),)
        )

        user = cursor.fetchone()

        if not user or not check_password_hash(
            user["password_hash"], password
        ):
            return jsonify({
                "message": "Invalid email or password"
            }), 401

        token = create_access_token(
            identity=str(user["user_id"])
        )

        return jsonify({
            "message": "Login successful",
            "access_token": token,
            "user": {
                "id": user["user_id"],
                "name": user["name"],
                "email": user["email"]
            }
        }), 200

    except Error:
        return jsonify({
            "message": "Database operation failed"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
