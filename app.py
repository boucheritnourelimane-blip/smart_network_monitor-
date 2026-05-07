import os
import sqlite3
import subprocess

from flask import Flask, flash, redirect, render_template, request, session, url_for


app = Flask(__name__)
app.secret_key = "secret123"


# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect('database.db')
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
    conn.close()


init_db()


# ================= PING =================
def ping(ip):
    try:
        subprocess.check_output(["ping", "-c", "1", ip])
        return "Actif"
    except Exception:
        return "Inactif"


# ================= LOGIN =================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "1234":
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash("Username ou mot de passe incorrect")

    return render_template("login.html")


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    devices = c.execute("SELECT * FROM devices").fetchall()

    routers = sum(1 for d in devices if d[4] == "Routeur")
    switches = sum(1 for d in devices if d[4] == "Switch")

    conn.close()

    return render_template(
        "dashboard.html",
        devices=devices,
        routers=routers,
        switches=switches
    )


# ================= ADD =================
@app.route('/add', methods=['GET', 'POST'])
def add():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        ip = request.form.get('ip')
        port = request.form.get('port')
        type_ = request.form.get('type')
        location = request.form.get('location')
        vendor = request.form.get('vendor')
        description = request.form.get('description')

        status = ping(ip)

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO devices
            (name, ip, port, type, status, location, vendor, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, ip, port, type_, status, location, vendor, description)
        )

        conn.commit()
        conn.close()

        flash("Device ajoute avec succes")
        return redirect(url_for('dashboard'))

    return render_template("add_device.html")


# ================= DELETE =================
@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM devices WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("Device supprime")
    return redirect(url_for('dashboard'))


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ================= STATUS =================
@app.route('/status')
def status():
    return {"status": "running"}


# ================= RUN =================
if __name__ == "__main__":
    print("Server starting...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)