
from datetime import date
from database.daily_savings import add_daily_saving

USER_ID = 3
TEST_GOAL_ID = 11

for amount in [0, -100]:
    try:
        add_daily_saving(
            user_id=USER_ID,
            goal_id=TEST_GOAL_ID,
            amount=amount,
            saving_date=date.today(),
        )
        print(f"FAIL: Invalid amount {amount} was accepted.")

    except (ValueError, TypeError) as error:
        print(f"PASS: Amount {amount} rejected: {error}")

    except Exception as error:
        print(
            f"CHECK: Amount {amount}: "
            f"{type(error).__name__}: {error}"
        )
