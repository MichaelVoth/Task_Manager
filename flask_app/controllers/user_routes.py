from flask import render_template, redirect, request, session, flash
from flask_app import app
from flask_app.models.users import User
from flask_app.models.tasks import Task
from flask_bcrypt import Bcrypt


bcrypt = Bcrypt(app)

@app.route('/')
def index_page():
    #Render the Homepage.
    return render_template('index.html')


@app.route('/register/user', methods=['POST'])
def register_user():
    #Registers the user in the DB based on form data.
    session['first_name'] = request.form['first_name']
    session['last_name'] = request.form['last_name']
    session['email'] = request.form['email']
    session['admin'] = 'admin' in request.form #Checks if admin checkbox is checked and adds to session data.
    # Checks if email already exists in the database
    email = request.form['email']
    if User.get_by_email({'email': email}):
        flash("Email already in use.", 'register')
        return redirect('/')
    
    #Handles validation of registration.
    if not User.validate_user(request.form):
        return redirect('/')
    
    #Hashes the password before saving in DB.
    hashed_password = bcrypt.generate_password_hash(request.form['password'])
    #Prepares dictionary with hashed password for DB save
    data = {
        "first_name": request.form['first_name'],
        "last_name" : request.form['last_name'],
        "email" : request.form['email'],
        "password" : hashed_password,
        "admin" : 'admin' in request.form
    }
    #Saves user in DB.
    user_id = User.save(data)
    #Adds user id to session data
    session['user_id'] = user_id
    del session['first_name'], session['last_name'], session['email']
    flash('Registration successful.', 'register')

    return redirect("/dashboard")


@app.route('/login', methods=['POST'])
def login():
    #Handels user login.
    #Prepares dictionary for email query.
    data = { "email" : request.form["email"] }
    #Gets user data based on email.
    user_in_db = User.get_by_email(data)
    #Checks if user is in DB.
    if not user_in_db:
        flash("Invalid Email/Password", 'login')
        return redirect("/")
    #Checks if password matches DB.
    if not bcrypt.check_password_hash(user_in_db.password, request.form['password']):
        flash("Invalid Email/Password", 'login')
        return redirect('/')
    #Adds user id to session data.
    session['user_id'] = user_in_db.id
    session['admin'] = user_in_db.admin

    return redirect("/dashboard")


@app.route('/logout')
def user_logout():
    #Clears session and redirects to homepage.
    session.clear()

    return redirect('/')