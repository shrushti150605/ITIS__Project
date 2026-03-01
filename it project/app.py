from flask import Flask, render_template, request, redirect, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secretkey"

# ---------------- DATABASE CONNECTION ----------------
conn = sqlite3.connect('clinic_db.sqlite', check_same_thread=False)
cursor = conn.cursor()

# ---------------- CREATE TABLES IF NOT EXIST ----------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    specialization TEXT,
    fees INTEGER,
    max_patients INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT,
    doctor_id INTEGER,
    date TEXT,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
)
''')

# Add default admin if not exists
cursor.execute("SELECT * FROM users WHERE username='admin'")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   ('admin', 'admin123', 'admin'))
conn.commit()

# ---------------- PATIENT HOME ----------------
@app.route('/')
def home():
    cursor.execute("SELECT id, name, specialization, fees FROM doctors")
    doctors = cursor.fetchall()
    return render_template("patient_home.html", doctors=doctors)

# ---------------- PATIENT BOOKING ----------------
@app.route('/book/<int:doctor_id>', methods=['GET', 'POST'])
def patient_book(doctor_id):
    if request.method == 'POST':
        patient_name = request.form['patient_name']
        date = request.form['date']

        # Count bookings for that doctor and date
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE doctor_id=? AND date=?", (doctor_id, date))
        count = cursor.fetchone()[0]

        cursor.execute("SELECT max_patients FROM doctors WHERE id=?", (doctor_id,))
        max_patients = cursor.fetchone()[0]

        if count >= max_patients:
            flash("Doctor is fully booked for this date!")
            return redirect('/')

        cursor.execute("INSERT INTO appointments (patient_name, doctor_id, date) VALUES (?, ?, ?)",
                       (patient_name, doctor_id, date))
        conn.commit()
        flash("Appointment Booked Successfully!")
        return redirect('/')

    cursor.execute("SELECT id, name, specialization FROM doctors WHERE id=?", (doctor_id,))
    doctor = cursor.fetchone()
    return render_template("book.html", doctor=doctor)

# ---------------- PATIENT VIEW APPOINTMENTS ----------------
@app.route('/appointments')
def patient_appointments():
    cursor.execute('''
        SELECT a.patient_name, d.name, a.date
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
    ''')
    appointments = cursor.fetchall()
    return render_template("appointments.html", appointments=appointments)

# ---------------- ADMIN LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND role='admin'", (username, password))
        user = cursor.fetchone()

        if user:
            session['admin'] = True
            return redirect('/dashboard')
        else:
            flash("Invalid Credentials")
            return redirect('/login')

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/login')
    return render_template("dashboard.html")

# ---------------- ADD DOCTOR ----------------
@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if 'admin' not in session:
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        specialization = request.form['specialization']
        fees = request.form['fees']
        max_patients = request.form['max_patients']

        cursor.execute("INSERT INTO doctors (name, specialization, fees, max_patients) VALUES (?, ?, ?, ?)",
                       (name, specialization, fees, max_patients))
        conn.commit()
        flash("Doctor Added Successfully!")
        return redirect('/dashboard')

    return render_template("add_doctor.html")

# ---------------- VIEW DOCTORS ----------------
@app.route('/view_doctors')
def view_doctors():
    if 'admin' not in session:
        return redirect('/login')
    cursor.execute("SELECT id, name, specialization, fees FROM doctors")
    doctors = cursor.fetchall()
    return render_template("doctors.html", doctors=doctors)

# ---------------- VIEW APPOINTMENTS (ADMIN) ----------------
@app.route('/view_appointments')
def view_appointments():
    if 'admin' not in session:
        return redirect('/login')
    cursor.execute('''
        SELECT a.patient_name, d.name, a.date
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
    ''')
    appointments = cursor.fetchall()
    return render_template("appointments.html", appointments=appointments)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
