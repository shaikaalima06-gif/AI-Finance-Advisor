
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from mysql.connector import Error

from db import get_db_connection

loans = Blueprint("loans", __name__)


@loans.route("/loans", methods=["POST"])
@jwt_required()
def add_loan():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    loan_name = data.get("loan_name")
    principal_amount = data.get("principal_amount")
    emi = data.get("emi")
    interest_rate = data.get("interest_rate", 0)

    if not loan_name or principal_amount is None or emi is None:
        return jsonify({
            "message": "Loan name, principal amount and EMI are required"
        }), 400

    try:
        principal_amount = Decimal(str(principal_amount))
        emi = Decimal(str(emi))
        interest_rate = Decimal(str(interest_rate))

        if (
            not principal_amount.is_finite()
            or not emi.is_finite()
            or not interest_rate.is_finite()
            or principal_amount <= 0
            or emi <= 0
            or interest_rate < 0
        ):
            raise ValueError("Loan amounts must be positive and interest rate cannot be negative")

    except (InvalidOperation, ValueError):
        return jsonify({
            "message": "Enter valid positive amounts and a non-negative interest rate"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO loans
                (user_id, loan_name, principal_amount, emi, interest_rate)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            loan_name,
            principal_amount,
            emi,
            interest_rate
        ))

        loan_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "message": "Loan added successfully",
            "loan_id": loan_id
        }), 201

    except Error:
        if connection:
            connection.rollback()
        app_error = "Could not save loan. Check the database table and connection."
        return jsonify({"message": app_error}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@loans.route("/loans", methods=["GET"])
@jwt_required()
def get_loans():
    user_id = get_jwt_identity()
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT loan_id, loan_name, principal_amount,
                   emi, interest_rate, created_at
            FROM loans
            WHERE user_id = %s
            ORDER BY loan_id DESC
        """, (user_id,))

        records = cursor.fetchall()

        for record in records:
            for key, value in record.items():
                if isinstance(value, Decimal):
                    record[key] = float(value)
                elif hasattr(value, "isoformat"):
                    record[key] = value.isoformat()

        return jsonify({
            "user_id": user_id,
            "loans": records
        }), 200

    except Error:
        return jsonify({
            "message": "Could not retrieve loans. Check the database table and connection."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
