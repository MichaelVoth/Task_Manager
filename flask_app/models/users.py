from flask_app.config.mysqlconnection import connectToMySQL  # connect to db
from flask import flash  # flash messages
from flask_app import app  # flask app
import re  # regex
from flask_bcrypt import Bcrypt  # password hashing

bcrypt = Bcrypt(app)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')


class User:
    DB = "task_manager_schema"  # database name

    def __init__(self, data):  # create user object
        self.id = data['id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data.get('email', None)
        self.password = data.get('password', None)
        self.admin = data.get('admin', None)
        self.created_at = data.get('created_at', None)
        self.updated_at = data.get('updated_at', None)

    @staticmethod  # static means it does not need to be instantiated
    def validate_user(user):  # validate user info
        is_valid = True
        if not len(user['first_name']) >= 3 or not str.isalpha(user['first_name']):
            flash(
                "First name must be at least 2 characters and contain only letters.", 'register_first_name')
            is_valid = False
        if not len(user['last_name']) >= 3 or not str.isalpha(user['last_name']):
            flash(
                "Last name must be at least 2 characters and contain only letters.", 'register_last_name')
            is_valid = False
        if not EMAIL_REGEX.match(user['email']):
            flash("Invalid email address.", 'register_email')
            is_valid = False
        if not len(user['password']) >= 8:
            flash('Password must contain at least 8 characters.', 'register_password')
            is_valid = False
        if not any(char.isdigit() for char in user['password']):
            flash('Password must contain at least 1 number', 'register_password')
            is_valid = False
        if not any(char.isupper() for char in user['password']):
            flash("Password must contain at least 1 capital letter", 'register_password')
            is_valid = False
        if not user['password'] == user['confirm_password']:
            flash('Passwords must match', 'register_confirm')
            is_valid = False

        return is_valid


# Create:
    @classmethod  # class means it needs to be instantiated
    def save(cls, data):  # save user to db
        query = '''INSERT INTO users (first_name, last_name, email, password, admin)
                    VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s, %(admin)s);'''

        return connectToMySQL(cls.DB).query_db(query, data)


# Read:
    @classmethod
    def get_all_users(cls): # get all users from db
        query = "SELECT * FROM users;"
        results = connectToMySQL(cls.DB).query_db(query)
        users = []
        for a_user in results:
            users.append(cls(a_user))
        return users
    

    @classmethod
    def get_by_email(cls, data): # get user by email
        query = "SELECT * FROM users WHERE email = %(email)s;"
        result = connectToMySQL(cls.DB).query_db(query, data)
        if len(result) < 1:
            return False
        return cls(result[0])

    @classmethod
    def get_by_id(cls, data): # get user by id
        query = "SELECT * FROM users WHERE users.id = %(id)s;"
        result = connectToMySQL(cls.DB).query_db(query, data)
        if len(result) < 1:
            return False
        return cls(result[0])

#Update:
    @classmethod
    def update_user_info(cls,data): # update user info
        query = '''UPDATE users SET
                    first_name = %(first_name)s,
                    last_name = %(last_name)s,
                    email = %(email)s,
                    admin = %(admin)s
                    WHERE id = %(id)s;'''
        
        return connectToMySQL(cls.DB).query_db(query,data)

#Delete:
    @classmethod
    def delete_user(cls, id):
        # Get the IDs of tasks assigned to the user
        query = "SELECT id FROM tasks WHERE assignee_id = %(assignee_id)s;"
        assigned_tasks = connectToMySQL(cls.DB).query_db(query, {'assignee_id': id})

        # Delete the user from the database
        query = "DELETE FROM users WHERE id = %(id)s;"
        connectToMySQL(cls.DB).query_db(query, {'id': id})

        # Set the assignee of assigned tasks to unassigned (NULL)
        if assigned_tasks:
            task_ids = [task['id'] for task in assigned_tasks]
            query = "UPDATE tasks SET assignee_id = NULL WHERE id IN %(task_ids)s;"
            connectToMySQL(cls.DB).query_db(query, {'task_ids': task_ids})
