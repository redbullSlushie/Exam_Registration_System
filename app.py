from flask import Flask, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user # type: ignore
from models import User, bcrypt, booking_details, input_exam_session, input_exam_type, update_exam, cancel_booking, exam_report, create_proctor, proctor_exists
from models import get_all_exams, add_to_booking, get_sessions_for_exam, input_location, create_account_stu, create_account_facu, account_exists, one_booking_details
from models import check_existing_booking
import os
from dotenv import load_dotenv # type: ignore
from datetime import datetime, timedelta

# Allows usage of .env file
load_dotenv()

app = Flask(__name__)

""" #update db with password_hash
hash_pw = User.hashed_password(1234567898)
print("Hashed password stored in db:", hash_pw) """

# Cookie Duration
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=2)

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
        login_user(u, remember=True)
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
     

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        nshe_id = request.form.get('nshe_id')
        confirmed_nshe_id = request.form.get('confirmed_nshe_id')
        
        if account_exists(nshe_id):
            flash("Account with that NSHE ID already exists.")
            return redirect('/signup')
        
        elif confirmed_nshe_id != nshe_id:
            flash("NSHE ID does not match.")
            return redirect('/signup')
        
        elif not email.endswith('@student.csn.edu'):
            create_account_facu(fullname, email, nshe_id)
            return render_template('faculty_additional.html', fullname=fullname, email=email, nshe_id=nshe_id)
        
        else: 
            create_account_stu(fullname, email, nshe_id)
            flash("Account created successfully!", "success")
            
            return redirect('/login')
    
    return render_template('signup.html')

@app.route('/faculty_additional', methods= ['POST'])
def faculty_additional():
    
    fullname = request.form.get('fullname')
    email = request.form.get('email')
    nshe_id = request.form.get('nshe_id')
    phone_number = request.form.get('phone_number')
    department = request.form.get('department')

    create_proctor(fullname, email, nshe_id, phone_number, department)
    flash("Faculty account created successfully!", "success")
    return redirect('/login')

@app.route('/register', methods = ['GET', 'POST'])
@login_required
def register_exam():
    #Get from DB
    exams = get_all_exams()
    if not exams:
        flash("Exam not found.", "danger")
        return redirect(url_for('student_acct'))
    
    #Load sessions then filter full sessions out
    all_sessions = []
    for exam in exams:
        sessions = get_sessions_for_exam(exam['exam_id'])

        #only sessions that are not full
        available_sessions = [s for s in sessions if int(s['booked_seats']) < int(s['max_seats'])]
        for s in available_sessions:
            s['exam_type'] = exam['exam_type']
            s['exam_id'] = exam['exam_id']
        
            start_time = (s['start_time'])
            end_time = (s['end_time'])

            #generate every hour
            available_times = []
            while start_time <= end_time:
                available_times.append(start_time)
                start_time += timedelta(hours= 1)

            s['available_times'] = available_times

        #add sessions to list
        all_sessions.extend(available_sessions)

    if request.method == 'POST':
        combined = request.form.get('session_id')
        time = request.form.get('time')

        if not combined or not time:
            flash('Please choose an exam session and time.', "danger")
            return redirect(url_for('register_exam'))
        
        session_id, exam_id = combined.split('|')
        session_id = int(session_id)
        exam_id = int(exam_id)

        if check_existing_booking(nshe_id = current_user.id, exam_id = exam_id):
            flash("You have already registered for this exam.", 'danger')
            return redirect(url_for('student_acct'))
        try:
            add_to_booking(nshe_id= current_user.id, session_id= session_id, exam_id= exam_id, time= time)
            flash("Successfully Registered!", 'success')
            return redirect(url_for('student_acct'))
        
        except Exception as e:
            flash(str(e), 'danger')
            return redirect(url_for('register_exam', exam_id = exam_id))
    
    return render_template('registration_page.html', sessions = all_sessions)

@app.route('/account/student/', methods = ['GET'])
@login_required
def student_acct():
    nshe_id = current_user.id
    bookings = booking_details(nshe_id)

    return render_template('acct_student.html', user = current_user, bookings = bookings)

@app.route('/account/faculty/', methods = ['GET'])
@login_required
def faculty_acct():
    return render_template('acct_faculty.html', user = current_user)

@app.route('/create_exam', methods = ['GET', 'POST'])
@login_required
def create_exam():
    if request.method == "POST":
        exam_type = request.form['exam_type']
        location = request.form.get('location')
        building = request.form.get('building')
        room_num = request.form.get('room_num')
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        proctor_id = current_user.id

        #validate locations
        if not location:
            flash('At least one location is required', 'danger')
            return redirect(url_for('create_exam'))

        #validate start and end times
        if start_time >= end_time:
            flash('Start time must be before end time.', 'danger')
            return redirect(url_for('create_exam'))
        
        if start_time < "08:00" or end_time > "17:00":
            flash('Time range must be between 08:00 and 17:00', 'danger')
            return redirect(url_for('create_exam'))
        
        # Make sure this faculty member exists in the proctor table for FK constraints
        proctor_exists(
            proctor_id=proctor_id,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            email=current_user.email
        )

        #insert exam >> return exam_id
        exam_id = input_exam_type(exam_type)
        
        #insert new location
        location_id= input_location(location, building, room_num)

        #insert each session using exam_id
        input_exam_session(proctor_id, exam_id, location_id, date, start_time, end_time)

        flash('Exam Successfully Created!', 'success')
        return redirect(url_for('faculty_acct'))

    return render_template('create_exam.html')

