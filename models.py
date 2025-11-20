from mysql.connector import connect
from dotenv import load_dotenv
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
import os

# Allows usage of .env file
load_dotenv()

#Allows usage of Bcrypt
bcrypt = Bcrypt()

""" # Connect to server
db = connect(
    host="localhost",
    port=3306,
    user="root",
    password= os.getenv('MYSQL_PASSWORD'), # Use your own password 
    database = "examreg_db") #db name """

""" # Get a cursor
cursor = db.cursor() """

# Connect to server   
def get_db_connection():
    return connect(
        host="localhost",
        port=3306,
         user="root",
        password=os.getenv('MYSQL_PASSWORD'), # Use your own password 
        database="examreg_db" #db name
    )

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

#All DB tables
conn = get_db_connection()
cursor = conn.cursor()

def user():
    cursor.execute('SELECT * FROM user')   #for the upcoming bookings
    units = cursor.fetchall()
    users = [{
            'nshe_id': unit[0],
            'email': unit[1],
            'role': unit[2],
            'first_name': unit[3],
            'last_name': unit[4],
            'exam_amount': unit[5]
        }for unit in units]
    return users

def booking():
    cursor.execute('SELECT * FROM bookings')   #for the upcoming bookings
    items = cursor.fetchall()
    bookings = [{
            'id': item[0],
            'nshe_id': item[1],
            'session_id': item[2],
            'exam_id':item[3],
            'session_status': item[4],
            'created_at': item[5]
            }for item in items]
    return bookings

def exam_types():
    cursor.execute('SELECT * FROM exam_type')
    units = cursor.fetchall()
    exam_type = [{
        'id': unit[0],
        'exam_type': unit[1]
    }for unit in units]
    return exam_type

def proctors():
    cursor.execute('SELECT * FROM proctor')
    units = cursor.fetchall()
    proctor = [{
        'id': unit[0],
        'first_name': unit[1],
        'last_name': unit[2],
        'email': unit[3],
        'phone': unit[4],
        'department': unit[5]
    }for unit in units]
    return proctor

def exam_sessions():
    cursor.execute('SELECT * FROM exam_session')   #for the upcoming bookings
    units = cursor.fetchall()
    exam_session = [{
            'id': unit[0],
            'session_datetime': unit[1],
            'proctor_id': unit[2],
            'exam_id':unit[3],
            'max_seats': unit[4],
            'booked_seats': unit[5]
            }for unit in units]
    return exam_session

def booking_details(nshe_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    b_details = "SELECT b.booking_id AS booking_id, b.created_at, b.session_status, " \
    "et.exam_type, et.exam_id, " \
    "es.session_datetime, es.max_seats, es.booked_seats, " \
    "p.first_name AS proctor_first, p.last_name AS proctor_last, " \
    "u.first_name, u.last_name, u.email " \
    "FROM bookings b " \
    "Join user u ON b.nshe_id = u.nshe_id " \
    "Join exam_session es ON b.session_id = es.session_id " \
    "Join exam_type et ON b.exam_id = et.exam_id " \
    "Join proctor p ON es.proctor_id = p.proctor_id " \
    "WHERE b.nshe_id = %s"

    cursor.execute(b_details, (nshe_id,))
    result = cursor.fetchall()

    cursor.close()
    conn.close()
    return result

def input_exam_session():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("INSERT INTO exam_session (location, session_datetime)" \
    "VALUES (%s, %s)")
    conn.commit()

    cursor.close()
    conn.close()

def input_exam_type():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    #how to add a id to a new exam type?
    cursor.execute("INSERT INTO exam_type (exam_id, exam_type)" \
    "VALUES (%s, %s)")
    conn.commit()

    cursor.close()
    conn.close()

def update_exam():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    #booking? exam_session?
    cursor.execute("UPDATE booking (exam_id, exam_type)" \
    "VALUES (%s, %s)")
    conn.commit()

    cursor.close()
    conn.close()