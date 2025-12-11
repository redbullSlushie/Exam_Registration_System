from mysql.connector import connect
from dotenv import load_dotenv
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
import os
from datetime import datetime

# Allows usage of .env file
load_dotenv()

#Allows usage of Bcrypt
bcrypt = Bcrypt()

# Connect to Database
def get_db_connection():
    return connect(
        host="localhost",
        port=3306,
        user="root",
        password=os.getenv('MYSQL_PASSWORD'), # Use your own password 
        database="examreg_db" #db name
    )

# User Model
class User(UserMixin):
    def __init__(self, nshe_id, email, password_hash, exam_amount, role, first_name, last_name):
        self.id = nshe_id    #flask_login uses .id
        self.email = email
        self.role = role
        self.password_hash = password_hash
        self.exam_amt = exam_amount
        self.first_name = first_name
        self.last_name = last_name

    # Get User by email
    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            return User(
                nshe_id = row['nshe_id'],
                email = row['email'],
                role = row['role'],
                first_name = row['first_name'],
                last_name = row['last_name'],
                exam_amount = row['exam_amount'],
                password_hash = row['password_hash']
            )
        return None
        
    #Get User by nshe_id
    @staticmethod
    def get_by_id(nshe_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE nshe_id = %s", (int(nshe_id),))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            return User(
                nshe_id = row['nshe_id'],
                email = row['email'],
                role = row['role'],
                first_name = row['first_name'],
                last_name = row['last_name'],
                exam_amount = row['exam_amount'],
                password_hash = row['password_hash']
            )
        return None
    
    #Get hashed password for user
    @staticmethod
    def hashed_password(nshe_id):
        user = User.get_by_id(nshe_id)
        if not user:
            return None
        
        #convert to str
        password = str(user.id)
        #generate hash
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        #Update db
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE user SET password_hash = %s Where nshe_id = %s", (password_hash, nshe_id))
        conn.commit()
        cursor.close()
        conn.close()
        return password_hash

#---------------
#Exam Models
#---------------

