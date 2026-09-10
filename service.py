Step 2: services/financial_analysis.py

# This is the main financial calculation module. 

def calculate_financial_analysis(
        total_income,
        total_expenses,
        total_loans
):

    # Avoid division by zero
    if total_income == 0:
        savings_rate = 0
        expense_ratio = 0
        dti_ratio = 0

    else:

        # Savings
        savings = total_income - total_expenses

        # Savings Rate
        savings_rate = (savings / total_income) * 100

        # Expense Ratio
        expense_ratio = (total_expenses / total_income) * 100

        # Debt To Income Ratio
        dti_ratio = (total_loans / total_income) * 100


    # Financial Health Score
    health_score = calculate_health_score(
        savings_rate,
        expense_ratio,
        dti_ratio
    )


    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "total_savings": round(total_income - total_expenses, 2),
        "savings_rate": round(savings_rate, 2),
        "expense_ratio": round(expense_ratio, 2),
        "debt_to_income_ratio": round(dti_ratio, 2),
        "financial_health_score": health_score
    }


def calculate_health_score(
        savings_rate,
        expense_ratio,
        dti_ratio
):

    score = 0


    # Savings Score
    if savings_rate >= 30:
        score += 40

    elif savings_rate >= 20:
        score += 30

    elif savings_rate >= 10:
        score += 20

    else:
        score += 10


    # Expense Score
    if expense_ratio <= 50:
        score += 30

    elif expense_ratio <= 70:
        score += 20

    else:
        score += 10


    # Debt Score
    if dti_ratio <= 20:
        score += 30

    elif dti_ratio <= 40:
        score += 20

    else:
        score += 10


    return score


def get_financial_health_status(score):

    if score >= 80:
        return "Excellent"

    elif score >= 60:
        return "Good"

    elif score >= 40:
        return "Average"

    else:
        return "Poor"