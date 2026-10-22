# Database Module — AI Finance Advisor

This folder contains the database schema, sample data, and Python modules for managing
users' financial goals and daily savings. Built by Member 4.

## Files

| File | Purpose |
|---|---|
| `schema.sql` | Creates all 4 tables (users, transactions, goals, daily_savings) |
| `seed.sql` | Inserts sample data for testing |
| `connection.py` | Reusable MySQL connection function, reads credentials from `.env` |
| `goals.py` | CRUD functions for managing financial goals |
| `daily_savings.py` | Functions for recording and tracking daily savings |

## Database Schema

**users** — stores account info
- `user_id` (PK), `name`, `email`, `password_hash`

**transactions** — income/expense records
- `transaction_id` (PK), `user_id` (FK → users), `amount`, `category`, `type` (income/expense), `date`

**goals** — financial goals a user is saving toward
- `goal_id` (PK), `user_id` (FK → users), `goal_name`, `target_amount`, `current_amount`, `target_date`, `created_at`

**daily_savings** — individual saving entries linked to a goal
- `saving_id` (PK), `user_id` (FK → users), `goal_id` (FK → goals), `amount`, `date`

**Relationships**
- One user → many transactions
- One user → many goals
- One goal → many daily savings entries
- Deleting a user or goal cascades and removes their related rows (`ON DELETE CASCADE`)

## Setup

1. Install dependencies: `pip install mysql-connector-python python-dotenv`
2. Create a `.env` file in the project root with:
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=ai_finance_advisor
   ```
3. Create the database and load the schema:
   ```
   mysql -u root -p -e "CREATE DATABASE ai_finance_advisor;"
   mysql -u root -p ai_finance_advisor < schema.sql
   mysql -u root -p ai_finance_advisor < seed.sql
   ```

## Available Functions

### `connection.py`
- `get_connection()` — returns a live MySQL connection using credentials from `.env`

### `goals.py`
- `create_goal(user_id, goal_name, target_amount, target_date)` — creates a new goal, returns its `goal_id`
- `get_user_goals(user_id)` — returns all goals for a user, each with calculated `remaining_amount` and `progress_percent`
- `get_goal_by_id(goal_id)` — returns a single goal with the same calculated fields
- `add_money_to_goal(goal_id, amount)` — adds to `current_amount`, capped at `target_amount`
- `update_goal(goal_id, goal_name=None, target_amount=None, target_date=None)` — updates only the fields provided
- `delete_goal(goal_id)` — deletes a goal and its linked savings entries (cascade)

### `daily_savings.py`
- `add_daily_saving(user_id, goal_id, amount, date)` — records a saving entry **and automatically updates the linked goal's `current_amount`**
- `get_savings_history(user_id, goal_id=None)` — returns saving entries for a user, optionally filtered to one goal
- `get_total_savings(user_id, goal_id=None)` — returns the sum of savings for a user, optionally for one goal
- `delete_saving(saving_id, goal_id, amount)` — deletes a saving entry and reverses the goal's `current_amount` accordingly

## Notes for Other Team Members

- **Backend (Member 2):** import functions directly from `goals.py` and `daily_savings.py` — no need to write raw SQL, everything returns plain dicts/values ready for JSON serialization in Flask routes.
- **AI/ML (Member 3):** `get_savings_history()` and `get_user_goals()` are the main sources of structured financial data for model input.
- **Frontend (Member 1):** goal objects include `remaining_amount` and `progress_percent` pre-calculated, so no need to compute these client-side.