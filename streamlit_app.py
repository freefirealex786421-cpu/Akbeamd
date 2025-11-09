from flask import Flask, request, render_template_string
import threading, requests, time, datetime

app = Flask(__name__)
app.debug = True

headers = {'User-Agent': 'Mozilla/5.0'}

runtime_data = {}
stop_flags = {}


def send_messages(access_token, thread_id, sender_name, time_interval, messages, task_id):
    start_time = datetime.datetime.now()
    runtime_data[task_id] = {
        "status": "RUNNING",
        "start_time": start_time,
        "fb_name": sender_name,
        "convo_uid": thread_id,
        "token": access_token[:40] + "...",
        "file": "Uploaded",
        "sent_count": 0
    }

    stop_flags[task_id] = False
    while not stop_flags.get(task_id, False):
        try:
            for msg in messages:
                if stop_flags.get(task_id, False):
                    break
                api_url = f"https://graph.facebook.com/v15.0/t_{thread_id}/"
                message = f"{sender_name}: {msg}"
                params = {'access_token': access_token, 'message': message}
                r = requests.post(api_url, data=params, headers=headers)
                runtime_data[task_id]["sent_count"] += 1
                print(f"[{task_id}] Sent: {message} (Status: {r.status_code})")
                time.sleep(time_interval)
        except Exception as e:
            print(f"[{task_id}] Error: {e}")
            time.sleep(5)
    runtime_data[task_id]["status"] = "STOPPED"
    print(f"[{task_id}] Task stopped.")


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # --- STOP OR CHECK PANEL ---
        if 'taskId' in request.form:
            task_id = request.form.get('taskId')
            action = request.form.get('action')
            if task_id not in runtime_data:
                return render_template_string(HTML_ERROR_PAGE, message="❌ Invalid Task ID!")

            if action == 'stop':
                stop_flags[task_id] = True
                runtime_data[task_id]["status"] = "STOPPED"
                return render_template_string(HTML_STOPPED_PAGE, task_id=task_id)

            if action == 'status':
                task = runtime_data[task_id]
                return render_template_string(HTML_STATUS_PAGE, **task, task_id=task_id)

        # --- START TASK ---
        access_token = request.form.get('accessToken')
        thread_id = request.form.get('threadId')
        sender_name = request.form.get('senderName')
        delay = int(request.form.get('delay'))
        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = f"TASK_{int(time.time())}"
        t = threading.Thread(target=send_messages, args=(access_token, thread_id, sender_name, delay, messages, task_id))
        t.start()

        fb_name = "Unknown"
        try:
            info = requests.get(f"https://graph.facebook.com/me?access_token={access_token}").json()
            fb_name = info.get("name", "Unknown")
        except:
            pass

        start_time = datetime.datetime.now().strftime("%d %b %Y - %I:%M:%S %p")
        runtime_data[task_id] = {
            "fb_name": fb_name,
            "convo_uid": thread_id,
            "token": access_token[:40] + "...",
            "file": txt_file.filename,
            "start_time": start_time,
            "status": "RUNNING",
            "sent_count": 0,
            "start_timestamp": time.time()
        }

        return render_template_string(HTML_STATUS_PAGE, **runtime_data[task_id], task_id=task_id)

    return HTML_FORM_PAGE


