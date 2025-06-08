from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse, urljoin

app = Flask(__name__)
app.secret_key = 'R123ober456t'  # Change this to a strong secret key in production

def is_safe_url(target):
    """Ensure redirect URL is safe to avoid open redirects."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https') and
            ref_url.netloc == test_url.netloc)

def get_yesterdays_expense_tip(user_id):
    conn = sqlite3.connect('data/zamani.db')
    c = conn.cursor()

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    c.execute("""
        SELECT category, SUM(amount) FROM expenses
        WHERE date = ? AND user_id = ?
        GROUP BY category
    """, (yesterday, user_id))
    data = c.fetchall()
    conn.close()

    if not data:
        return "No spending recorded yesterday. Great job staying mindful! 🧘🏽‍♂️"

    top_category, top_amount = max(data, key=lambda x: x[1])
    return f"You spent Ksh {top_amount} on {top_category} yesterday. Try cutting back tomorrow for balance! 💡"

@app.route("/")
def home():
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.path))

    user_id = session['user_id']

    conn = sqlite3.connect('data/zamani.db')
    c = conn.cursor()
    c.execute("""
        SELECT amount, category, note, date FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC LIMIT 10
    """, (user_id,))
    expenses = c.fetchall()
    conn.close()

    tip = get_yesterdays_expense_tip(user_id)
    return render_template("index.html", expenses=expenses, tip=tip)

@app.route("/add", methods=["POST"])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.path))

    amount = request.form.get("amount")
    category = request.form.get("category")
    note = request.form.get("note")
    date = request.form.get("date")
    user_id = session['user_id']

    if not amount or not category or not date:
        return "Missing data, please fill all required fields.", 400

    conn = sqlite3.connect('data/zamani.db')
    c = conn.cursor()
    c.execute("INSERT INTO expenses (amount, category, note, date, user_id) VALUES (?, ?, ?, ?, ?)",
              (amount, category, note, date, user_id))
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/weekly")
def weekly_overview():
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.path))

    user_id = session['user_id']

    conn = sqlite3.connect('data/zamani.db')
    c = conn.cursor()

    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    c.execute("""
        SELECT date, SUM(amount) FROM expenses
        WHERE date >= ? AND user_id = ?
        GROUP BY date
    """, (seven_days_ago, user_id))
    daily_data = c.fetchall()
    conn.close()

    total_spent = sum(row[1] for row in daily_data)
    no_spend_days = 7 - len(daily_data)
    suggested_goal = round(total_spent * 0.9)

    return render_template("weekly.html", total=total_spent, streak=no_spend_days, goal=suggested_goal)

@app.route("/zen")
def zen_mode():
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.path))
    return render_template("zen.html")

@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.path))

    user_id = session['user_id']

    conn = sqlite3.connect('data/zamani.db')
    c = conn.cursor()

    # Monthly totals
    c.execute("""
        SELECT strftime('%Y-%m', date) AS month, SUM(amount)
        FROM expenses
        WHERE user_id = ?
        GROUP BY month
        ORDER BY month
    """, (user_id,))
    monthly_data = c.fetchall()

    # Category totals
    c.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (user_id,))
    category_data = c.fetchall()

    # Top category in last 30 days
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    c.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE date >= ? AND user_id = ?
        GROUP BY category
        ORDER BY total DESC
        LIMIT 1
    """, (thirty_days_ago, user_id))
    top_category_row = c.fetchone()
    top_category = top_category_row[0] if top_category_row else "N/A"
    top_category_amount = top_category_row[1] if top_category_row else 0

    ai_tips = {
        "Groceries": "Consider planning meals and using shopping lists to avoid impulse buying.",
        "Transport": "Try carpooling or tracking fuel efficiency to cut down on transport costs.",
        "Entertainment": "Set a monthly cap for fun activities to avoid overspending.",
        "Bills": "Review subscription services and cancel unused ones to lower bills.",
        "Eating Out": "Limit eating out to once or twice a week to save money.",
        "Shopping": "Unsubscribe from promo emails to resist impulsive purchases.",
        "Health": "Track medical expenses and check for insurance coverage or discounts.",
    }

    tip = ai_tips.get(top_category, "Keep tracking your expenses to gain better insights!")

    conn.close()

    return render_template(
        "dashboard.html",
        monthly_data=monthly_data,
        category_data=category_data,
        top_category=top_category,
        top_category_amount=top_category_amount,
        ai_tip=tip
    )

