#Step 1: models/goal_model.py

#This model handles all financial goal database operations.  from db_connection import get_db_connection


class GoalModel:

    # Create Goal
    @staticmethod
    def create_goal(user_id, goal_name, target_amount, current_amount, deadline):

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO goals
        (user_id, goal_name, target_amount, current_amount, deadline)
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(query, (
            user_id,
            goal_name,
            target_amount,
            current_amount,
            deadline
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return True


    # Get All Goals
    @staticmethod
    def get_goals(user_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT * FROM goals
        WHERE user_id = %s
        """

        cursor.execute(query, (user_id,))

        goals = cursor.fetchall()

        cursor.close()
        connection.close()

        return goals


    # Get Single Goal
    @staticmethod
    def get_goal_by_id(goal_id, user_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT * FROM goals
        WHERE goal_id = %s AND user_id = %s
        """

        cursor.execute(query, (goal_id, user_id))

        goal = cursor.fetchone()

        cursor.close()
        connection.close()

        return goal


    # Update Goal
    @staticmethod
    def update_goal(goal_id, user_id, goal_name,
                    target_amount, current_amount, deadline):

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        UPDATE goals
        SET goal_name = %s,
            target_amount = %s,
            current_amount = %s,
            deadline = %s
        WHERE goal_id = %s AND user_id = %s
        """

        cursor.execute(query, (
            goal_name,
            target_amount,
            current_amount,
            deadline,
            goal_id,
            user_id
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return True


    # Delete Goal
    @staticmethod
    def delete_goal(goal_id, user_id):

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        DELETE FROM goals
        WHERE goal_id = %s AND user_id = %s
        """

        cursor.execute(query, (goal_id, user_id))

        connection.commit()

        cursor.close()
        connection.close()

        return True