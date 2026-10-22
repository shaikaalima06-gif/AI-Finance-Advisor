
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from mysql.connector import Error

from db import get_db_connection

analysis = Blueprint("analysis", __name__)


def calculate_financial_metrics(total_income, total_expenses, debt_payments):
    monthly_savings = total_income - total_expenses - debt_payments

    savings_rate = (
        monthly_savings / total_income * 100
        if total_income > 0 else 0
    )
    expense_ratio = (
        total_expenses / total_income * 100
        if total_income > 0 else 0
    )
    dti = (
        debt_payments / total_income * 100
        if total_income > 0 else 0
    )

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "debt_payments": round(debt_payments, 2),
        "monthly_savings": round(monthly_savings, 2),
        "savings_rate": round(savings_rate, 2),
        "expense_ratio": round(expense_ratio, 2),
        "dti": round(dti, 2)
    }


def classify_financial_health(savings_rate, dti, expense_ratio):
    if savings_rate >= 20 and dti <= 30 and expense_ratio <= 70:
        return "Healthy"
    if savings_rate >= 10 and dti <= 40 and expense_ratio <= 85:
        return "Moderate"
    return "Needs Improvement"


def get_user_analysis(user_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN type = 'income'
                    THEN amount ELSE 0 END), 0) AS total_income,
                COALESCE(SUM(CASE WHEN type = 'expense'
                    THEN amount ELSE 0 END), 0) AS total_expenses
            FROM transactions
            WHERE user_id = %s
        """, (user_id,))
        totals = cursor.fetchone()

        cursor.execute("""
            SELECT COALESCE(SUM(emi), 0) AS debt_payments
            FROM loans
            WHERE user_id = %s
        """, (user_id,))
        debt = cursor.fetchone()

        total_income = float(totals["total_income"] or 0)
        total_expenses = float(totals["total_expenses"] or 0)
        debt_payments = float(debt["debt_payments"] or 0)

        metrics = calculate_financial_metrics(
            total_income, total_expenses, debt_payments
        )
        health = classify_financial_health(
            metrics["savings_rate"],
            metrics["dti"],
            metrics["expense_ratio"]
        )

        return metrics, health

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@analysis.route("/analysis/test", methods=["GET"])
def test_analysis():
    metrics = calculate_financial_metrics(50000, 30000, 5000)
    health = classify_financial_health(
        metrics["savings_rate"], metrics["dti"], metrics["expense_ratio"]
    )
    return jsonify({
        "message": "Financial analysis working",
        "analysis": metrics,
        "financial_health": health
    }), 200


@analysis.route("/analysis/calculate", methods=["POST"])
@jwt_required()
def calculate_analysis():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    try:
        total_income = float(data.get("total_income", 0))
        total_expenses = float(data.get("total_expenses", 0))
        debt_payments = float(data.get("debt_payments", 0))

        if any(
            value < 0 or value != value or value == float("inf")
            or value == float("-inf")
            for value in (total_income, total_expenses, debt_payments)
        ):
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({"message": "Amounts must be valid non-negative numbers"}), 400

    metrics = calculate_financial_metrics(
        total_income, total_expenses, debt_payments
    )
    health = classify_financial_health(
        metrics["savings_rate"], metrics["dti"], metrics["expense_ratio"]
    )

    return jsonify({
        "message": "Financial analysis calculated",
        "user_id": user_id,
        "analysis": metrics,
        "financial_health": health
    }), 200


@analysis.route("/analysis", methods=["GET"])
@jwt_required()
def financial_analysis():
    user_id = get_jwt_identity()

    try:
        metrics, health = get_user_analysis(user_id)
        return jsonify({
            "message": "Financial analysis retrieved",
            "user_id": user_id,
            "analysis": metrics,
            "financial_health": health
        }), 200
    except Error:
        return jsonify({
            "message": "Could not retrieve financial analysis. Check database tables."
        }), 500
