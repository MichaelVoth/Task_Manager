from flask import render_template, redirect, request, session, flash
from flask_app import app
from flask_app.models.messages import Message

@app.route('/message', methods=['POST'])
def save_message():
    if session.get('user_id') is None:
            return redirect('/')
    
    if not Message.validate_message(request.form):
        return redirect(f"/show/{request.form['task_id']}")
    
    Message.save(request.form)

    return redirect(f'/show/{request.form["task_id"]}')