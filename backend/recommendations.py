
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from mysql.connector import Error

from db import get_db_connection

recommendations = Blueprint("recommendations", __name__)


def generate_recommendations(savings_rate, expense_ratio, dti):
    recommendations_list = []

    if savings_rate < 10:
        recommendations_list.append(
            "Increase your monthly savings and aim to save at least 10% of income."
        )
    elif savings_rate < 20:
        recommendations_list.append(
            "Your savings are progressing. Try to gradually increase your savings rate toward 20%."
        )
    else:
        recommendations_list.append(
            "Maintain your current savings habit."
        )

    if expense_ratio > 70:
        recommendations_list.append(
            "Review your expenses and reduce unnecessary spending."
        )

    if dti > 40:
        recommendations_list.append(
            "Consider reducing outstanding debt and monthly debt payments."
        )

    if not recommendations_list:
        recommendations_list.append(
            "Continue tracking your income, expenses, savings and financial goals."
        )

    return recommendations_list


@recommendations.route("/recommendations/test", methods=["GET"])
def test_recommendations():
    recommendations_list = generate_recommendations(
        savings_rate=10,
        expense_ratio=60,
        dti=20
    )

    return jsonify({
        "message": "Recommendations generated",
        "recommendations": recommendations_list
    }), 200


@recommendations.route("/recommendations", methods=["GET"])
@jwt_required()
def get_recommendations():
    user_id = get_jwt_identity()
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Income and expenses are stored in transactions.
        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN type = 'income'
                    THEN amount ELSE 0 END), 0) AS total_income,
                COALESCE(SUM(CASE WHEN type = 'expense'
                    THEN amount ELSE 0 END), 0) AS total_expenses
            FROM transactions
            WHERE user_id = %s
        """, (user_id,))
        transaction_row = cursor.fetchone()

        # Sum EMI payments from the user's loans.
        cursor.execute("""
            SELECT COALESCE(SUM(emi), 0) AS debt_payments
            FROM loans
            WHERE user_id = %s
        """, (user_id,))
        loan_row = cursor.fetchone()

        total_income = float(transaction_row["total_income"] or 0)
        total_expenses = float(transaction_row["total_expenses"] or 0)
        debt_payments = float(loan_row["debt_payments"] or 0)

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

        recommendations_list = generate_recommendations(
            savings_rate, expense_ratio, dti
        )

        return jsonify({
            "message": "Recommendations generated",
            "user_id": user_id,
            "financial_summary": {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "debt_payments": debt_payments,
                "monthly_savings": round(monthly_savings, 2),
                "savings_rate": round(savings_rate, 2),
                "expense_ratio": round(expense_ratio, 2),
                "dti": round(dti, 2)
            },
            "recommendations": recommendations_list
        }), 200

    except Error:
        return jsonify({
            "message": "Could not generate recommendations. Check the database connection and table schema."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
