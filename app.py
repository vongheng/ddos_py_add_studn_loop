from flask import Flask, render_template_string, request, jsonify
import threading
import time
import requests
import random
from faker import Faker
import os

app = Flask(__name__)
fake = Faker()

# API endpoints
BASE_URL = "https://staging-student-score-d7vi.encr.app"
API_ADD = f"{BASE_URL}/addtostudent"

faculties = ["IT", "Business", "Engineering", "Web develop", "Design"]
genders = [
    "Male", "Female", "Transgender Male", "Transgender Female",
    "Non-Binary", "Genderqueer", "Genderfluid", "Agender",
    "Bigender", "Two-Spirit", "Intersex", "Other", "Prefer not to say"
]

logs = []
logs_lock = threading.Lock()

def log(message):
    with logs_lock:
        logs.append(message)
        if len(logs) > 200:
            logs.pop(0)

success_count = 0
failure_count = 0

def add_student():
    global success_count, failure_count
    student = {
        "fullname": fake.name(),
        "gender": random.choice(genders),
        "dob": fake.date_of_birth(minimum_age=17, maximum_age=24).strftime("%Y/%m/%d"),
        "faculty": random.choice(faculties)
    }
    try:
        res = requests.post(API_ADD, json=student)
        if res.status_code == 200:
            success_count += 1
            log(f"✅ Added: {student['fullname']}  (count {success_count})")
        else:
            failure_count += 1
            log(f"❌ Failed: {res.status_code} - {res.text}")
    except Exception as e:
        failure_count += 1
        log(f"❌ Error: {e}")

def add_students(n):
    log(f"🚀 Starting to add {n} students...")
    for i in range(1, n+1):
        add_student()
        time.sleep(0.1)
    log(f"✅ Finished adding {n} students. Success: {success_count}, Failures: {failure_count}")

@app.route("/", methods=["GET"])
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>🎓 Student API Hacker Console</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

  body {
    background: #0f0f0f;
    color: #00ff00;
    font-family: 'Share Tech Mono', monospace;
    margin: 0; padding: 20px;
    user-select: none;
  }

  h2 {
    text-align: center;
    letter-spacing: 2px;
    text-shadow:
      0 0 5px #00ff00,
      0 0 10px #00ff00,
      0 0 20px #00ff00,
      0 0 40px #0f0;
  }

  form {
    text-align: center;
    margin-bottom: 20px;
  }

  input[type=number] {
    width: 80px;
    background: #111;
    border: 1px solid #00ff00;
    color: #00ff00;
    padding: 5px 10px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.2rem;
    outline: none;
    border-radius: 3px;
  }

  input[type=number]:focus {
    box-shadow: 0 0 10px #00ff00;
  }

  button {
    background: #000;
    border: 1px solid #00ff00;
    color: #00ff00;
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.2rem;
    padding: 5px 15px;
    cursor: pointer;
    border-radius: 3px;
    margin-left: 10px;
    transition: 0.3s ease;
  }

  button:hover {
    background: #00ff00;
    color: #000;
    box-shadow:
      0 0 5px #00ff00,
      0 0 20px #00ff00;
  }

  #console {
    background: #000;
    border: 2px solid #00ff00;
    padding: 15px;
    height: 400px;
    overflow-y: scroll;
    white-space: pre-wrap;
    font-size: 1rem;
    line-height: 1.4;
    box-shadow:
      inset 0 0 10px #00ff00,
      0 0 20px #00ff00;
    position: relative;
  }

  /* Blinking cursor effect */
  #console::after {
    content: '|';
    position: absolute;
    bottom: 15px;
    left: 15px;
    color: #00ff00;
    animation: blink 1s steps(2, start) infinite;
    font-weight: bold;
  }

  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
</style>
</head>
<body>

<h2>🎓 Student API Hacker Console</h2>

<form id="runForm">
  <label for="count">Add how many students?</label>
  <input type="number" id="count" name="count" min="1" max="1000" value="10" required />
  <button type="submit">🚀 Start Adding</button>
</form>

<div id="console"></div>

<script>
const consoleDiv = document.getElementById('console');
const runForm = document.getElementById('runForm');

function escapeHtml(text) {
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

async function fetchLogs() {
  try {
    const res = await fetch('/log');
    if (res.ok) {
      const data = await res.json();
      consoleDiv.innerHTML = data.logs.map(escapeHtml).join('\\n');
      consoleDiv.scrollTop = consoleDiv.scrollHeight;
    }
  } catch(e) {
    consoleDiv.innerHTML += `\\n❌ Error fetching logs: ${e}`;
  }
}

runForm.onsubmit = async (e) => {
  e.preventDefault();
  const count = document.getElementById('count').value;
  try {
    await fetch('/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: `count=${encodeURIComponent(count)}`
    });
  } catch (e) {
    alert('Failed to start adding students: ' + e);
  }
}

setInterval(fetchLogs, 1000);
fetchLogs();
</script>

</body>
</html>
    """)

@app.route("/run", methods=["POST"])
def run():
    count = int(request.form.get("count", 10))
    threading.Thread(target=add_students, args=(count,), daemon=True).start()
    return "", 204

@app.route("/log", methods=["GET"])
def get_log():
    with logs_lock:
        return jsonify(logs=logs)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Get PORT from environment or default to 5000
    app.run(host="0.0.0.0", port=port, debug=True)
