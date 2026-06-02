from flask import Flask, request, jsonify, render_template_string
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Database connection configuration
db_config = {
    'user': 'root',
    'password': '12345',
    'host': 'localhost',
    'database': 'queue_management'
}

# Function to get queue data from the database
def get_queue_data_from_db():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT office, currently_serving, next_serving FROM queue_system")
        rows = cursor.fetchall()
        print("Fetched rows:", rows)  # Debugging output
        cursor.close()
        connection.close()
        
        queue_data = {}
        for row in rows:
            queue_data[row['office']] = {
                'current': row['currently_serving'],
                'next': row['next_serving']
            }
        print("Formatted queue data:", queue_data)  # Debugging output
        return queue_data
    except Error as e:
        print(f"Error: {e}")
        return {}

# Function to update queue data in the database
def update_queue_data_in_db(office, current, next_ticket):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE students 
            SET currently_serving = %s, next_serving = %s 
            WHERE office = %s  # Updated table name
        """, (current, next_ticket, office))
        connection.commit()
        cursor.close()
        connection.close()
    except Error as e:
        print(f"Error: {e}")

# HTML template with inline CSS & JS, using Jinja2 for initial values
dashboard_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PGPC Queue Monitoring Dashboard</title>
  <style>
   :root {
      --dark-blue: #142d70;
      --light-beige: #e1cb81;
      --muted-blue: #64728c;
      --olive-green: #8a733d;
      --light-gray: #fbfbf9;
      --serving-color: #d4edda; /* Light green for currently serving */
      --next-color: #fff3cd; /* Light yellow for next in line */
      --default-color: white; /* Default background */
    }
    body, html {
      margin: 0;
      height: 100vh;
      background: var(--light-gray);
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      color: var(--dark-blue);
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .container {
      background: var(--light-beige);
      width: 95vw;
      max-width: 1200px;
      border-radius: 16px;
      padding: 30px;
      box-shadow: 0 8px 30px rgba(20, 45, 112, 0.35);
    }
    h1 {
      text-align: center;
      font-weight: 900;
      font-size: 2.5rem;
      color: var(--dark-blue);
      margin-bottom: 20px;
      user-select: none;
    }
    table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0 20px;
      font-size: 1.5rem;
    }
    thead {
      background: var(--olive-green);
      color: #fff;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }
    thead th {
      padding: 15px;
      text-align: center;
    }
    tbody tr {
      background: var(--default-color);
      border-radius: 12px;
      box-shadow: 0 10px 22px rgba(20, 45, 112, 0.15);
      transition: background-color 0.3s;
    }
    tbody tr.serving {
      background-color: var(--serving-color);
    }
    tbody tr.next {
      background-color: var(--next-color);
    }
    tbody td {
      padding: 15px;
      text-align: center;
      border-radius: 12px;
      user-select: text;
    }
    .dept-office {
      font-weight: 700;
      color: var(--muted-blue);
    }
    .ticket-number {
      font-family: 'Courier New', Courier, monospace;
      font-weight: 900;
      font-size: 2rem;
      color: var(--olive-green);
      letter-spacing: 0.15em;
      user-select: text;
    }
    footer {
      text-align: center;
      margin-top: 30px;
      font-size: 1rem;
      color: var(--dark-blue);
      user-select: none;
    }
    @media (max-width: 720px) {
      h1 {
        font-size: 2rem;
      }
      table {
        font-size: 1.2rem;
      }
      .ticket-number {
        font-size: 1.5rem;
      }
      .dept-office {
        font-size: 1.1rem;
      }
    }
  </style>
</head>
<body>
  <div class="container" role="main" aria-label="PGPC Queue Monitoring Dashboard">
    <h1>PGPC Queue Monitoring Dashboard</h1>
    <table aria-describedby="desc">
      <caption id="desc" style="display:none;">Shows live queue tickets currently being served and next in line per office</caption>
      <thead>
        <tr>
          <th>Office</th>
          <th>Currently Serving</th>
          <th>Next in Line</th>
        </tr>
      </thead>
      <tbody>
        {% for office, data in queue_data.items() %}
        <tr>
          <td class="dept-office">{{ office }}</td>
          <td class="ticket-number" id="serving-{{ office }}">{{ data.current }}</td>
          <td class="ticket-number" id="next-{{ office }}">{{ data.next }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    <footer>PGPC Queue Management System - Queue Monitor</footer>
  </div>
  <script>
    // JavaScript code omitted for brevity
  </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    queue_data = get_queue_data_from_db()
    print("QUEUE DATA:", queue_data)  # Debug
    return render_template_string(dashboard_template, queue_data=queue_data)


@app.route('/queue_data', methods=['GET'])
def get_queue_data():
    queue_data = get_queue_data_from_db()
    return jsonify(queue_data)

@app.route('/update_queue', methods=['POST'])
def update_queue():
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Missing JSON"), 400

    office = data.get('office')
    current = data.get('current')
    next_ticket = data.get('next')

    if office and current is not None and next_ticket is not None:
        update_queue_data_in_db(office, current, next_ticket)
        return jsonify(success=True, message=f"Queue updated for {office}")
    return jsonify(success=False, message="Invalid data or office"), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
