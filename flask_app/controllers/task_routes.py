from flask import render_template, redirect, request, session
from flask_app import app
from flask_app.models.users import User
from flask_app.models.tasks import Task
from flask_app.models.messages import Message

@app.route('/dashboard')
def dashboard_page():
    if session.get('user_id') is None:
        return redirect('/')

    user_id = session['user_id']
    user = User.get_by_id({'id': user_id})
    tasks = Task.get_incomplete_tasks_for_user({'id': user_id})
    available_tasks = Task.get_available_tasks()

    tasks_with_unread_messages = Task.get_tasks_with_unread_messages(user_id)

    return render_template('dashboard.html', user=user, tasks=tasks, available_tasks=available_tasks, tasks_with_unread_messages=tasks_with_unread_messages)


@app.route('/create') # Create task page.
def create_task_page():
    if session.get('user_id') is None:
        return redirect('/')
    user = User.get_all_users() # Get all users for assignee dropdown.
    return render_template('create_task.html', user=user)


@app.route('/add/task', methods=['POST']) # Add task to DB.
def add_task():
    if session.get('user_id') is None:
        return redirect('/')
    data = { # Create data dictionary to pass to save method.
        'title' : request.form['title'],
        'details' : request.form['details'],
        'due_date' : request.form['due_date'],
        'assignee_id' : int(request.form['assignee_id']) if request.form['assignee_id'] != '' else None,
    }
    Task.save(data)
    if request.form['assignee_id'] != 'null': # If assignee is not null, save assignee.
        Task.save_assignee(request.form) # Save assignee to task.
    return redirect('/dashboard')

@app.route('/add/assignee/<int:id>/task/<int:task_id>', methods=['POST']) # Add assignee to task.
def add_assignee(id, task_id):
    if session.get('user_id') is None:
        return redirect('/')
    data = {
        'id': id,
        'task_id': task_id 
    }
    Task.save_assignee(data)
    return redirect('/dashboard')


@app.route('/show/<int:id>') # Show task details page
def show_task_page(id):
    if session.get('user_id') is None:
        return redirect('/')
    
    # Get the task
    task = Task.get_task_by_id({'id': id}, session['user_id'])

    # If the current user is the assignee, mark unread messages as read
    if session['user_id'] == task.assignee_id:
        for message in task.unread_messages:
            Message.set_read({'id': message.id}) 
            task.read_messages.append(message)
        task.unread_messages = []

    # messages = Message.get_messages({'id': id})
    return render_template('task_details.html', task=task)

@app.route('/edit/<int:id>') # Edit task page
def edit_task(id):
    if session.get('user_id') is None:
        return redirect('/')
    task = Task.get_task_by_id({'id': id}, session['user_id'])
    user = User.get_all_users() # Get all users for assignee dropdown.
    return render_template('edit_task.html', task=task, user=user)

@app.route('/update/<int:id>', methods=['POST']) # Update task in DB.
def update_task(id):
    if session.get('user_id') is None:
        return redirect('/')
    data = {
        'task_id': id,
        'title': request.form['title'],
        'details': request.form['details'],
        'due_date': request.form['due_date'],
        'assignee_id': int(request.form['assignee_id']) if request.form['assignee_id'] != '' else None,
    }
    Task.update_task(data)
    return redirect('/dashboard')

@app.route('/delete/<int:id>') # Delete task from DB.
def delete_task(id):
    if session.get('user_id') is None:
        return redirect('/')
    Task.delete_task({'id': id})
    return redirect('/dashboard')

@app.route('/complete/<int:id>', methods = ["POST"]) # Mark task as complete.
def complete_task(id):
    if session.get('user_id') is None:
        return redirect('/')
    Task.mark_complete({'id': id})
    return redirect('/show/'+str(id))

@app.route('/incomplete/<int:id>', methods = ["POST"]) # Mark task as incomplete.
def incomplete_task(id):
    if session.get('user_id') is None:
        return redirect('/')
    Task.mark_incomplete({'id': id})
    return redirect('/show/'+str(id))

@app.route('/task/overview') # Task overview page.
def task_overview_page():
    if session.get('user_id') is None:
        return redirect('/')
    tasks = Task.get_all_tasks()
    user = User.get_by_id({'id': session['user_id']}) # Get user info by id in session.
    return render_template('task_overview.html', tasks=tasks, user=user)

@app.route('/user/<int:id>') # User details page.
def user_overview_page(id):
    if session.get('user_id') is None:
        return redirect('/')
    user = User.get_by_id({'id': id})
    complete_tasks = Task.get_complete_tasks_for_user({'id': id})
    incomplete_tasks = Task.get_incomplete_tasks_for_user({'id': id})
    return render_template('user_overview.html', user=user, complete_tasks=complete_tasks, incomplete_tasks=incomplete_tasks)