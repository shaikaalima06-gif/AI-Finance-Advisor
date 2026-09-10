INSERT INTO users (name, email, password_hash) VALUES
('Priya', 'priya@example.com', 'hashed_pw_1'),
('Rupa', 'rupa@example.com', 'hashed_pw_2');

INSERT INTO transactions (user_id, amount, category, type, date) VALUES
(1, 25000.00, 'Salary', 'income', '2026-09-01'),
(1, 3500.00, 'Groceries', 'expense', '2026-09-03'),
(2, 30000.00, 'Salary', 'income', '2026-09-01');

INSERT INTO goals (user_id, goal_name, target_amount, current_amount, target_date) VALUES
(1, 'Laptop', 60000.00, 15000.00, '2026-12-31'),
(2, 'Emergency Fund', 100000.00, 20000.00, '2027-03-31');

INSERT INTO daily_savings (user_id, goal_id, amount, date) VALUES
(1, 1, 100.00, '2026-09-09'),
(1, 1, 150.00, '2026-09-10'),
(2, 2, 500.00, '2026-09-09');