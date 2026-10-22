
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from mysql.connector import Error

from db import get_db_connection

income = Blueprint("income", __name__)


@income.route("/income", methods=["POST"])
@jwt_required()
def add_income():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    amount = data.get("amount")
    source = data.get("source")
    income_date = data.get("income_date") or data.get("date")

    if amount is None:
        return jsonify({"message": "Amount is required"}), 400

    try:
        amount = Decimal(str(amount))
        if not amount.is_finite() or amount <= 0:
            raise ValueError()
        if amount.as_tuple().exponent < -2:
            raise ValueError()
    except (InvalidOperation, ValueError):
        return jsonify({
            "message": "Amount must be positive with at most 2 decimal places"
        }), 400

    if not isinstance(source, str) or not source.strip():
        return jsonify({"message": "Source is required"}), 400

    try:
        income_date = date.fromisoformat(str(income_date))
    except (TypeError, ValueError):
        return jsonify({
            "message": "A valid date is required (YYYY-MM-DD)"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO transactions (user_id, amount, category, type, date)
            VALUES (%s, %s, %s, 'income', %s)
            """,
            (int(user_id), amount, source.strip(), income_date)
        )

        transaction_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "message": "Income added successfully",
            "transaction_id": transaction_id
        }), 201

    except Error:
        if connection is not None:
            connection.rollback()
        return jsonify({
            "message": "Database operation failed"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@income.route("/income", methods=["GET"])
@jwt_required()
def get_income():
    user_id = get_jwt_identity()
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT transaction_id, amount, category, date
            FROM transactions
            WHERE user_id = %s AND type = 'income'
            ORDER BY date DESC, transaction_id DESC
            """,
            (int(user_id),)
        )

        records = cursor.fetchall()

        return jsonify({
            "user_id": int(user_id),
            "income": [
                {
                    "id": row["transaction_id"],
                    "amount": float(row["amount"]),
                    "source": row["category"],
                    "income_date": (
                        row["date"].isoformat()
                        if row["date"] else None
                    )
                }
                for row in records
            ]
        }), 200

    except Error:
        return jsonify({
            "message": "Database operation failed"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
