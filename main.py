from flask import Flask, json, redirect, render_template, flash, request
from flask.globals import request, session
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import login_required, logout_user, login_user, login_manager, LoginManager, current_user

from flask_mail import Mail
import json



# mydatabase connection
local_server = True
app = Flask(__name__)
app.secret_key = "vaishu"


with open('config.json', 'r') as c:
    params = json.load(c)["params"]


app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)


# this is for getting the unique user access
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# app.config['SQLALCHEMY_DATABASE_URI']='mysql://username:password@localhost/databsename'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:vaishu%400427@localhost/covid1'
db = SQLAlchemy(app)

#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:vaishu@0427@localhost/covid1'
#db = SQLAlchemy(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Hospitaluser.query.get(int(user_id))


class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    srfid = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(50))
    dob = db.Column(db.String(1000))


class Hospitaluser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode = db.Column(db.String(20))
    email = db.Column(db.String(50))
    password = db.Column(db.String(1000))


class Hospitaldata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode = db.Column(db.String(20), unique=True)
    hname = db.Column(db.String(100))
    normalbed = db.Column(db.Integer)
    hicubed = db.Column(db.Integer)
    icubed = db.Column(db.Integer)
    vbed = db.Column(db.Integer)


class Trig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode = db.Column(db.String(20))
    normalbed = db.Column(db.Integer)
    hicubed = db.Column(db.Integer)
    icubed = db.Column(db.Integer)
    vbed = db.Column(db.Integer)
    querys = db.Column(db.String(50))
    date = db.Column(db.String(50))


class Bookingpatient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    srfid = db.Column(db.String(20), unique=True)
    bedtype = db.Column(db.String(100))
    hcode = db.Column(db.String(20))
    spo2 = db.Column(db.Integer)
    pname = db.Column(db.String(100))
    pphone = db.Column(db.String(100))
    paddress = db.Column(db.String(100))


@app.route("/")
def home():

    return render_template("index.html")


