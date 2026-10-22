
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from mysql.connector import Error

from db import get_db_connection

goals = Blueprint("goals", __name__)


@goals.route("/goals", methods=["POST"])
@jwt_required()
def add_goal():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    goal_name = data.get("goal_name")
    target_amount = data.get("target_amount")
    target_date = data.get("target_date")

    if (
        not isinstance(goal_name, str)
        or not goal_name.strip()
        or target_amount is None
        or not target_date
    ):
        return jsonify({
            "message": "Goal name, target amount and target date are required"
        }), 400

    try:
        target_amount = Decimal(str(target_amount))
        if not target_amount.is_finite() or target_amount <= 0:
            raise ValueError()
        if target_amount.as_tuple().exponent < -2:
            raise ValueError()
        target_date = date.fromisoformat(str(target_date))
    except (InvalidOperation, TypeError, ValueError):
        return jsonify({
            "message": "Provide a positive target amount with at most 2 decimal places and a date in YYYY-MM-DD format"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO goals
                (user_id, goal_name, target_amount, current_amount, target_date)
            VALUES (%s, %s, %s, 0, %s)
            """,
            (user_id, goal_name.strip(), target_amount, target_date)
        )

        goal_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "message": "Goal added successfully",
            "goal_id": goal_id
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


@goals.route("/goals", methods=["GET"])
@jwt_required()
def get_goals():
    user_id = int(get_jwt_identity())
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT goal_id, goal_name, target_amount,
                   current_amount, target_date, created_at
            FROM goals
            WHERE user_id = %s
            ORDER BY goal_id DESC
            """,
            (user_id,)
        )

        records = cursor.fetchall()

        result = []
        for row in records:
            result.append({
                "goal_id": row["goal_id"],
                "goal_name": row["goal_name"],
                "target_amount": float(row["target_amount"]),
                "current_amount": float(row["current_amount"]),
                "target_date": (
                    row["target_date"].isoformat()
                    if row["target_date"] else None
                ),
                "created_at": (
                    row["created_at"].isoformat()
                    if row["created_at"] else None
                )
            })

        return jsonify({
            "user_id": user_id,
            "goals": result
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


@goals.route("/goals/advisor", methods=["POST"])
@jwt_required()
def savings_advisor():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    try:
        target_amount = Decimal(str(data.get("target_amount", "")))
        current_savings = Decimal(str(data.get("current_savings", 0)))

        if (
            not target_amount.is_finite()
            or not current_savings.is_finite()
            or target_amount <= 0
            or current_savings < 0
        ):
            raise ValueError()

        target_date = date.fromisoformat(str(data.get("target_date", "")))

    except (InvalidOperation, TypeError, ValueError):
        return jsonify({
            "message": "Provide a positive target amount, non-negative current savings, and target date in YYYY-MM-DD format"
        }), 400

    days_remaining = (target_date - date.today()).days
    remaining_amount = max(target_amount - current_savings, Decimal("0"))

    daily_target = (
        remaining_amount / days_remaining
        if days_remaining > 0
        else remaining_amount
    )

    return jsonify({
        "message": "Savings advisor calculated",
        "user_id": user_id,
        "advisor": {
            "target_amount": float(target_amount),
            "current_savings": float(current_savings),
            "remaining_amount": round(float(remaining_amount), 2),
            "days_remaining": days_remaining,
            "daily_savings_target": round(float(daily_target), 2),
            "weekly_savings_target": round(float(daily_target * 7), 2)
        }
    }), 200
