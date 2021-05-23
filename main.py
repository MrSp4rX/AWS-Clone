from flask import Flask, render_template, session, g, redirect, url_for
from flask.globals import request 
import sqlite3, pyotp
from datetime import date
from datetime import timedelta

app = Flask(__name__)

app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(days=7)
global COOKIE_TIME_OUT
COOKIE_TIME_OUT = 60*60*24*7 #7 days

@app.route('/')
def index():
    return redirect('/signup')

@app.route('/dashboard')
def dashboard():
    if "user" in session and session['status'] == 'verified':
        return render_template('dashboard.html')

    elif "user" in session and session['status'] == 'not-verified':
        return redirect('/scanQR')

    elif "user" not in session or session['status'] == 'not-verified':
        return '<script>alert("Please Login First!");window.onload = function() {location.href = "/login";}</script>'

    else:
        redirect('/signup')

@app.route('/myaccount')
def account():
    if "user" in session and session['status'] == 'verified':
        return render_template('myaccount.html')

    elif "user" in session and session['status'] == 'not-verified':
        return '<script>alert("Please Verify Yourself!");window.onload = function() {location.href = "/login";}</script>'

    elif "user" not in session or session['status'] == 'not-verified':
        return '<script>alert("Please Login First!");window.onload = function() {location.href = "/login";}</script>'

    else:
        return redirect('/login')

@app.route('/logout')
def logout():
    if "user" in session and session['status'] == 'verified':
        session.pop('user')
        session.pop('status')
        return redirect('/signup')

    elif "user" not in session or session['status'] == 'not-verified':
        return '<script>alert("Please Login First!");window.onload = function() {location.href = "/login";}</script>'

    else:
        return '<script>alert("Something went Wrong!");window.onload = function() {location.href = "/dashboard";}</script>'
        

@app.route('/verify/<email>', methods=['POST', 'GET'])
def verify(email):
    if "user" in session and session['status'] == 'not-verified':
        if request.method == "POST":
            con = sqlite3.connect('database.db')
            cur = con.cursor()
            cur.execute(f"select token from users where email = '{email}'")
            token = cur.fetchall()
            if len(token) == 1:
                totp = pyotp.TOTP(str(token[0][0]))
                otp = request.form['otp']
                if str(otp) == str(totp.now()):
                    session['status'] = "verified"
                    return redirect('/dashboard')

                elif str(otp) != str(totp.now()):
                    return '<script>alert("Wrong OTP Entered!");window.onload = function() {location.href = "/verify/' +email+ '";}</script>'

                else:
                    pass

        elif request.method == "GET":
            return render_template('verify.html', email=email)

        else:
            return redirect('/login')

    elif "user" in session and session['status'] == 'verified':
        return '<script>alert("You are Already Logged in Bruh");window.onload = function() {location.href = "/dashboard";}</script>'

    elif "user" not in session or session['status'] == 'not-verified':
        return '<script>alert("Please Login First!");window.onload = function() {location.href = "/signup";}</script>'

    else:
        return redirect('/login')

# @app.route('/login', methods=['POST', 'GET'])
# def login():
#     con = sqlite3.connect('database.db')
#     cur = con.cursor()
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
#         cur.execute(f"select name from users where email = '{email}' and password = '{password}'")
#         username = cur.fetchall()
#         if len(username) == 1:
#             session["user"] = username
#             session['status'] = 'not-verified'
#             # js = f"localStorage.setItem('status', 'not-verified'); localStorage.setItem('user', '{username}')"
#             return redirect('/verify/'+email)

#         elif len(username) < 1:
#             js = '<script>alert("Username or Password is Wrong!");window.onload = function() {location.href = "/signup";}</script>'
#             return js
#             # return render_template('login_signup.html', js=js)

#         else:
#             js = '<script>alert("Something went Wrong!");window.onload = function() {location.href = "/signup";}</script>'
                    
    
#     else:
#         return redirect('/signup')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    try:
        session.pop('user')
        session.pop('status')
    except:
        pass
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    if request.method == 'POST':
        if "name" in request.form:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            token = pyotp.random_base32()
            link = f"https://chart.googleapis.com/chart?chs=200x200&cht=qr&chl=otpauth://totp/AWSClone:{email}?secret={token}&issuer=AWSClone&choe=UTF-8"
            dt = date.today()
            cur.execute(f"select email from users where email = '{email}'")
            emails = cur.fetchall()
            if len(emails) > 0:
                for mail in emails:
                    if str(mail[0]) == email:
                        js = "<script>alert('Email Already Exist.');window.onload = function() {location.href = '/signup';}</script>"
                        # return render_template('login_signup.html', js=js)
                        return js
                        break
            else:
                cur.execute("select sno from users")
                snos = cur.fetchall()
                sno = snos[-1][0]
                cur.execute(f"INSERT INTO users VALUES ({sno+1}, '{name}', '{email}', '{password}', '{dt}', '{token}', '{link}')")
                con.commit()
                session["user"] = name
                session["status"] = 'not-verified'
                return render_template('scanqr.html', link=link, email=email, video_link="")
            
        else:
            email = request.form['email']
            password = request.form['password']
            cur.execute(f"select name from users where email = '{email}' and password = '{password}'")
            username = cur.fetchall()
            if len(username) == 1:
                session["user"] = username
                session['status'] = 'not-verified'
                return redirect('/verify/'+email)

            elif len(username) < 1:
                js = '<script>alert("Username or Password is Wrong!");window.onload = function() {location.href = "/signup";}</script>'
                # return render_template('login_signup.html', js=js)
                return js

            else:
                js = '<script>alert("Something went Wrong!");window.onload = function() {location.href = "/signup";}</script>'
                # return render_template('login_signup.html', js=js)
                return js

    else:
        return render_template('login_signup.html')

if __name__=="__main__":
    app.run(debug=True)