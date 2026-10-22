from decimal import Decimal
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.daily_savings import (
    add_daily_saving,
    get_savings_history,
    get_total_savings,
)

savings = Blueprint("savings", __name__)


@savings.route("/savings", methods=["POST"])
@jwt_required()
def add_saving():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    amount = data.get("amount")
    goal_id = data.get("goal_id")
    saving_date = data.get("saving_date") or data.get("date")

    if amount is None or goal_id is None:
        return jsonify({
            "message": "Amount and goal_id are required"
        }), 400

    try:
        amount = Decimal(str(amount))
        if not amount.is_finite() or amount <= 0:
            raise ValueError()
        if amount.as_tuple().exponent < -2:
            raise ValueError()

        goal_id = int(goal_id)
        if goal_id <= 0:
            raise ValueError()

        saving_date = date.fromisoformat(str(saving_date))
    except (InvalidOperation, TypeError, ValueError):
        return jsonify({
            "message": (
                "Provide a positive amount with at most 2 decimal places, "
                "a valid goal_id, and a date in YYYY-MM-DD format"
            )
        }), 400

    try:
        saving_id = add_daily_saving(
            user_id, goal_id, amount, saving_date
        )

        return jsonify({
            "message": "Savings added successfully",
            "saving_id": saving_id
        }), 201

    except Exception as e:
        message = str(e).lower()

        if "goal" in message and (
            "not found" in message or "not belong" in message
        ):
            return jsonify({
                "message": "Goal not found for this user"
            }), 404

        if "exceed" in message or "target" in message:
            return jsonify({
                "message": "Saving exceeds the goal's remaining target"
            }), 400

        return jsonify({
            "message": "Could not add saving"
        }), 500



@savings.route("/savings", methods=["GET"])
@jwt_required()
def get_savings():
    user_id = int(get_jwt_identity())
    goal_id = request.args.get("goal_id", type=int)

    try:
        records = get_savings_history(user_id, goal_id)

        savings_records = []
        for row in records:
            savings_records.append({
                key: (
                    float(value)
                    if isinstance(value, Decimal)
                    else value.isoformat()
                    if hasattr(value, "isoformat")
                    else value
                )
                for key, value in row.items()
            })

        return jsonify({
            "user_id": user_id,
            "savings": savings_records
        }), 200

    except Exception:
        return jsonify({
            "message": "Could not retrieve savings"
        }), 500



@savings.route("/savings/total", methods=["GET"])
@jwt_required()
def get_savings_total():
    user_id = int(get_jwt_identity())

    try:
        total = get_total_savings(user_id)
        return jsonify({
            "user_id": user_id,
            "total_savings": float(total)
        }), 200

    except Exception:
        return jsonify({
            "message": "Could not retrieve savings total"
        }), 500
