import os
import sqlite3
import subprocess

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

# ================= CONFIGURATION =================

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


# ================= DATABASE =================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # Création table
    c.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ip TEXT NOT NULL,
            port TEXT,
            type TEXT,
            status TEXT,
            location TEXT,
            vendor TEXT,
            description TEXT
        )
    """)

    conn.commit()

    # Vérifier si la table est vide
    c.execute("SELECT COUNT(*) FROM devices")
    count = c.fetchone()[0]

    # Insertion automatique des équipements
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
                "Routeur principal assurant le routage et la connexion Internet"
            ),

            (
                "Router_Backup_02",
                "192.168.1.2",
                "8080",
                "Routeur",
                "Inactif",
                "Data Center - Salle A",
                "MikroTik",
                "Routeur de secours utilise en cas de panne"
            ),

            (
                "Router_DMZ_03",
                "192.168.2.1",
                "443",
                "Routeur",
                "Actif",
                "DMZ Zone",
                "Cisco",
                "Routeur securisant les serveurs publics"
            ),

            (
                "Switch_Core_01",
                "192.168.1.10",
                "22",
                "Switch",
                "Actif",
                "Data Center - Salle A",
                "Cisco",
                "Switch principal du reseau"
            ),

            (
                "Switch_Floor1_02",
                "192.168.1.11",
                "22",
                "Switch",
                "Actif",
                "Batiment A - Etage 1",
                "HP",
                "Switch utilise pour les postes utilisateurs"
            ),

            (
                "Switch_Floor2_03",
                "192.168.1.12",
                "22",
                "Switch",
                "Inactif",
                "Batiment A - Etage 2",
                "HP",
                "Switch actuellement en maintenance"
            ),

            (
                "Switch_Lab_04",
                "192.168.2.10",
                "22",
                "Switch",
                "Actif",
                "Laboratoire",
                "D-Link",
                "Switch dedie aux travaux pratiques"
            ),

            (
                "Switch_Server_05",
                "192.168.3.1",
                "22",
                "Switch",
                "Actif",
                "Salle Serveurs",
                "Cisco",
                "Switch assurant la connexion des serveurs"
            ),
        ]

        c.executemany("""
            INSERT INTO devices
            (name, ip, port, type, status, location, vendor, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_devices)

        conn.commit()

    conn.close()


# Initialisation DB
init_db()


# ================= PING FUNCTION =================

def ping_device(ip):

    try:

        # Windows
        if os.name == "nt":
            command = ["ping", "-n", "1", ip]

        # Linux / Ubuntu / Docker / Render
        else:
            command = ["ping", "-c", "1", ip]

        subprocess.check_output(command)

        return "Actif"

    except Exception:
        return "Inactif"


# ================= ROUTES =================

@app.route("/")
def home():
    return redirect(url_for("login"))


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Simple authentication
        if username == "admin" and password == "1234":

            session["logged_in"] = True
            flash("Connexion reussie", "success")

            return redirect(url_for("dashboard"))

        else:
            flash("Nom utilisateur ou mot de passe incorrect", "danger")

    return render_template("login.html")


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()

    devices = c.execute("SELECT * FROM devices").fetchall()

    total_devices = len(devices)

    routers = sum(1 for d in devices if d["type"] == "Routeur")

    switches = sum(1 for d in devices if d["type"] == "Switch")

    actifs = sum(1 for d in devices if d["status"] == "Actif")

    inactifs = sum(1 for d in devices if d["status"] == "Inactif")

    conn.close()

    return render_template(
        "dashboard.html",
        devices=devices,
        total_devices=total_devices,
        routers=routers,
        switches=switches,
        actifs=actifs,
        inactifs=inactifs
    )


# ================= ADD DEVICE =================

@app.route("/add", methods=["GET", "POST"])
def add_device():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form.get("name")
        ip = request.form.get("ip")
        port = request.form.get("port")
        device_type = request.form.get("type")
        location = request.form.get("location")
        vendor = request.form.get("vendor")
        description = request.form.get("description")

        # Ping automatique
        status = ping_device(ip)

        conn = get_db()
        c = conn.cursor()

        c.execute("""
            INSERT INTO devices
            (name, ip, port, type, status, location, vendor, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            ip,
            port,
            device_type,
            status,
            location,
            vendor,
            description
        ))

        conn.commit()
        conn.close()

        flash("Equipement ajoute avec succes", "success")

        return redirect(url_for("dashboard"))

    return render_template("add_device.html")


# ================= DELETE DEVICE =================

@app.route("/delete/<int:id>")
def delete_device(id):

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()

    c.execute("DELETE FROM devices WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    flash("Equipement supprime avec succes", "info")

    return redirect(url_for("dashboard"))


# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    flash("Deconnexion effectuee", "info")

    return redirect(url_for("login"))


# ================= STATUS API =================

@app.route("/status")
def status():
    return {"status": "ok"}, 200


# ================= MAIN =================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )