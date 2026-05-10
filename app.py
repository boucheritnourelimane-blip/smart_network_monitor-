import os
import sqlite3
import subprocess
from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "secret123"

# ================= BASE DE DONNÉES =================
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            ip TEXT,
            port TEXT,
            type TEXT,
            status TEXT,
            location TEXT,
            vendor TEXT,
            description TEXT
        )
    ''')
    conn.commit()

    # ✅ SEED DATA — يتحمل تلقائياً عند كل restart
    c.execute("SELECT COUNT(*) FROM devices")
    count = c.fetchone()[0]

    if count == 0:
        seed_devices = [
            ("Router_Main",    "192.168.1.1",   "80",   "Routeur", "Actif",   "Data Center", "MikroTik", "Routeur principal pour internet"),
            ("Router_Backup",  "192.168.1.2",   "8080", "Routeur", "Inactif", "Data Center", "Mikrotik", "Routeur de secours"),
            ("Core_Switch",    "192.168.1.20",  "22",   "Switch",  "Actif",   "Data Center", "Cisco",    "Switch central du réseau"),
            ("Switch_Floor1",  "192.168.1.10",  "22",   "Switch",  "Actif",   "1er étage",   "HP",       "Switch pour les postes utilisateurs"),
            ("Switch_Lab",     "192.168.2.10",  "22",   "Switch",  "Inactif", "Salle TP",    "D-Link",   "Switch pour les étudiants"),
        ]
        c.executemany(
            "INSERT INTO devices (name, ip, port, type, status, location, vendor, description) VALUES (?,?,?,?,?,?,?,?)",
            seed_devices
        )
        conn.commit()

    conn.close()

init_db()

# ================= FONCTION PING =================
def ping_device(ip):
    try:
        subprocess.check_output(["ping", "-c", "1", "-W", "2", ip])
        return "Actif"
    except Exception:
        return "Inactif"

# ================= ROUTES =================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "1234":
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash("Identifiants incorrects", "danger")
    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()
    devices = c.execute("SELECT * FROM devices").fetchall()
    routers  = sum(1 for d in devices if d["type"] == "Routeur")
    switches = sum(1 for d in devices if d["type"] == "Switch")
    actifs   = sum(1 for d in devices if d["status"] == "Actif")
    conn.close()

    return render_template("dashboard.html",
        devices=devices, routers=routers,
        switches=switches, actifs=actifs)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        name        = request.form.get('name')
        ip          = request.form.get('ip')
        port        = request.form.get('port')
        device_type = request.form.get('type')
        location    = request.form.get('location')
        vendor      = request.form.get('vendor')
        description = request.form.get('description')
        status      = ping_device(ip)

        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO devices (name,ip,port,type,status,location,vendor,description) VALUES (?,?,?,?,?,?,?,?)",
            (name, ip, port, device_type, status, location, vendor, description)
        )
        conn.commit()
        conn.close()
        flash("Équipement ajouté avec succès", "success")
        return redirect(url_for('dashboard'))

    return render_template("add_device.html")

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM devices WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Équipement supprimé", "info")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/status')
def status():
    return {"status": "ok"}, 200

# ================= LANCEMENT =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)