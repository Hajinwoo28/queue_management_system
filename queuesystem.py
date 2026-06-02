from flask import Flask, redirect, url_for, request, flash
from flask_mysqldb import MySQL
import MySQLdb
import logging

app = Flask(__name__)
app.secret_key = 'replace_with_a_secure_secret_key'

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'  # Change if your MySQL server is on a different host
app.config['MYSQL_USER'] = 'root'  # Replace with your MySQL username
app.config['MYSQL_PASSWORD'] = '12345'  # Replace with your MySQL password
app.config['MYSQL_DB'] = 'queue_management'

mysql = MySQL(app)

DEPARTMENTS = {
    'cashier': 'Cashier',
    'registrar': 'Registrar'
}

DEPT_PREFIXES = {
    'cashier': 'C',
    'registrar': 'R'
}

base_css = """
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(to bottom, #4CAF50, #3498db);
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      color: white;
      margin: 0;
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      padding: 20px;
      position: relative;
      z-index: 0;
    }
    body::before {
      content: "";
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.5);
      z-index: -1;
    }
    h1, h2 {
      text-align: center;
      margin-bottom: 1rem;
      text-shadow: 1px 1px 4px rgba(0,0,0,0.7);
    }
    .button-container {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 20px;
      margin-top: 20px;
    }
    .btn {
      background: rgba(255,255,255,0.15);
      border: none;
      border-radius: 12px;
      padding: 14px 40px;
      color: white;
      font-size: 1.4rem;
      cursor: pointer;
      transition: background 0.3s ease, transform 0.2s ease;
      box-shadow: 0 8px 20px rgba(0,0,0,0.3);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1.1px;
      text-decoration: none;
      display: inline-block;
      text-align: center;
    }
    .btn:hover {
      background: #ffffffcc;
      color: #2c3e50;
      transform: scale(1.05);
      box-shadow: 0 10px 30px rgba(255,255,255,0.8);
      text-decoration: none;
    }
    .number-display {
      font-size: 10rem;
      font-weight: 900;
      letter-spacing: 12px;
      margin-top: 20px;
      color: #fff;
      text-shadow: 0 0 15px #fff, 0 0 30px #7b2ff7bb;
    }
    .footer {
      position: fixed;
      bottom: 10px;
      font-size: 0.9rem;
      color: #ddd;
      user-select: none;
      text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }
    a {
      color: #ffccffcc;
      text-decoration: none;
      font-weight: bold;
    }
    a:hover {
      text-decoration: underline;
      color: #fff;
    }
    form {
      margin-top: 30px;
      text-align: center;
    }
    #refreshCount {
      font-weight: 700;
      font-size: 1.3rem;
    }
    input[type="text"] {
      padding: 10px;
      font-size: 1rem;
      margin: 10px;
      border-radius: 8px;
      border: none;
      width: 250px;
      max-width: 90vw;
    }
  </style>
"""

@app.route('/')
def welcome():
    app.logger.debug("Serving welcome page")
    html = f"""
    <html><head><title>Welcome to Queue Management System</title>{base_css}</head><body>
      <h1>Welcome to PGPC Queue System</h1>
      <p style="text-align:center;font-size:1.3rem; max-width:450px; text-shadow: 1px 1px 3px rgba(0,0,0,0.7);">
        Got a Transaction?
      </p>
      <div style="text-align:center; margin-top:40px;">
        <a href="{url_for('select_department')}" class="btn">GET STARTED</a>
      </div>
      <div class="footer">Queue Management System &copy; 2025</div>
    </body></html>
    """
    return html

@app.route('/select')
def select_department():
    app.logger.debug("Serving select_department page with buttons")
    buttons_html = ""
    for key, name in DEPARTMENTS.items():
        link = url_for('get_number', department=key)
        buttons_html += f'<a href="{link}" class="btn">{name}</a>'
    html = f"""
    <html><head><title>Select Department</title>{base_css}</head><body>
      <h2>Select Your Department</h2>
      <div class="button-container">
        {buttons_html}
      </div>
      <div class="footer">Queue Management System &copy; 2025</div>
    </body></html>
    """
    return html

@app.route('/get_number/<department>')
def get_number(department):
    app.logger.debug(f"Request to get_number for department: {department}")
    department = department.lower()
    if department not in DEPARTMENTS:
        app.logger.warning(f"Attempted access to unknown department: {department}")
        return redirect(url_for('select_department'))
    
    cur = mysql.connection.cursor()
    try:
        # We treat 'currently_serving' as last issued number (queue number for last user)
        cur.execute("SELECT currently_serving FROM students WHERE office = %s", (department,))
        row = cur.fetchone()

        if row:
            last_issued = row[0]
            number = last_issued + 1
            cur.execute("UPDATE students SET currently_serving = %s WHERE office = %s", (number, department))
            app.logger.debug(f"Updated currently_serving to {number} for {department}")
        else:
            number = 1
            cur.execute("INSERT INTO students (office, currently_serving) VALUES (%s, %s)", (department, number))
            app.logger.debug(f"Inserted new currently_serving {number} for {department}")

        mysql.connection.commit()
    except MySQLdb.Error as e:
        app.logger.error(f"MySQL error: {e}")
        return f"<h1>Database error: {e}</h1><p>Please contact the administrator.</p>", 500
    finally:
        cur.close()

    return redirect(url_for('acquire_number', department=department, number=number))  