@app.route('/reports')
@login_required
def reports():
    proctor_id = current_user.id
    result = exam_report(proctor_id)

    for r in result:
        print("DEBUG ROW:", r)

    exams = {}
    
    for r in result:
        session_id = r['session_id']

        if session_id not in exams:
            exams[session_id] = {
                "exam_type": r["exam_type"],
                "campus_name": r["campus_name"],
                "building": r["building"],
                "room_num": r["room_num"],
                "date": r["date"],
                "start_time": r["start_time"],
                "end_time": r["end_time"],
                "booked_seats": r["booked_seats"],
                "max_seats": r["max_seats"],
                "students": []
            }

        if r.get("nshe_id"):
            exams[session_id]["students"].append({
                "first_name": r['first_name'],
                "last_name": r['last_name'],
                "nshe_id": r['nshe_id']
            })

    for session_id, exam in exams.items():
        print("DEBUG SESSION:", session_id, exam['students'])

    return render_template('reports.html', exams = exams)

@app.route('/account/student/<int:booking_id>') #each exam individually
@login_required
def exam(booking_id):
    exam = one_booking_details(nshe_id= current_user.id, booking_id= booking_id)
    if isinstance(exam['time'], timedelta):
        seconds = exam['time'].seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        exam['time'] = f"{hours:02d}:{minutes:02d} {'AM' if hours < 12 else 'PM'}"

    return render_template('exams.html', exam = exam)

@app.route('/account/student/edit/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_exam(booking_id):
    nshe_id = current_user.id
    booking = one_booking_details(nshe_id, booking_id)

    if booking is None:
        flash("Booking not found.", "danger")
        return redirect(url_for('student_acct'))

    # Load available sessions for that exam
    sessions = get_sessions_for_exam(booking['exam_id'])

    all_sessions = []
    for s in sessions:
        s['exam_id'] = booking['exam_id']
        if (s['booked_seats']) < (s['max_seats']):

            #generate every hour
            available_times = []
            current = s['start_time']
            while current <= s['end_time']:
                available_times.append(current)
                current += timedelta(hours= 1)

            s['available_times'] = available_times

        else:
            s['available_times'] = []   #full session
        all_sessions.append(s)

    # Determine selected session for time dropdown
    selected_session_id = request.args.get('session_id', default=booking['session_id'], type=int)
    selected_session = next((s for s in all_sessions if s['session_id'] == selected_session_id), None)
    available_times = selected_session['available_times'] if selected_session else []

    if request.method == 'POST':
        combined = request.form.get('session_id')
        time = request.form.get('time')

        if not combined or not time:
            flash('Please choose an exam session and time.', "danger")
            return redirect(url_for('edit_exam', booking_id=booking_id, session_id=selected_session_id))
        
        try:
            session_id_str, exam_id_str = map(int, combined.split('|'))
        except (ValueError, AttributeError):
            flash('Invalid session selected.', 'danger')
            return redirect(url_for('edit_exam', booking_id=booking_id, session_id=selected_session_id))
        
        session_id = int(session_id_str)
        exam_id = int(exam_id_str)

        #convert time to time_object
        try:
            if len(time) == 8:
                time_obj = datetime.strptime(time, "%H:%M:%S").time()
            else:
                # Try HH:MM
                time_obj = datetime.strptime(time, "%H:%M").time()
        except (ValueError, TypeError):
            flash('Invalid time selected.', 'danger')
            return redirect(url_for('edit_exam', booking_id=booking_id, session_id=selected_session_id))
        
        print("Form data:", request.form)
        print("Parsed session_id, exam_id, time:", session_id, exam_id, time)
        
        try:
            update_exam(exam_id, session_id, booking_id=booking_id, time=time_obj,)
            print("Booking updated successfully!")
        except Exception as e:
            print("Error updating booking:", e)
            flash(str(e), 'danger')

        flash("Exam successfully rescheduled!", "success")
        return redirect(url_for('student_acct'))

    return render_template(
        'edit_registration.html',
        booking=booking,
        sessions=all_sessions,
        exam_id=booking['exam_id'],
        selected_session_id=selected_session_id,
        available_times=available_times
    )

@app.route('/account/student/delete/<int:booking_id>', methods=['POST'])
def cancel_booking_route(booking_id):
    
    try:
        # call the DB logic function
        cancel_booking(booking_id, nshe_id=current_user.id)
        flash("Your booking has been cancelled.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        print("Cancel error:", e)
        flash("An error occurred while cancelling the booking.", "danger")

    return redirect(url_for('student_acct'))

@app.route('/confirm', methods=['GET', 'POST'])
@login_required
def confirm():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    location = request.form.get('location')
    time = request.form.get('time')

    return render_template('Confirmation_Page.html', name=name, email=email, subject=subject, location=location, time=time)


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
