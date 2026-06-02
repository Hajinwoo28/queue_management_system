from flask import Blueprint

auth = Blueprint('auth',__name__)

@auth.route('/QueuingSystem')
def QueuingSystem():
    return "<p>Queue Management System</p>"

@auth.route('/Select_Department')
def Select_Department():
    return "<p>Queue Management System</p>"

@auth.route('/MonitorCode')
def MonitorCode():
    return "<p>Queue Management System</p>"

@auth.route('/')
def Get_Started():
    return "<p>Queue Management System</p>"