# 🌞 WHITE PANEL UI
HTML_FORM_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ALEX DARKSTAR PANEL</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: 'Poppins', sans-serif;
    background: #ffffff;
    color: #333;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
  .panel {
    background: #f9f9f9;
    border: 2px solid #007bff;
    border-radius: 15px;
    box-shadow: 0 0 20px #007bff33;
    padding: 25px;
    width: 100%;
    max-width: 420px;
    margin: 15px 0;
  }
  h2 {
    color: #007bff;
    text-align: center;
    margin-bottom: 15px;
  }
  input, button {
    width: 100%;
    padding: 12px;
    margin: 8px 0;
    border-radius: 8px;
    outline: none;
    font-size: 14px;
  }
  input {
    border: 1px solid #ccc;
  }
  input:focus {
    border-color: #007bff;
    box-shadow: 0 0 5px #007bff77;
  }
  button {
    border: none;
    font-weight: bold;
    text-transform: uppercase;
    color: #fff;
    cursor: pointer;
    transition: 0.3s;
  }
  .start-btn { background: linear-gradient(90deg, #00aaff, #0077ff); }
  .stop-btn { background: linear-gradient(90deg, #ff3355, #ff0000); }
  .status-btn { background: linear-gradient(90deg, #00c851, #007e33); }
  button:hover { transform: scale(1.03); }
  .footer {
    text-align: center;
    color: #777;
    font-size: 12px;
    margin-top: 10px;
  }
</style>
</head>
<body>
  <div class="panel">
    <h2>🚀 START MESSAGE TASK</h2>
    <form action="/" method="post" enctype="multipart/form-data">
      <input type="text" name="accessToken" placeholder="Facebook Access Token" required>
      <input type="text" name="threadId" placeholder="Convo / Group UID" required>
      <input type="text" name="senderName" placeholder="Sender Name" required>
      <input type="file" name="txtFile" accept=".txt" required>
      <input type="number" name="delay" placeholder="Delay (seconds)" required>
      <button type="submit" class="start-btn">Start Task</button>
    </form>
  </div>

  <div class="panel">
    <h2>🛑 STOP OR CHECK TASK</h2>
    <form action="/" method="post">
      <input type="text" name="taskId" placeholder="Enter Task ID" required>
      <button type="submit" name="action" value="stop" class="stop-btn">Stop Task</button>
      <button type="submit" name="action" value="status" class="status-btn">Check Status</button>
    </form>
  </div>

  <div class="footer">© 2025 ALEX DARKSTAR PANEL</div>
</body>
</html>
"""


# 🌞 STATUS PAGE (with uptime)
HTML_STATUS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Status - ALEX DARKSTAR</title>
<style>
  body {
    margin: 0;
    background: #fff;
    color: #222;
    font-family: 'Consolas', monospace;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
  }
  .status-box {
    background: #f8f8f8;
    padding: 25px 35px;
    border: 2px solid #007bff;
    border-radius: 15px;
    box-shadow: 0 0 25px #007bff33;
    width: 90%;
    max-width: 420px;
  }
  h3 {
    text-align: center;
    color: #0077ff;
    margin-bottom: 15px;
  }
  p { margin: 8px 0; }
  .green { color: #00aa55; }
  .yellow { color: #e6b800; }
  .pink { color: #ff3399; }
  .cyan { color: #0077ff; }
</style>
</head>
<body>
  <div class="status-box">
    <h3>⚡ TASK STATUS ⚡</h3>
    <p>🆔 TASK ID ➜ <span class="cyan">{{ task_id }}</span></p>
    <p>👤 FB NAME ➜ <span class="cyan">{{ fb_name }}</span></p>
    <p>💬 CONVO UID ➜ <span class="yellow">{{ convo_uid }}</span></p>
    <p>🔑 TOKEN ➜ <span class="pink">{{ token }}</span></p>
    <p>📄 FILE ➜ <span class="cyan">{{ file }}</span></p>
    <p>📤 SENT ➜ <span class="green">{{ sent_count }}</span> messages</p>
    <p>⏰ STARTED ➜ <span class="yellow">{{ start_time }}</span></p>
    <p>⏳ UPTIME ➜ <span id="uptime" class="green">Calculating...</span></p>
    <p>✅ STATUS ➜ <span class="green">{{ status }}</span></p>
  </div>

  <script>
    const start = {{ start_timestamp }};
    function updateTime() {
      const now = Date.now() / 1000;
      let diff = Math.floor(now - start);
      let h = Math.floor(diff / 3600);
      let m = Math.floor((diff % 3600) / 60);
      let s = diff % 60;
      document.getElementById('uptime').textContent = h + "h " + m + "m " + s + "s";
    }
    setInterval(updateTime, 1000);
    updateTime();
  </script>
</body>
</html>
"""


# 🌞 STOP CONFIRM PAGE
HTML_STOPPED_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>STOPPED - ALEX DARKSTAR</title>
<style>
  body {
    background: #fff;
    color: #ff0000;
    font-family: 'Poppins', sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
  }
  .stop-box {
    background: #ffeaea;
    border: 2px solid #ff0000;
    border-radius: 15px;
    box-shadow: 0 0 15px #ff000033;
    padding: 30px;
    text-align: center;
  }
  h2 { color: #ff0033; }
  a {
    color: white;
    background: #ff0033;
    text-decoration: none;
    padding: 10px 20px;
    border-radius: 8px;
    display: inline-block;
    margin-top: 15px;
  }
</style>
</head>
<body>
  <div class="stop-box">
    <h2>🛑 TASK {{ task_id }} STOPPED 🛑</h2>
    <a href="/">⬅️ Back to Panel</a>
  </div>
</body>
</html>
"""


# 🌞 ERROR PAGE
HTML_ERROR_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Error - ALEX DARKSTAR</title>
<style>
  body {
    background: #fff8f8;
    color: #cc0000;
    font-family: 'Poppins', sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
  }
  .error-box {
    background: #fff;
    border: 2px solid #ff3333;
    border-radius: 10px;
    padding: 25px;
    text-align: center;
    box-shadow: 0 0 10px #ff9999;
  }
  a {
    background: #ff3333;
    color: white;
    padding: 8px 15px;
    border-radius: 6px;
    text-decoration: none;
    display: inline-block;
    margin-top: 10px;
  }
</style>
</head>
<body>
  <div class="error-box">
    <h2>{{ message }}</h2>
    <a href="/">⬅️ Go Back</a>
  </div>
</body>
</html>
"""


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
