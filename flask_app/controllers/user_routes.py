from flask import render_template, redirect, request, session, flash, get_flashed_messages, request
from flask_app import app
from flask_app.models.users import User
from flask_bcrypt import Bcrypt
import requests


bcrypt = Bcrypt(app)

def get_weather_data(lat, lon):
    OPENWEATHER_API_KEY = '780b52cec813bd796130f8b9e4167ad8'
    OPENWEATHER_URL = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    try:
        response = requests.get(OPENWEATHER_URL)
        response.raise_for_status()  # This will raise an HTTPError for 4xx and 5xx responses
        return response.json()
    except requests.HTTPError as http_err:
        app.logger.error(f"HTTP error occurred: {http_err}")
        return None

@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error("Server Error: %s", (error))
    return render_template("500.html", error=error), 500



#Login Page.
@app.route('/')
def index_page():
#Collect validation messages and classes.
    validation_results = None
    validation_class = None
    login_email_messages = get_flashed_messages(category_filter=['login_email'])
    login_password_messages = get_flashed_messages(category_filter=['login_password'])

    if login_email_messages or login_password_messages:
        validation_results = {
            'email': login_email_messages,
            'password': login_password_messages,
        }
        validation_class = {
            'email': 'is-invalid' if login_email_messages else 'is-valid',
            'password': 'is-invalid' if login_password_messages else 'is-valid',
        }
    return render_template('login.html', validation_results=validation_results, validation_class=validation_class, session=session)


# Render the registration page.
@app.route('/register')
def register_page():
# Collect validation messages and classes.
    validation_class = None
    validation_results = None
    register_first_name_messages = get_flashed_messages(category_filter=['user_first_name'])
    register_last_name_messages = get_flashed_messages(category_filter=['user_last_name'])
    register_email_messages = get_flashed_messages(category_filter=['user_email'])
    register_password_messages = get_flashed_messages(category_filter=['user_password'])
    register_confirm_messages = get_flashed_messages(category_filter=['register_confirm'])
    register_validation_messages = get_flashed_messages(category_filter=['register_validation'])
    
    if register_validation_messages:
        validation_results = {
            'first_name': register_first_name_messages,
            'last_name': register_last_name_messages,
            'email': register_email_messages,
            'password': register_password_messages,
            'confirm_password': register_confirm_messages,
        }
        validation_class = {
            'first_name': 'is-invalid' if register_first_name_messages else 'is-valid',
            'last_name': 'is-invalid' if register_last_name_messages else 'is-valid',
            'email': 'is-invalid' if register_email_messages else 'is-valid',
            'password': 'is-invalid' if register_password_messages else 'is-valid',
            'confirm_password': 'is-invalid' if register_confirm_messages else 'is-valid',
        }

    return render_template(
        'register.html',
        validation_results=validation_results,  # Pass the validation_results to the template
        validation_class=validation_class,  # Pass the validation_classes to the template
    )


#Create user route.
@app.route('/register/user', methods=['POST'])
def register_user():
# Registers the user in the DB based on form data.
    session['first_name'] = request.form['first_name']
    session['last_name'] = request.form['last_name']
    session['email'] = request.form['email']
    session['admin'] = 'admin' in request.form  # Checks if admin checkbox is checked and adds to session data.
# Checks if email already exists in the database
    email = request.form['email']
    if User.get_by_email({'email': email}):
        flash("Email already in use.", 'register_email')
        return redirect('/register')

# Handles validation of registration.
    if not User.validate_user(request.form):
        flash("Invalid Registration", 'register_validation')
        return redirect('/register')
    
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

#Weather API call
    weather_data = get_weather_data(request.form['lat'], request.form['lon'])
    if not weather_data:
        flash("Failed to fetch weather data. Please try again later.", 'weather_error')
    session['weather_data'] = weather_data

    return redirect("/dashboard")


#Login route.
@app.route('/login', methods=['POST'])
def login():
#Handels user login.
    session['email'] = request.form['email']
#Prepares dictionary for email query.
    data = { "email" : request.form["email"] }
#Gets user data based on email.
    user_in_db = User.get_by_email(data)
#Checks if user is in DB.
    if not user_in_db:
        flash("Invalid Email/Password", 'login_email')
        return redirect("/")
#Checks if password matches DB.
    if not bcrypt.check_password_hash(user_in_db.password, request.form['password']):
        flash("Invalid Email/Password", 'login_password')
        return redirect('/')
#Adds user id to session data.
    session['user_id'] = user_in_db.id
    session['admin'] = user_in_db.admin
    del session['email']

#Weather API call.
    weather_data = get_weather_data(request.form['lat'], request.form['lon'])
    if not weather_data:
        flash("Failed to fetch weather data. Please try again later.", 'weather_error')
    session['weather_data'] = weather_data

    return redirect("/dashboard")


#Logout route.
@app.route('/logout')
def user_logout():
#Clears session and redirects to homepage.
    session.clear()

    return redirect('/')


#Edit user page.
@app.route("/user/edit/<int:id>")
def edit_user(id):
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')

    validation_results = None
    validation_class = None
    first_name_messages = get_flashed_messages(category_filter=['user_first_name'])
    last_name_messages = get_flashed_messages(category_filter=['user_last_name'])
    email_messages = get_flashed_messages(category_filter=['user_email'])
    if first_name_messages or last_name_messages or email_messages:
        validation_results = {
            'first_name': first_name_messages,
            'last_name': last_name_messages,
            'email': email_messages,
        }
        validation_class = {
            'first_name': 'is-invalid' if first_name_messages else 'is-valid',
            'last_name': 'is-invalid' if last_name_messages else 'is-valid',
            'email': 'is-invalid' if email_messages else 'is-valid',
        }
    
    user = User.get_by_id({'id': id})
    return render_template('user_edit.html', user=user, validation_results=validation_results, validation_class=validation_class)


#Update user route.
@app.route('/user/update/<int:id>', methods=['POST'])
def update_user(id):
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')

    
    if not User.validate_user_edit(request.form):
        return redirect('/user/edit/{}'.format(id))
    
    data = {
        "id" : id,
        "first_name" : request.form['first_name'],
        "last_name" : request.form['last_name'],
        "email" : request.form['email'],
        "admin" : 'admin' in request.form
    }
    User.update_user_info(data)

    return redirect('/user/{}'.format(id))


#Delete user route.
@app.route('/user/delete/<int:id>')
def delete_user(id):
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')
    User.delete_user(id)

    return redirect('/task/overview')

#Delete user confirmation page.
@app.route('/user/delete/confirm/<int:id>')
def delete_user_confirm(id):
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')
    
    message = "Are you sure you want to DELETE this user? This action cannot be undone."
    action = "/user/delete/" + str(id)
    method = "get"
    return redirect('/confirm?id={}&message={}&action={}&method{}'.format(id, message, action, method))