@app.route("/smart-budget")
def smart_budget():
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.path))

    user_id = session['user_id']

    conn = sqlite3.connect('data/zamani.db')
    c = conn.cursor()

    two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    c.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE date >= ? AND user_id = ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (two_weeks_ago, user_id))
    data = c.fetchall()
    conn.close()

    total = sum(row[1] for row in data)
    suggestions = []

    for category, amount in data:
        percentage = (amount / total) * 100 if total > 0 else 0
        if percentage > 30:
            suggestions.append(f"🔻 You're spending {int(percentage)}% on {category}. Try reducing it slightly to balance your budget.")
        elif percentage < 10:
            suggestions.append(f"🔺 Your {category} spending is quite low. Is this accurate or being missed?")

    if not suggestions:
        suggestions.append("You're managing your budget well! 🧘🏾‍♀️")

    affirmation = "🌱 Small shifts create big changes. Keep budgeting mindfully."

    return render_template("smart_budget.html", suggestions=suggestions, affirmation=affirmation)

# --- Authentication routes ---

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            flash("Please enter username, email, and password.")
            return redirect(url_for('signup'))

        conn = sqlite3.connect('data/zamani.db')
        c = conn.cursor()

        # Optional: Check if username already exists
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        if c.fetchone():
            flash("Username already taken.")
            conn.close()
            return redirect(url_for('signup'))

        # Check if email already exists
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            flash("Email already registered.")
            conn.close()
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                  (username, email, hashed_password))
        conn.commit()
        conn.close()

        flash("Signup successful! Please login.")
        return redirect(url_for('login'))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_input = request.form.get("user_input")
        password = request.form.get("password")
        next_page = request.args.get("next")

        if not user_input or not password:
            flash("Please enter your username/email and password.")
            return redirect(url_for('login', next=next_page) if next_page else url_for('login'))

        conn = sqlite3.connect('data/zamani.db')
        c = conn.cursor()

        # Check both username and email
        c.execute("SELECT id, password FROM users WHERE username = ? OR email = ?", (user_input, user_input))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            flash("Login successful!")

            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash("Invalid credentials.")
            return redirect(url_for('login', next=next_page) if next_page else url_for('login'))

    else:
        next_page = request.args.get("next")
        return render_template("login.html", next=next_page)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.")
    return redirect(url_for('login'))

# --- Delete test data ---

@app.route("/delete-tests", methods=["POST"])
def delete_tests():
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.path))

    user_id = session['user_id']

    conn = sqlite3.connect('data/zamani.db')
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE category = 'test' AND user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("Test data deleted successfully.")
    return redirect(url_for('home'))
# --- API Route for fetching recent expenses ---

from flask import jsonify

@app.route("/api/expenses/recent")
def api_recent_expenses():
    if 'user_id' not in session:
        return jsonify({"error": "You must log in first"}), 401

    user_id = session['user_id']

    conn = sqlite3.connect('data/zamani.db')
    c = conn.cursor()
    c.execute("""
        SELECT amount, category, note, date 
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC LIMIT 10
    """, (user_id,))
    expenses = c.fetchall()
    conn.close()

    expenses_list = [
        {"amount": row[0], "category": row[1], "note": row[2], "date": row[3]}
        for row in expenses
    ]
    
    return jsonify(expenses_list)

# --- Run the app ---

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

