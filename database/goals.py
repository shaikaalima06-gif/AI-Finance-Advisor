from connection import get_connection


def create_goal(user_id, goal_name, target_amount, target_date):
    """Creates a new goal for a user. current_amount starts at 0."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO goals (user_id, goal_name, target_amount, current_amount, target_date)
        VALUES (%s, %s, %s, 0, %s)
    """
    cursor.execute(query, (user_id, goal_name, target_amount, target_date))
    conn.commit()
    new_goal_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return new_goal_id


def get_user_goals(user_id):
    """Returns all goals for a user, including calculated remaining amount and progress %."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM goals WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    goals = cursor.fetchall()
    cursor.close()
    conn.close()

    for goal in goals:
        goal["remaining_amount"] = float(goal["target_amount"]) - float(goal["current_amount"])
        goal["progress_percent"] = round(
            (float(goal["current_amount"]) / float(goal["target_amount"])) * 100, 2
        ) if float(goal["target_amount"]) > 0 else 0

    return goals


def get_goal_by_id(goal_id):
    """Returns a single goal with remaining amount and progress %."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM goals WHERE goal_id = %s"
    cursor.execute(query, (goal_id,))
    goal = cursor.fetchone()
    cursor.close()
    conn.close()

    if goal:
        goal["remaining_amount"] = float(goal["target_amount"]) - float(goal["current_amount"])
        goal["progress_percent"] = round(
            (float(goal["current_amount"]) / float(goal["target_amount"])) * 100, 2
        ) if float(goal["target_amount"]) > 0 else 0

    return goal


def add_money_to_goal(goal_id, amount):
    """Adds money toward a goal's current_amount. Does not let it exceed target."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        UPDATE goals
        SET current_amount = LEAST(current_amount + %s, target_amount)
        WHERE goal_id = %s
    """
    cursor.execute(query, (amount, goal_id))
    conn.commit()
    cursor.close()
    conn.close()


def update_goal(goal_id, goal_name=None, target_amount=None, target_date=None):
    """Updates only the fields that are provided."""
    conn = get_connection()
    cursor = conn.cursor()

    fields = []
    values = []
    if goal_name is not None:
        fields.append("goal_name = %s")
        values.append(goal_name)
    if target_amount is not None:
        fields.append("target_amount = %s")
        values.append(target_amount)
    if target_date is not None:
        fields.append("target_date = %s")
        values.append(target_date)

    if not fields:
        cursor.close()
        conn.close()
        return

    values.append(goal_id)
    query = f"UPDATE goals SET {', '.join(fields)} WHERE goal_id = %s"
    cursor.execute(query, tuple(values))
    conn.commit()
    cursor.close()
    conn.close()


def delete_goal(goal_id):
    """Deletes a goal. Related daily_savings rows are removed too (ON DELETE CASCADE)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM goals WHERE goal_id = %s", (goal_id,))
    conn.commit()
    cursor.close()
    conn.close()