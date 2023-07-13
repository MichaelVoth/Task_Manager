from flask_app.config.mysqlconnection import connectToMySQL
from flask import flash
from flask_app import app
from flask_app.models.users import User



class Message:
    DB = "task_manager_schema"

    def __init__(self, data):
        self.id = data['id']
        self.message = data['message']
        self.task_id = data['task_id']
        self.author_id = data['author_id']
        self.is_read = data['is_read']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.author = None
        
    #Static
    @staticmethod
    def validate_message(message):
        is_valid = True
        if not len(message['message']) > 1:
            flash("* Message cannot be blank.", 'create')
            is_valid = False
        return is_valid

    #Class Methods

    #Create
    @classmethod
    def save(cls, data):
        query = '''INSERT INTO messages (author_id, task_id, message, is_read)
                VALUES (%(author_id)s, %(task_id)s, %(message)s, false);'''
        return connectToMySQL(cls.DB).query_db(query, data)

    
    #Read
    @classmethod
    def get_messages(cls, data):
        query = '''SELECT * FROM messages
                    JOIN users ON users.id = author_id
                    WHERE task_id = %(id)s;'''
        results = connectToMySQL(cls.DB).query_db(query, data)
        messages = []
        for message in results:
            message_obj = cls(message)
            user_data = {
                "id": message["id"],
                "first_name": message["first_name"],
                "last_name": message["last_name"],
                "email": message["email"],
                "password": message["password"],
                "admin": message["admin"],
                "created_at": message["users.created_at"],
                "updated_at": message["users.updated_at"]
            }
            message_obj.author = User(user_data)
            messages.append(message_obj)
        return messages
    
    @classmethod
    def get_messages_for_task(cls, data):
        query = '''SELECT * FROM messages WHERE task_id = %(task_id)s;'''
        results = connectToMySQL(cls.DB).query_db(query, data)
        
        messages = []
        for message in results:
            messages.append(cls(message))
        
        return messages
    
    @classmethod
    def check_if_read(cls, data):
        query = '''SELECT * FROM messages WHERE id = %(id)s AND `is_read` = 0;'''
        results = connectToMySQL(cls.DB).query_db(query, data)
        if len(results) > 0:
            return False
        return True
    

    #Update
    @classmethod
    def set_read(cls, data):
        query = "UPDATE messages SET is_read = true WHERE id = %(id)s"
        return connectToMySQL(cls.DB).query_db(query, data)


    
    @classmethod
    def edit_message(cls, data):
        query = '''UPDATE messages SET message = %(message)s WHERE id = %(id)s;'''
        return connectToMySQL(cls.DB).query_db(query, data)

    #Delete
    @classmethod
    def delete_message(cls, data):
        query = '''DELETE FROM messages WHERE id = %(id)s;'''
        return connectToMySQL(cls.DB).query_db(query, data)
    