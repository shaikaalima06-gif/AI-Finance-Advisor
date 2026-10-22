
from datetime import date
from database.daily_savings import add_daily_saving

try:
    add_daily_saving(
        user_id=3,
        goal_id=11,
        amount=600,
        saving_date=date.today(),
    )
    print("CHECK: The function accepted the saving.")

except ValueError as error:
    print("PASS: Excessive saving rejected:", error)

except Exception as error:
    print("CHECK ERROR:", type(error).__name__, error)
