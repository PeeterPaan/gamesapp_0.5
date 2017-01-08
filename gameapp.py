from flask import Flask, request, g, render_template, redirect, url_for, session, flash
import sqlite3 as sql
from wtforms import Form, TextField, PasswordField, validators, BooleanField
from passlib.hash import sha256_crypt
import flask_wtf
import gc
app = Flask(__name__)
app.secret_key = 'sikret ki'

DATABASE = '/Users/PeterPan/Documents/gameapp/userslist.db'


def database_command(command, *args):
    con = sql.connect('/Users/PeterPan/Documents/gameapp/userslist.db')
    cur = con.cursor()
    cur.execute(command, args)
    rows = cur.fetchall()
    con.commit()
    con.close()
    gc.collect()
    return rows


class user(object):
    def __init__(self, username, usertype):
        self.username = username
        self.type = usertype

def login_check():
    if session.get('logged_in'):
        user.username = session['username']
        user.type = database_command("select user_type from users WHERE username = ?", user.username)
        return True
    else:
        return False

class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min = 4, max = 20)])
    email = TextField('Email Address', [validators.Length(min = 6, max = 50)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message = 'Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the Terms of Service and Privacy Notice (updated Jan 22, 2015)',
                              [validators.Required()])

@app.route('/')

def home():

    return redirect('welcome')

@app.route('/welcome')
def tuna():
    posts = database_command("select * from posts")

    if session.get('logged_in'):
        login = session['username']
        user.username = session['username']
        user.type = database_command("select user_type from users WHERE username = ?", user.username)
        posts = database_command("select * from posts")
        return render_template("welcome.html", login = login, type = user.type[0][0], posts = posts)


    else:
        return render_template("welcome.html", posts = posts)


@app.route('/login', methods = ['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        con = sql.connect('/Users/PeterPan/Documents/gameapp/userslist.db')
        cur = con.cursor()

        cur.execute("SELECT password FROM users WHERE username= ?", (request.form['username'],))
        check_if_exists = cur.fetchall()

        if check_if_exists:

            if sha256_crypt.verify(request.form['password'], check_if_exists[0][0]):
                flash('You succesfully logged in, good job nygga')
                session['logged_in'] = True
                session['username'] = request.form['username']
                return redirect(url_for('table'))

            else:
                flash('Noooope')
                return render_template('login.html')
        else:
            flash('User doesnt exist')
            return render_template('login.html')

    return render_template('login.html', error=error, login=session['username'])


@app.route('/table')
def table():

    if session.get('logged_in'):
        rows = database_command("select * from games")

        return render_template("table.html", rows = rows, login = session['username'])
    else:
        flash('You are not logged in. Please log in to view rank')
        return redirect('welcome')
    print get_flashed_messages()

@app.route('/logout')
def logout():
    if session.get('logged_in'):
        session['logged_in'] = False
        flash('You succesfully logged out')

        return redirect('welcome')

    else:
        return redirect('welcome')



@app.route('/register', methods = ["GET", "POST"])

def register():
        form = RegistrationForm(request.form)

        if request.method == "POST" and form.validate:
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))

            con = sql.connect('/Users/PeterPan/Documents/gameapp/userslist.db')
            cur = con.cursor()
            cur.execute("select * from users where Username = ?", (username,))
            check_if_exists = cur.fetchall()

            if int(len(check_if_exists)) > 0:
                flash('User already exists')
                return render_template("register.html", form = form)

            else:

                cur.execute("insert into users (username, password, email) Values(?,?,?)", (username,password,email,))
                con.commit()
                flash('Succesfully reigstered, cocksucker.')
                con.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username
                return redirect('/welcome')

        return render_template("register.html", form = form)

@app.route('/whatulike', methods = ["GET", "POST"])

def whatulike():

    if session.get('logged_in'):
        rows = database_command("select * from games")
        return render_template("games_search.html", rows = rows, login=session['username'])
    else:
        flash('You are not logged in. Please log in to view this page')
        return redirect('welcome')

@app.route('/postit', methods = ["GET","POST"])
def post_it():
    if request.method == "POST" and login_check():
        title = request.form['title']
        content = request.form["content"]
        database_command("insert into posts (post_title, post_content, post_writer) values (?,?,?)", *(title, content,
                                                                                                    user.username,))
        return redirect('/welcome')

    elif login_check():
        return render_template("postit.html")


    else:
        return redirect("login")




if __name__ == "__main__":
    app.run(host = '0.0.0.0', debug = True)