#find exam by id
def get_exam_by_id(exam_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM exam_type WHERE exam_id = %s", (int(exam_id),))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return row

#Get all exams
def get_all_exams():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM exam_type")
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return results

#save to exam_type table
def input_exam_type(exam_type):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = ("INSERT INTO exam_type (exam_type) " \
    "VALUES (%s)")

    cursor.execute(query, (exam_type,))
    conn.commit()

    exam_id = cursor.lastrowid #the new exam_id

    cursor.close()
    conn.close()
    return exam_id

#---------------
#Location Models
#---------------

#insert location from create_exam
def input_location(location, building, room_num):
    conn= get_db_connection()
    cursor = conn.cursor()

    #check if location already exists
    cursor.execute("SELECT location_id " \
    "FROM location " \
    "WHERE campus_name = %s AND building= %s AND room_num = %s",
    (location, building, room_num))

    result = cursor.fetchone()
    if result:
        return result[0] #already exists

    #get new location_id
    cursor.execute("SELECT MAX(location_id) " \
    "FROM location")
    max_id= cursor.fetchone()[0]
    if max_id is None:
        new_id = 1
    else:
        new_id = max_id + 1

    #insert new location
    cursor.execute("INSERT INTO location (location_id, campus_name, building, room_num) " \
    "VALUES(%s, %s, %s, %s)", (new_id, location, building, room_num))
    conn.commit()

    cursor.close()
    conn.close()
    return new_id

# Get all locations from DB to display in the form
def locations():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT location_id, campus_name, building, room_num FROM location")
    locations = cursor.fetchall()

    cursor.close()
    conn.close()

#---------------
#Proctor Models
#---------------

#Check proctor existence
def proctor_exists(proctor_id, first_name, last_name, email):
    """Ensure there is a proctor row for the given user so FK inserts succeed."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT proctor_id FROM proctor WHERE proctor_id = %s", (proctor_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.close()
        conn.close()
        return proctor_id

    cursor.execute(
        "INSERT INTO proctor (proctor_id, first_name, last_name, email) "
        "VALUES (%s, %s, %s, %s)",
        (proctor_id, first_name, last_name, email)
    )
    conn.commit()

    cursor.close()
    conn.close()
    return proctor_id

#--------------------
#Exam Session Models
#--------------------

#save to exam_session table
def input_exam_session(proctor_id, exam_id, location_id, date, start_time, end_time):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = ("INSERT INTO exam_session (proctor_id, exam_id, location_id, date, start_time, end_time) "
    "VALUES (%s, %s, %s, %s, %s, %s)")

    cursor.execute(query, (proctor_id, exam_id, location_id, date, start_time, end_time))
    conn.commit()

    cursor.close()
    conn.close()

#Get all sessions for registration
def get_sessions_for_exam(exam_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT s.session_id, s.date, s.start_time, s.end_time, s.booked_seats, s.max_seats, l.campus_name, l.building, l.room_num, e.exam_type " \
    "FROM exam_session s " \
    "JOIN location l ON s.location_id = l.location_id " \
    "JOIN exam_type e ON s.exam_id = e.exam_id " \
    "WHERE s.exam_id = %s " \
    "ORDER BY s.date ASC"

    cursor.execute(query, (exam_id,))
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result if result else []

#get all sessions from db
def exam_session(exam_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM exam_session WHERE exam_id = %s", (exam_id,))
    sessions = cursor.fetchall()
    cursor.close()
    conn.close()

    return sessions

#---------------
#Booking Models
#---------------

#save to booking table
def add_to_booking(nshe_id, session_id, exam_id, time):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()
            
        #Check Seats are Available
        cursor.execute("SELECT max_seats, booked_seats " \
        "FROM exam_session " \
        "WHERE session_id = %s FOR UPDATE", (session_id,))
        sess = cursor.fetchone()

        if not sess:
            raise ValueError("Session Does Not Exist.")
        
        if sess['booked_seats'] >= sess['max_seats']:
            raise ValueError("This Session is Full.")

        #Create Booking
        cursor.execute("INSERT INTO bookings (nshe_id, session_id, exam_id, session_status, created_at, time) " \
        "VALUES (%s, %s, %s, 'Booked', NOW(), %s)", (nshe_id, session_id, exam_id, time))

        #Update Seat Count
        cursor.execute("UPDATE exam_session " \
        "SET booked_seats = booked_seats + 1 " \
        "WHERE session_id = %s", (session_id, ))

        #Update Student Exams
        cursor.execute("UPDATE user " \
        "SET exam_amount = exam_amount + 1 " \
        "WHERE nshe_id = %s", (nshe_id,))

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

#delete from booking table
def cancel_booking (booking_id, nshe_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        # Lock the booking row
        cursor.execute("""
            SELECT b.booking_id, b.nshe_id, b.session_id, b.session_status, b.time
            FROM bookings b
            WHERE b.booking_id=%s FOR UPDATE
        """, (booking_id,))
        b = cursor.fetchone()

        if not b or b["nshe_id"] != nshe_id:
            raise ValueError("Booking not found")

        if b["session_status"] != "Booked":
            raise ValueError("Only booked sessions can be cancelled")

        # Mark the booking as cancelled
        cursor.execute("""
            UPDATE bookings
            SET session_status='Cancelled'
            WHERE booking_id=%s
        """, (booking_id,))

        # Free a seat (assuming booked_seats counts how many are booked)
        cursor.execute("""
            UPDATE exam_session
            SET booked_seats = GREATEST(booked_seats - 1, 0)
            WHERE session_id=%s
        """, (b["session_id"],))

        # Decrease the user's exam count (but not below 0)
        cursor.execute("""
            UPDATE user
            SET exam_amount = GREATEST(exam_amount - 1, 0)
            WHERE nshe_id=%s
        """, (nshe_id,))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

#One booking
def one_booking_details(nshe_id, booking_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    b_details = "SELECT b.booking_id AS booking_id, b.created_at, b.time, b.session_status, b.session_id, " \
    "et.exam_type, et.exam_id, " \
    "es.date, es.start_time, es.end_time, es.max_seats, es.booked_seats, " \
    "p.first_name AS proctor_first, p.last_name AS proctor_last, " \
    "u.first_name, u.last_name, u.email, " \
    "l.campus_name, l.building, l.room_num " \
    "FROM bookings b " \
    "Join user u ON b.nshe_id = u.nshe_id " \
    "Join exam_session es ON b.session_id = es.session_id " \
    "Join exam_type et ON b.exam_id = et.exam_id " \
    "Join proctor p ON es.proctor_id = p.proctor_id " \
    "Join location l ON es.location_id = l.location_id " \
    "WHERE b.nshe_id = %s AND booking_id = %s"

    cursor.execute(b_details, (nshe_id, booking_id))
    result = cursor.fetchone()

    cursor.close()
    conn.close()
    return result

#All bookings
def booking_details(nshe_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    b_details = "SELECT b.booking_id AS booking_id, b.created_at, b.time, b.session_status, " \
    "et.exam_type, et.exam_id, " \
    "es.date, es.start_time, es.end_time, es.max_seats, es.booked_seats, " \
    "p.first_name AS proctor_first, p.last_name AS proctor_last, " \
    "u.first_name, u.last_name, u.email, " \
    "l.campus_name, l.building, l.room_num " \
    "FROM bookings b " \
    "Join user u ON b.nshe_id = u.nshe_id " \
    "Join exam_session es ON b.session_id = es.session_id " \
    "Join exam_type et ON b.exam_id = et.exam_id " \
    "Join proctor p ON es.proctor_id = p.proctor_id " \
    "Join location l ON es.location_id = l.location_id " \
    "WHERE b.nshe_id = %s"

    cursor.execute(b_details, (nshe_id,))
    result = cursor.fetchall()

    cursor.close()
    conn.close()
    return result

#Update booking
def update_exam(exam_id, session_id, booking_id, time):
    """Move a booking to a new session (and optional time) while keeping seat counts accurate."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        # Lock the existing booking
        cursor.execute(
            "SELECT session_id FROM bookings WHERE booking_id = %s FOR UPDATE",
            (booking_id,)
        )
        booking = cursor.fetchone()
        if not booking:
            raise ValueError("Booking not found.")

        old_session_id = booking["session_id"]

        # Lock the target session to check capacity
        cursor.execute(
            "SELECT booked_seats, max_seats FROM exam_session WHERE session_id = %s FOR UPDATE",
            (session_id,)
        )
        target_session = cursor.fetchone()
        if not target_session:
            raise ValueError("Selected session does not exist.")

        if session_id != old_session_id and target_session["booked_seats"] >= target_session["max_seats"]:
            raise ValueError("This session is full.")

        # Update booking
        cursor.execute(
            "UPDATE bookings SET exam_id = %s, session_id = %s, time = %s WHERE booking_id = %s",
            (exam_id, session_id, time, booking_id)
        )

        # Adjust seat counts if the session changed
        if session_id != old_session_id:
            cursor.execute(
                "UPDATE exam_session SET booked_seats = GREATEST(booked_seats - 1, 0) WHERE session_id = %s",
                (old_session_id,)
            )
            cursor.execute(
                "UPDATE exam_session SET booked_seats = booked_seats + 1 WHERE session_id = %s",
                (session_id,)
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to update exam: {e}")
    finally:
        cursor.close()
        conn.close()

#Check if booking exists
def check_existing_booking(nshe_id, exam_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * " \
    "FROM bookings " \
    "WHERE nshe_id = %s AND exam_id = %s " \
    "LIMIT 1", (nshe_id, exam_id))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result
    

#Check account existence
def account_exists(nshe_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM user WHERE nshe_id = %s", (nshe_id,))
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count > 0

#Create account - student
def create_account_stu(fullname, email, nshe_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    #password is hashed nshe_id
    pw_hash = bcrypt.generate_password_hash(str(nshe_id)).decode('utf-8')

    first_name, last_name = fullname.split(' ', 1)

    # Default role is 'student' and exam_amount is 0
    query = "INSERT INTO user (nshe_id, email, role, first_name, last_name, exam_amount, password_hash) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    values = (nshe_id, email, "student", first_name, last_name, 0, pw_hash)
    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

#Create account - faculty
def create_account_facu(fullname, email, nshe_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    #password is hashed nshe_id
    pw_hash = bcrypt.generate_password_hash(str(nshe_id)).decode('utf-8')

    first_name, last_name = fullname.split(' ', 1)

    # Default role is 'student' and exam_amount is 0
    query = "INSERT INTO user (nshe_id, email, role, first_name, last_name, exam_amount, password_hash) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    values = (nshe_id, email, "faculty", first_name, last_name, 0, pw_hash)
    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

#Create proctor account
def create_proctor(fullname, email, nshe_id, phone_number, department):
    conn = get_db_connection()
    cursor = conn.cursor()

    first_name, last_name = fullname.split(' ', 1)

    # Insert new proctor
    query ="INSERT INTO proctor (proctor_id, first_name, last_name, email, phone_number, department) VALUES (%s, %s, %s, %s, %s, %s)"
    values = (nshe_id, first_name, last_name, email, phone_number, department)
    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

#Exam sessions for Faculty reports
def exam_report(proctor_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT s.session_id, s.exam_id, s.date, s.start_time, s.end_time, s.booked_seats, s.max_seats, " \
    "l.campus_name, l.building, l.room_num, " \
    "e.exam_type, " \
    "u.first_name, u.last_name, u.nshe_id " \
    "FROM exam_session s " \
    "JOIN location l ON s.location_id = l.location_id " \
    "JOIN exam_type e ON s.exam_id = e.exam_id " \
    "LEFT JOIN bookings b ON b.session_id = s.session_id AND b.session_status = 'Booked' " \
    "LEFT JOIN user u ON u.nshe_id = b.nshe_id " \
    "WHERE s.proctor_id = %s " \
    "ORDER BY s.date ASC, s.start_time ASC"
    cursor.execute(query, (proctor_id, ))
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result

#Students in exam session > Faculty reports
def report_sess_dict(result):
    sessions = {}
    
    for row in result:
        sid = row['session_id']

        if sid not in sessions:
            sessions[sid] = {
            "exam_type": row["exam_type"],
                "campus_name": row["campus_name"],
                "building": row["building"],
                "room_num": row["room_num"],
                "booked_seats": row["booked_seats"],
                "max_seats": row["max_seats"],
                "students": []
        }
        
        #only if student exists in booking > exam_session
        if row['first_name']:
            sessions[sid]["students"].append({
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "nshe_id": row["nshe_id"]
            })

    return sessions