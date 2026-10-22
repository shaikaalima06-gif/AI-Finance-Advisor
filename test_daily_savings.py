
from datetime import date
from database.daily_savings import (
    add_daily_saving,
    get_savings_history,
    get_total_savings,
)

USER_ID = 3
TEST_GOAL_ID = 11  # Replace 8 with the actual ID from Step 1

try:
    saving_id = add_daily_saving(
        user_id=USER_ID,
        goal_id=TEST_GOAL_ID,
        amount=500,
        saving_date=date.today(),
    )

    print("PASS: Saving recorded. Saving ID:", saving_id)

    history = get_savings_history(USER_ID, TEST_GOAL_ID)
    print("Savings history:", history)

    total = get_total_savings(USER_ID, TEST_GOAL_ID)
    print("Total savings:", total)

except Exception as error:
    print("TEST FAILED:", type(error).__name__, error)
