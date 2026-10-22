
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from mysql.connector import Error

from db import get_db_connection

expenses = Blueprint("expenses", __name__)


@expenses.route("/expenses", methods=["POST"])
@jwt_required()
def add_expense():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    amount = data.get("amount")
    category = data.get("category")
    description = data.get("description")
    expense_date = data.get("expense_date") or data.get("date")

    if amount is None or not isinstance(category, str) or not category.strip():
        return jsonify({
            "message": "Amount and category are required"
        }), 400

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

    try:
        expense_date = date.fromisoformat(str(expense_date))
    except (TypeError, ValueError):
        return jsonify({
            "message": "A valid expense_date is required (YYYY-MM-DD)"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # The existing transactions table has no description column.
        # Store the expense category in the category column.
        cursor.execute(
            """
            INSERT INTO transactions (user_id, amount, category, type, date)
            VALUES (%s, %s, %s, 'expense', %s)
            """,
            (int(user_id), amount, category.strip(), expense_date)
        )

        transaction_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "message": "Expense added successfully",
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


@expenses.route("/expenses", methods=["GET"])
@jwt_required()
def get_expenses():
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
            WHERE user_id = %s AND type = 'expense'
            ORDER BY date DESC, transaction_id DESC
            """,
            (int(user_id),)
        )

        records = cursor.fetchall()

        return jsonify({
            "user_id": int(user_id),
            "expenses": [
                {
                    "id": row["transaction_id"],
                    "amount": float(row["amount"]),
                    "category": row["category"],
                    "expense_date": (
                        row["date"].isoformat() if row["date"] else None
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