@app.route("/trigers")
def trigers():
    query = Trig.query.all()
    return render_template("trigers.html", query=query)


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        srfid = request.form.get('srf')
        email = request.form.get('email')
        dob = request.form.get('dob')

        user = User.query.filter_by(srfid=srfid).first()
        emailUser = User.query.filter_by(email=email).first()
        if user or emailUser:
            flash("Email or SRFID is already taken", "warning")
            return render_template("usersignup.html")

        # Adjust the SQL statement to match your actual table structure
        new_user = db.engine.execute(
            f"INSERT INTO user (srfid, email, dob) VALUES ('{srfid}', '{email}', '{dob}')"
        )

        flash("SignUp Success Please Login", "success")
        return render_template("userlogin.html")

    return render_template("usersignup.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        srfid = request.form.get('srf')
        dob = request.form.get('dob')
        user = User.query.filter_by(srfid=srfid).first()
        
        # Compare the stored dob directly
        if user and user.dob == dob:
            login_user(user)
            flash("Login Success", "info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials", "danger")
            return render_template("userlogin.html")

    return render_template("userlogin.html")


@app.route('/hospitallogin', methods=['POST', 'GET'])
def hospitallogin():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = Hospitaluser.query.filter_by(email=email).first()
        if user and user.password == password:  # Compare directly
            login_user(user)
            flash("Login Success", "info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials", "danger")
            return render_template("hospitallogin.html")

    return render_template("hospitallogin.html")


@app.route('/admin', methods=['POST', 'GET'])
def admin():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Assuming params is a dictionary that stores admin credentials
        # Example: params = {'user': 'admin_username', 'password': 'admin_password'}
        if username == params['user'] and password == params['password']:
            session['user'] = username
            flash("Login Success", "info")
            return render_template("addHosUser.html")
        else:
            flash("Invalid Credentials", "danger")

    return render_template("admin.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul", "warning")
    return redirect(url_for('login'))




@app.route('/addHospitalUser', methods=['POST', 'GET'])
def hospitalUser():
    if 'user' in session and session['user'] == params['user']:
        if request.method == "POST":
            hcode = request.form.get('hcode')
            email = request.form.get('email')
            password = request.form.get('password')  # Get the password directly
            hcode = hcode.upper()

            # Check if the user already exists in the database
            emailUser = Hospitaluser.query.filter_by(email=email).first()
            
            if emailUser:
                # Update the existing user's information if email exists
                emailUser.hcode = hcode
                emailUser.password = password  # Assuming plain text, consider hashing for security
                db.session.commit()
                flash("User already exists. Information updated successfully", "info")
            else:
                # Insert new user if email is not taken
                new_user = Hospitaluser(hcode=hcode, email=email, password=password)
                db.session.add(new_user)
                db.session.commit()
                flash("User added successfully", "info")

            return render_template("addHosUser.html")
    else:
        flash("Login and try Again", "warning")
        return render_template("addHosUser.html")
# testing wheather db is connected or not
@app.route("/test")
def test():
    try:
        a = Test.query.all()
        print(a)
        return f'MY DATABASE IS CONNECTED'
    except Exception as e:
        print(e)
        return f'MY DATABASE IS NOT CONNECTED {e}'


@app.route("/logoutadmin")
def logoutadmin():
    session.pop('user')
    flash("You are logout admin", "primary")

    return redirect('/admin')


@app.route("/hedit/<string:id>", methods=['POST', 'GET'])
@login_required
def hedit(id):
    posts = Hospitaldata.query.filter_by(id=id).first()

    if request.method == "POST":
        hcode = request.form.get('hcode')
        hname = request.form.get('hname')
        nbed = request.form.get('normalbed')
        hbed = request.form.get('hicubeds')
        ibed = request.form.get('icubeds')
        vbed = request.form.get('ventbeds')
        hcode = hcode.upper()
        db.engine.execute(
            f"UPDATE hospitaldata SET hcode ='{hcode}',hname='{hname}',normalbed='{nbed}',hicubed='{hbed}',icubed='{ibed}',vbed='{vbed}' WHERE hospitaldata.id={id}")
        flash("Slot Updated", "info")
        return redirect("/addhospitalinfo")

    # posts=Hospitaldata.query.filter_by(id=id).first()
    return render_template("hedit.html", posts=posts)


@app.route("/hdelete/<string:id>", methods=['POST', 'GET'])
@login_required
def hdelete(id):
    db.engine.execute(
        f"DELETE FROM hospitaldata WHERE hospitaldata.id={id}")
    flash("Data Deleted", "danger")
    return redirect("/addhospitalinfo")


@app.route("/pdetails", methods=['GET'])
@login_required
def pdetails():
    code = current_user.srfid
    data = Bookingpatient.query.filter_by(srfid=code).first()

    return render_template("detials.html", data=data)


@app.route("/slotbooking", methods=['POST', 'GET'])
@login_required
def slotbooking():
    query = db.engine.execute(f"SELECT * FROM hospitaldata ")
    seat = None  # Initialize seat to None

    if request.method == "POST":
        srfid = request.form.get('srfid')
        bedtype = request.form.get('bedtype')
        hcode = request.form.get('hcode')
        spo2 = request.form.get('spo2')
        pname = request.form.get('pname')
        pphone = request.form.get('pphone')
        paddress = request.form.get('paddress')

        check2 = Hospitaldata.query.filter_by(hcode=hcode).first()
        if not check2:
            flash("Hospital Code does not exist", "warning")
            return render_template("booking.html", query=query)  # Early return if hospital code not found

        code = hcode
        dbb = db.engine.execute(f"SELECT * FROM hospitaldata WHERE hospitaldata.hcode='{code}' ")

        # Logic to handle bed types
        if bedtype == "NormalBed":
            for d in dbb:
                seat = d.normalbed  # Set the number of available normal beds
                print(seat)
                ar = Hospitaldata.query.filter_by(hcode=code).first()
                ar.normalbed = seat - 1  # Update the bed count
                db.session.commit()

        elif bedtype == "HICUBed":
            for d in dbb:
                seat = d.hicubed
                print(seat)
                ar = Hospitaldata.query.filter_by(hcode=code).first()
                ar.hicubed = seat - 1
                db.session.commit()

        elif bedtype == "ICUBed":
            for d in dbb:
                seat = d.icubed
                print(seat)
                ar = Hospitaldata.query.filter_by(hcode=code).first()
                ar.icubed = seat - 1
                db.session.commit()

        elif bedtype == "VENTILATORBed":
            for d in dbb:
                seat = d.vbed
                print(seat)
                ar = Hospitaldata.query.filter_by(hcode=code).first()
                ar.vbed = seat - 1
                db.session.commit()
        else:
            flash("Invalid bed type", "danger")
            return render_template("booking.html", query=query)  # Handle invalid bed type

        # Check if seat is available and proceed with booking
        check = Hospitaldata.query.filter_by(hcode=hcode).first()
        if seat is not None and seat > 0 and check:
            res = Bookingpatient(srfid=srfid, bedtype=bedtype, hcode=hcode,
                                 spo2=spo2, pname=pname, pphone=pphone, paddress=paddress)
            db.session.add(res)
            db.session.commit()
            flash("Slot is booked; kindly visit the hospital for further procedure", "success")
        else:
            flash("Something went wrong or no seats available", "danger")

    return render_template("booking.html", query=query)



app.run(debug=True, port=5001)