@app.route('/acquire_number/<department>/<int:number>', methods=['GET', 'POST'])
def acquire_number(department, number):
    app.logger.debug(f"Serving acquire_number page for {department}, number {number}")
    if department not in DEPARTMENTS:
        return redirect(url_for('select_department'))
    display_dept = DEPARTMENTS[department]
    prefix = DEPT_PREFIXES.get(department, '')
    display_number = f"{prefix}{number:03d}"

    if request.method == 'POST':
        return redirect(url_for('show_number', department=department, number=number))

    html = f"""
    <html><head><title>Acquire Your Number</title>{base_css}</head><body>
      <h2>{display_dept} - Acquire Your Queue Number</h2>
      <div class="number-display">{display_number}</div>
      <p style="text-align:center; font-size:1.1rem; margin-top: 15px; text-shadow: 2px 2px 8px rgba(0,0,0,0.8);">
        Please confirm to proceed.
      </p>
      <form method="post" style="text-align:center;">
        <button type="submit" class="btn">Confirm</button>
      </form>
      <div class="footer">Queue Management System &copy; 2025</div>
    </body></html>
    """
    return html

@app.route('/show_number/<department>/<int:number>')
def show_number(department, number):
    if department not in DEPARTMENTS:
        return redirect(url_for('select_department'))
    display_dept = DEPARTMENTS[department]
    prefix = DEPT_PREFIXES.get(department, '')
    display_number = f"{prefix}{number:03d}"

    html = f"""
    <html><head><title>Your Queue Number</title>{base_css}</head><body>
      <h2>{display_dept} - Your Queue Number</h2>
      <div class="number-display">{display_number}</div>
      <div style="text-align:center; margin-top: 15px; font-size: 1.1rem; text-shadow: 2px 2px 8px rgba(0,0,0,0.8);">
        Please wait for your number to be called.
      </div>
      <div class="button-container" style="justify-content:center; margin-top: 30px;">
        <a href="{url_for('select_department')}" class="btn">Get Another Number</a>
        <a href="{url_for('waiting_area')}" class="btn">Done</a>
      </div>
      <div class="footer">Queue Management System &copy; 2025</div>
    </body></html>
    """
    return html

@app.route('/waiting_area')
def waiting_area():
    html = f"""
    <html><head><title>Waiting Area</title>{base_css}
      <script>
        let count = 5;
        function countdown() {{
          const countElem = document.getElementById('refreshCount');
          if (count > 0) {{
            countElem.textContent = count;
            count--;
            setTimeout(countdown, 1000);
          }} else {{
            window.location.href = '{url_for('welcome')}';
          }}
        }}
        window.onload = countdown;
      </script>
    </head><body>
      <h2>Waiting Area</h2>
      <p style="text-align:center; font-size:1.5rem; max-width:600px; margin-top: 40px; text-shadow: 2px 2px 8px rgba(0,0,0,0.8);">
        Please wait for your turn, Proceed to the waiting area.
      </p>
      <p style="text-align:center; font-size:1.2rem; margin-top: 20px; text-shadow: 2px 2px 8px rgba(0,0,0,0.8);">
        Refreshing in <span id="refreshCount">5</span> seconds...
      </p>
      <div class="footer">Queue Management System &copy; 2025</div>
    </body></html>
    """
    return html

@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        new_department = request.form['department_name'].strip().lower()
        if new_department and new_department not in DEPARTMENTS:
            DEPARTMENTS[new_department] = new_department.capitalize()
            DEPT_PREFIXES[new_department] = new_department[0].upper()
            cur = mysql.connection.cursor()
            try:
                cur.execute("INSERT INTO departments (name) VALUES (%s)", (new_department,))
                mysql.connection.commit()
                app.logger.debug(f"Added new department: {new_department}")
            except MySQLdb.Error as e:
                app.logger.error(f"MySQL error while adding department: {e}")
                return f"<h1>Database error: {e}</h1><p>Please contact the administrator.</p>", 500
            finally:
                cur.close()
            return redirect(url_for('select_department'))
        else:
            flash("Department already exists or invalid input.")
            return redirect(url_for('add_department'))

    html = f"""
    <html><head><title>Add Department</title>{base_css}</head><body>
      <h2>Add a New Department</h2>
      <form method="post">
        <input type="text" name="department_name" placeholder="Department Name" required>
        <button type="submit" class="btn">Add Department</button>
      </form>
      <div class="footer">Queue Management System &copy; 2025</div>
    </body></html>
    """
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

