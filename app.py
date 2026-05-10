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

    c.execute("SELECT COUNT(*) FROM devices")
    count = c.fetchone()[0]

    if count == 0:
        sample_devices = [
            (
                "Router_Core_01",
                "192.168.1.1",
                "80",
                "Routeur",
                "Actif",
                "Data Center - Salle A",
                "Cisco",
                "Routeur principal — gestion du trafic reseau et connexion Internet"
            ),
            (
                "Router_Backup_02",
                "192.168.1.2",
                "8080",
                "Routeur",
                "Inactif",
                "Data Center - Salle A",
                "MikroTik",
                "Routeur de secours — active en cas de panne du routeur principal"
            ),
            (
                "Router_DMZ_03",
                "192.168.2.1",
                "443",
                "Routeur",
                "Actif",
                "Data Center - Salle B",
                "Cisco",
                "Routeur zone demilitarisee — gestion des serveurs publics"
            ),
            (
                "Switch_Core_01",
                "192.168.1.10",
                "22",
                "Switch",
                "Actif",
                "Data Center - Salle A",
                "Cisco",
                "Switch central — interconnexion de tous les equipements reseau"
            ),
            (
                "Switch_Floor1_02",
                "192.168.1.11",
                "22",
                "Switch",
                "Actif",
                "Batiment A - 1er etage",
                "HP",
                "Switch etage 1 — connexion des postes utilisateurs bureau"
            ),
            (
                "Switch_Floor2_03",
                "192.168.1.12",
                "22",
                "Switch",
                "Inactif",
                "Batiment A - 2eme etage",
                "HP",
                "Switch etage 2 — en maintenance programmee"
            ),
            (
                "Switch_Lab_04",
                "192.168.2.10",
                "22",
                "Switch",
                "Actif",
                "Salle TP Informatique",
                "D-Link",
                "Switch salle TP — connexion des postes etudiants"
            ),
            (
                "Switch_Server_05",
                "192.168.3.1",
                "22",
                "Switch",
                "Actif",
                "Data Center - Salle B",
                "Cisco",
                "Switch serveurs — interconnexion des serveurs virtuels"
            ),
        ]
        c.executemany(
            """INSERT INTO devices
            (name, ip, port, type, status, location, vendor, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            sample_devices
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
    routers = sum(1 for d in devices if d["type"] == "Routeur")
    switches = sum(1 for d in devices if d["type"] == "Switch")
    actifs = sum(1 for d in devices if d["status"] == "Actif")
    conn.close()

    return render_template(
        "dashboard.html",
        devices=devices,
        routers=routers,
        switches=switches,
        actifs=actifs
    )


@app.route('/add', methods=['GET', 'POST'])
def add():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        ip = request.form.get('ip')
        port = request.form.get('port')
        device_type = request.form.get('type')
        location = request.form.get('location')
        vendor = request.form.get('vendor')
        description = request.form.get('description')
        status = ping_device(ip)

        conn = get_db()
        c = conn.cursor()
        c.execute(
            """INSERT INTO devices
            (name, ip, port, type, status, location, vendor, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, ip, port, device_type, status, location, vendor, description)
        )
        conn.commit()
        conn.close()
        flash("Equipement ajoute avec succes", "success")
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
    flash("Equipement supprime", "info")
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