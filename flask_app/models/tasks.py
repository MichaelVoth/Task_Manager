from flask_app.config.mysqlconnection import connectToMySQL
from flask import flash
from flask_app import app
from flask_app.models.users import User
from flask_app.models.messages import Message


class Task:
    DB = "task_manager_schema"

    def __init__(self, data):
        self.id = data['id']
        self.title = data['title']
        self.due_date = data['due_date']
        self.details = data['details']
        self.complete = data['complete']
        self.completed_on = data['completed_on']
        self.assignee_id = data['assignee_id'] 
        self.assignee = None
        self.read_messages = []
        self.unread_messages = []
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
    
    #Validate:
    @staticmethod
    def validate_task(data):
        is_valid = True
        if len(data['title']) < 3:
            flash("Title must be at least 3 characters.", "task_title")
            is_valid = False
        if not data['due_date']:
            flash("Due date is required.", "task_due_date")
            is_valid = False
        if len(data['details']) < 3:
            flash("Details must be at least 3 characters.", "task_details")
            is_valid = False
        return is_valid

    # Create:
    @classmethod
    def save(cls, data):
        query = '''INSERT INTO tasks (title, due_date, details, assignee_id, complete)
                VALUES (%(title)s, %(due_date)s, %(details)s, %(assignee_id)s, 0);'''
        return connectToMySQL(cls.DB).query_db(query, data)

    # Read:
    @classmethod
    def get_all_tasks(cls): #get all tasks for all users
        query = '''SELECT * FROM tasks
                    LEFT JOIN users ON users.id = assignee_id;'''
        results = connectToMySQL(cls.DB).query_db(query) #returns a list of dictionaries
        tasks = [] #list of task objects
        for task in results: #loop through list of dictionaries
            task_obj = cls(task) #create a task object for each dictionary
            user_data = { #create a user object for each dictionary
                "id": task["assignee_id"],
                "first_name": task["first_name"],
                "last_name": task["last_name"],
                "email": task["email"],
                "password": task["password"],
                "admin": task["admin"],
                "created_at": task["users.created_at"],
                "updated_at": task["users.updated_at"]
            }
            task_obj.assignee = User(user_data) #assign the user object to the task object
            tasks.append(task_obj) #append the task object to the list of task objects
        return tasks
    
    @classmethod
    def get_complete_tasks_for_user(cls, data): #get all tasks for a specific user
        query = '''SELECT * FROM tasks WHERE assignee_id = %(id)s AND complete = 1;'''
        results = connectToMySQL(cls.DB).query_db(query, data) #returns a list of dictionaries
        tasks = [] #list of task objects
        for task in results: #loop through list of dictionaries
            tasks.append(cls(task)) #create a task object for each dictionary and append to list of task objects
        return tasks #return list of task objects

    @classmethod
    def get_incomplete_tasks_for_user(cls, data): #get all tasks for a specific user
        query = '''SELECT * FROM tasks WHERE assignee_id = %(id)s AND (complete = 0 OR complete IS NULL);'''
        results = connectToMySQL(cls.DB).query_db(query, data) #returns a list of dictionaries
        tasks = [] #list of task objects
        for task in results: #loop through list of dictionaries
            tasks.append(cls(task)) #create a task object for each dictionary and append to list of task objects
        return tasks #return list of task objects
    
    @classmethod
    def get_available_tasks(cls):
        query =  '''SELECT * FROM tasks WHERE (complete = 0 OR complete IS NULL)  AND assignee_id IS NULL;'''
        results = connectToMySQL(cls.DB).query_db(query) #returns a list of dictionaries
        tasks = [] #list of task objects
        for task in results: #loop through list of dictionaries
            tasks.append(cls(task)) #create a task object for each dictionary and append to list of task objects
        return tasks #return list of task objects
    

    @classmethod
    def get_task_by_id(cls, data, user_id):
        query = '''SELECT tasks.*, messages.id as message_id, messages.*, users.first_name, users.last_name
                    FROM tasks
                    LEFT JOIN messages ON tasks.id = messages.task_id
                    LEFT JOIN users ON messages.author_id = users.id
                    WHERE tasks.id = %(id)s;
                    '''
        results = connectToMySQL(cls.DB).query_db(query, data)
        # Create the task object
        task = cls(results[0])
        # Get all messages for this task
        for row in results:
            # Only process rows with a message
            if row['messages.id'] is not None:
                message_data = {
                    "id": row["message_id"],
                    "message": row["message"],
                    "task_id": row["task_id"],
                    "author_id": row["author_id"],
                    "is_read": row["is_read"],
                    "created_at": row["messages.created_at"],
                    "updated_at": row["messages.updated_at"]
                }
                # Create the message object
                message_obj = Message(message_data)
                # Create the author data dictionary
                author_data = {
                    "id": row["author_id"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"]
                }
                # Assign the author to the message object
                message_obj.author = User(author_data)
                # If the current user is the assignee and the message is not read, mark it as read
                if user_id == task.assignee_id and not message_obj.is_read:
                    Message.set_read({'id': message_obj.id})
                    message_obj.is_read = True
                # Add the message to the task's list of messages
                if message_obj.is_read:
                    task.read_messages.append(message_obj)
                else:
                    task.unread_messages.append(message_obj)
        return task


    @classmethod
    def get_tasks_with_unread_messages(cls, user_id):
        query = '''
            SELECT tasks.id, tasks.title
            FROM tasks
            JOIN messages ON tasks.id = messages.task_id
            WHERE messages.is_read = 0
            AND tasks.assignee_id = %(user_id)s
            GROUP BY tasks.id, tasks.title
        '''
        data = {'user_id': user_id}
        results = connectToMySQL(cls.DB).query_db(query, data)
        tasks = [{'id': row['id'], 'title': row['title']} for row in results]
        return tasks

    

    # Update:
    @classmethod
    def save_assignee(cls, data):
        query = '''
            UPDATE tasks
            SET assignee_id = %(id)s
            WHERE tasks.id = %(task_id)s;
        '''
        return connectToMySQL(cls.DB).query_db(query, data)
    
    @classmethod
    def mark_complete(cls, data):
        query = '''
            UPDATE tasks
            SET complete = 1, completed_on = NOW()
            WHERE id = %(id)s;
        '''
        return connectToMySQL(cls.DB).query_db(query, data)
    
    @classmethod
    def mark_incomplete(cls, data):
        query = '''
            UPDATE tasks
            SET complete = 0, completed_on = null
            WHERE id = %(id)s;
        '''
        return connectToMySQL(cls.DB).query_db(query, data)
    
    @classmethod
    def update_task(cls, data):
        query = '''
            UPDATE tasks
            SET title = %(title)s, due_date = %(due_date)s, details = %(details)s, assignee_id = %(assignee_id)s
            WHERE tasks.id = %(task_id)s;
        '''
        return connectToMySQL(cls.DB).query_db(query, data)
    
    #Delete:
    @classmethod
    def delete_task(cls, data):
        task_id = data['id']
        
        # Delete the messages associated with the task
        query_delete_messages = 'DELETE FROM messages WHERE task_id = %(task_id)s;'
        connectToMySQL(cls.DB).query_db(query_delete_messages, {'task_id': task_id})
        
        # Delete the task
        query_delete_task = 'DELETE FROM tasks WHERE id = %(task_id)s;'
        connectToMySQL(cls.DB).query_db(query_delete_task, {'task_id': task_id})

    

