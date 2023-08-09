from flask import render_template, redirect, request, session, get_flashed_messages, request
from flask_app import app
from flask_app.models.users import User
from flask_app.models.tasks import Task
from flask_app.models.messages import Message
import requests


# Dashboard page.


@app.route('/dashboard')
def dashboard_page():
    if session.get('user_id') is None:
        return redirect('/')
# Get user and tasks for dashboard.
    user_id = session['user_id']
    user = User.get_by_id({'id': user_id})
    tasks = Task.get_incomplete_tasks_for_user({'id': user_id})
    available_tasks = Task.get_available_tasks()
    tasks_with_unread_messages = Task.get_tasks_with_unread_messages(user_id)

    return render_template('dashboard.html', user=user, tasks=tasks, available_tasks=available_tasks, tasks_with_unread_messages=tasks_with_unread_messages)

# Create task page.
@app.route('/create')
def create_task_page():
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')
# Collect validation messages and classes.
    validation_results = None
    validation_class = None
    title_messages = get_flashed_messages(category_filter=['task_title'])
    due_date_messages = get_flashed_messages(category_filter=['task_due_date'])
    details_messages = get_flashed_messages(category_filter=['task_details'])
    if title_messages or due_date_messages or details_messages:
        validation_results = {
            'title': title_messages,
            'due_date': due_date_messages,
            'details': details_messages,
        }
        validation_class = {
            'title': 'is-invalid' if title_messages else 'is-valid',
            'due_date': 'is-invalid' if due_date_messages else 'is-valid',
            'details': 'is-invalid' if details_messages else 'is-valid',
        }
# Get all users for assignee dropdown.
    user = User.get_all_users()
    return render_template('create_task.html', user=user, validation_results=validation_results, validation_class=validation_class)


# Add task to DB.
@app.route('/add/task', methods=['POST'])
def add_task():
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')
# Validate task
    is_valid = Task.validate_task(request.form)
    if not is_valid:
        session['title'] = request.form['title']
        session['details'] = request.form['details']
        session['due_date'] = request.form['due_date']
        assignee_id = request.form['assignee_id']
        session['assignee_id'] = int(assignee_id) if assignee_id else None

        return redirect('/create')
# Task is valid, proceed with saving
    data = {
        'title': request.form['title'],
        'details': request.form['details'],
        'due_date': request.form['due_date'],
        'assignee_id': int(request.form['assignee_id']) if request.form['assignee_id'] != '' else None,
    }
    Task.save(data)
# If assignee is not null, save assignee.
    if request.form['assignee_id'] != 'null':
        Task.save_assignee(request.form)
# Clear session variables.
    session.pop('title', None)
    session.pop('details', None)
    session.pop('due_date', None)
    session.pop('assignee_id', None)
    return redirect('/dashboard')


# Add assignee to task.
@app.route('/add/assignee/<int:id>/task/<int:task_id>', methods=['POST'])
def add_assignee(id, task_id):
    if session.get('user_id') is None:
        return redirect('/')

    data = {
        'id': id,
        'task_id': task_id
    }
    Task.save_assignee(data)
    return redirect('/dashboard')

# Show task details page


@app.route('/show/<int:id>')
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
    return render_template('task_details.html', task=task)


# Edit task page
@app.route('/edit/<int:id>')
def edit_task(id):
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')
# Collect validation messages and classes.
    validation_results = None
    validation_class = None
    title_messages = get_flashed_messages(category_filter=['task_title'])
    due_date_messages = get_flashed_messages(category_filter=['task_due_date'])
    details_messages = get_flashed_messages(category_filter=['task_details'])
    if title_messages or due_date_messages or details_messages:
        validation_results = {
            'title': title_messages,
            'due_date': due_date_messages,
            'details': details_messages,
        }
        validation_class = {
            'title': 'is-invalid' if title_messages else 'is-valid',
            'due_date': 'is-invalid' if due_date_messages else 'is-valid',
            'details': 'is-invalid' if details_messages else 'is-valid',
        }
# Get task and all users for assignee dropdown.
    task = Task.get_task_by_id({'id': id}, session['user_id'])
    user = User.get_all_users()
    return render_template('edit_task.html', task=task, user=user, validation_results=validation_results, validation_class=validation_class)


# Update task in DB.
@app.route('/update/<int:id>', methods=['POST'])
def update_task(id):
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')
# Validate task
    is_valid = Task.validate_task(request.form)
    if not is_valid:
        session['title'] = request.form['title']
        session['details'] = request.form['details']
        session['due_date'] = request.form['due_date']
        session["assignee_id"] = int(request.form["assignee_id"])
        return redirect(f'/edit/{id}')
# Task is valid, proceed with saving
    data = {
        'task_id': id,
        'title': request.form['title'],
        'details': request.form['details'],
        'due_date': request.form['due_date'],
        'assignee_id': int(request.form['assignee_id']) if request.form['assignee_id'] != '' else None,
    }
    Task.update_task(data)
# Clear session variables.
    session.pop('title', None)
    session.pop('details', None)
    session.pop('due_date', None)
    session.pop('assignee_id', None)
    return redirect('/dashboard')


# Mark Delete Task Confirmation
@app.route('/delete/confirm/<int:id>')
def delete_task_confirm(id):
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')

    message = "Are you sure you want to DELETE this task? This action cannot be undone."
    action = "/delete/" + str(id)
    method = "get"
    return redirect('/confirm?id={}&message={}&action={}&method{}'.format(id, message, action, method))


# Delete task from DB.
@app.route('/delete/<int:id>')
def delete_task(id):
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')

    Task.delete_task({'id': id})
    return redirect('/dashboard')


# Mark task as complete.
@app.route('/complete/<int:id>', methods=["POST"])
def complete_task(id):
    if session.get('user_id') is None:
        return redirect('/')

    Task.mark_complete({'id': id})
    return redirect('/dashboard')


# Mark task as incomplete.
@app.route('/incomplete/<int:id>', methods=["POST"])
def incomplete_task(id):
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')
    Task.mark_incomplete({'id': id})
    return redirect('/dashboard')


# Mark Complete Task Confirmation
@app.route('/complete/confirm/<int:id>')
def complete_confirm(id):
    if session.get('user_id') is None:
        return redirect('/')

    message = "Are you sure you want to complete this task? You will not be able to come back to it after it is complete!"
    action = "/complete/" + str(id)
    method = "POST"
    return render_template('confirm.html', id=id, message=message, action=action, method=method)


# Task overview page.
@app.route('/task/overview')
def task_overview_page():
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')

    tasks = Task.get_all_tasks()
# Get user info by id in session.
    user = User.get_by_id({'id': session['user_id']})
    

    return render_template('task_overview.html', tasks=tasks, user=user)


# User details page.
@app.route('/user/<int:id>')
def user_overview_page(id):
    if 'user_id' not in session or session.get('admin') != True:
        return redirect('/')

    user = User.get_by_id({'id': id})
    complete_tasks = Task.get_complete_tasks_for_user({'id': id})
    incomplete_tasks = Task.get_incomplete_tasks_for_user({'id': id})

    return render_template('user_overview.html', user=user, complete_tasks=complete_tasks, incomplete_tasks=incomplete_tasks)


# Confirmation page

@app.route('/confirm')
def confirm_page():
    if session.get('user_id') is None:
        return redirect('/')

    id = request.args.get('id')
    message = request.args.get('message')
    action = request.args.get('action')
    method = request.args.get('method')

    return render_template('confirm.html', message=message, action=action, id=id, method=method)
