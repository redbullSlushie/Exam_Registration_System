from flask import Flask, render_template, redirect
from mysql.connector import connect

# Connect to server
db = connect(
    host="localhost",
    port=3306,
    user="root",
    password="*****", # Use your own password
    database = "project_db") #db name

app = Flask(__name__)

# Get a cursor
cursor = db.cursor()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
     return redirect(render_template('login.html'))
     

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/account/', methods = ['GET']) #<id> add in
def acct():
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
    num_of_user = len(users)
    
    #if 'user' {{user.role}} == 'Student':  #how to choose template to render?
    cursor.execute('SELECT * FROM bookings')   #for the upcoming bookings
    items = cursor.fetchall()
    registrations = [{
            'id': item[0],
            'nshe_id': item[1],
            'class_name': item[2],
            'exam_session':item[3],
            'exam_type': item[4],
            'exam_date': item[5],
            'exam_time': item[6],
            'location': item[7],
            'room_num':item[8],
            'proctor': item[9],
            'created_at': item[10]
            }for item in items]
    num_of_regs = len(registrations)

    return render_template('acct_student.html', registrations = registrations, num_of_regs = num_of_regs,
                           users = users, num_of_user = num_of_user)   #render when user = student
    #return render_template('acct_faculty.html')    #render when user = faculty

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
