#!/usr/bin/python3

from flask import Flask, render_template, redirect, url_for, request, Response
from functools import wraps
import sqlite3
import sys
import os.path
from datetime import datetime

DATABASE = "comments.db"

app = Flask(__name__, template_folder="templates")



def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
    

# DB MANAGEMENT


def dict_factory(cursor, row):
    '''Useful function to print tables SELECT as dict'''

    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def connect_to_db():
    '''Manage the connection opening to the DB
    Does NOT include the closure of the connection'''

    if not os.path.isfile(DATABASE):
        print("Database not found, exit.")
        sys.exit(1)
    try:
        conn = sqlite3.connect(DATABASE)
        return conn
    except:
        print("Error when opening the database, exit.")
        sys.exit(1)


def print_comments(search_args=None):
    '''Return a list of dict of comments.
    if search_args, then apply the search
    Return 1 if error during the search (bad search argument)
    Return 2 if nothing to diplay
    '''

    conn = connect_to_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    query = "SELECT comments.*, threads.title, threads.uri \
        FROM comments JOIN threads ON comments.tid = threads.id"

    if search_args:
        query += " WHERE"
        for arg in search_args:
            if search_args[arg] != "none":
                query += " " + arg + " = '" + search_args[arg] + "' AND"
            else: # search for empty field
                query += " " + arg + " is null AND"
        query = query[:-3] + "COLLATE NOCASE"

    print(query)
    try:
        cursor.execute(query)
        comments = cursor.fetchall()
    except:
        return 1
   
    if comments:
        comments = sorted(comments, key=lambda k: k['created'], reverse=True)
        for c in comments:
            c["created"]=datetime.fromtimestamp(c["created"])  # human readable date
            c["created"] = c["created"].strftime("%Y-%m-%d %H:%M")

        #print(comments)
        return comments
    else:
        return 2


def delete_comment(selected_comments):
    '''Delete the selected comments.
    selected_comments is the list of the id (PRIMARY KEYS)
    '''

    conn = connect_to_db()
    cursor = conn.cursor()
    selected_comments = tuple(selected_comments)
    query = "DELETE FROM comments WHERE id IN (" \
        + ",".join(["?"] * len(selected_comments)) + ")"
    cursor.execute(query, selected_comments)
    conn.commit()
    conn.close()
    return True


# ROUTES


@app.route('/')
@requires_auth
def home():
    return redirect(url_for("moderation"))


@app.route('/moderation', methods=['GET', 'POST'])
@requires_auth
def moderation():
    '''Default page. Display the comment depending on the search arguments
    '''

    if request.method == 'GET':
        search_args = {}
        for arg in request.args:
            if request.args[arg] and arg != 'submit':
                search_args[arg] = request.args[arg].lower()

    comments = print_comments(search_args)
    if comments == 1:
        return "Bad request"
    elif comments == 2:
        return "Nothing to display"
    else:
        return render_template('moderation.html', comments=comments)


@app.route('/delete', methods=['GET', 'POST'])
@requires_auth
def delete():
    '''Used for deleting comments.
    Receive a list of id and gives it to delete_comment()
    '''

    selected_comments = request.form.getlist('id')
    try:
        selected_comments = [ int(x) for x in selected_comments ]
    except:
        return "Error during suppression: bad request."

    #print(selected_comments)
    delete_comment(selected_comments)
    return redirect(url_for('moderation'))

if __name__ == '__main__':
    app.run(debug=True)
