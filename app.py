from flask import Flask, render_template, redirect, session, request, url_for, flash, render_template_string
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import User, bcrypt, booking_details, input_exam_session, input_exam_type, update_exam
import os
from dotenv import load_dotenv

# Allows usage of .env file
load_dotenv()

app = Flask(__name__)

""" #update db with password_hash
hash_pw = User.hashed_password(1234567898)
print("Hashed password stored in db:", hash_pw) """

# Flask Secret Key
app.config['SECRET_KEY'] = os.getenv('FlaskSecretKey')

# Flask_Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
#user_id comes from User.id (nshe_id)
def load_user(user_id):
    return User.get_by_id(user_id)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods= ['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        #look up user by email
        u = User.get_by_email(email)
        if u is None:
            flash("No account found with that email.", "danger")
            return redirect(url_for('login'))
        
        # PW Hash Existence Verification
        if not u.password_hash:
            flash("Password not set. Contact Support.", "danger")
            return redirect(url_for('login'))
        
        # Bcrypt Verification
        if not bcrypt.check_password_hash(u.password_hash, password):
            flash("Invalid Password.", "danger")
            return redirect(url_for('login'))
        
        print("Loggin in User:", u.email,u.role)
        login_user(u)
        flash("Login Successful!", "success")
    
        #redirect based on role
        role = u.role.lower()
        if role == "student":
            return redirect(url_for('student_acct')) #account/student
        elif role == "faculty":
            return redirect(url_for('faculty_acct')) #account/faculty
        else:
            flash("Unknown User. Contact Support", "danger")
            return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout', methods= ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
     

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/register')
def register():
    return render_template('registration_page.html')

@app.route('/register/add', methods = ['GET', 'POST'])
def add_booking():
    if request.method == 'POST':
        data = request.form
        subject = data.get('subject')
        location = data.get('location')
        time = data.get('time')

        add_exam = input_exam_session()
        add_exam_type = input_exam_type()

        return redirect(url_for('student_acct'))
    return render_template('registration_page.html')

@app.route('/account/student/', methods = ['GET'])
@login_required
def student_acct():
    nshe_id = current_user.id
    bookings = booking_details(nshe_id)

    return render_template('acct_student.html', user = current_user, bookings = bookings)

@app.route('/account/faculty/', methods = ['GET'])
#@login_required
def faculty_acct():
    nshe_id = current_user.id
    
    return render_template('acct_faculty.html', user = current_user)

@app.route('/account/student/<id>') #each exam individually
#@login_required
def exam(id):
    nshe_id = current_user.id
    bookings = booking_details(nshe_id)
    return render_template('exams.html', bookings = bookings)

@app.route('/account/student/edit/<id>')
def edit_exam():
    if request.method == 'POST':
        data = request.form
        subject = data.get('subject')
        location = data.get('location')
        time = data.get('time')

        update = update_exam()
    
    return redirect(url_for('student_acct'))

#@app.route('account/student/delete/<id>')

@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    location = request.form.get('location')
    time = request.form.get('time')

    return render_template('Confirmation_Page.html', name=name, email=email, subject=subject, location=location, time=time)


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
