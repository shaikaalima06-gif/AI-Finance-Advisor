from datetime import datetime


def calculate_savings_plan(
        target_amount,
        current_amount,
        deadline
):

    # Convert deadline string to date
    deadline_date = datetime.strptime(
        str(deadline),
        "%Y-%m-%d"
    )

    today = datetime.today()

    # Calculate remaining days
    remaining_days = (
        deadline_date - today
    ).days


    # Remaining money required
    remaining_amount = (
        target_amount - current_amount
    )


    # If goal already achieved
    if remaining_amount <= 0:

        return {
            "status": "Goal Achieved",
            "remaining_amount": 0,
            "daily_saving": 0,
            "weekly_saving": 0,
            "monthly_saving": 0
        }


    # If deadline passed
    if remaining_days <= 0:

        return {
            "status": "Deadline Passed",
            "remaining_amount": remaining_amount,
            "daily_saving": 0,
            "weekly_saving": 0,
            "monthly_saving": 0
        }


    # Calculate saving targets
    daily_saving = remaining_amount / remaining_days

    weekly_saving = daily_saving * 7

    monthly_saving = daily_saving * 30


    return {

        "status": "Active Goal",

        "remaining_amount":
        round(remaining_amount, 2),

        "remaining_days":
        remaining_days,

        "daily_saving":
        round(daily_saving, 2),

        "weekly_saving":
        round(weekly_saving, 2),

        "monthly_saving":
        round(monthly_saving, 2)

    }