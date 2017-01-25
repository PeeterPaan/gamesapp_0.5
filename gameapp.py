from flask import Flask, request, g, render_template, redirect, url_for, session, flash, jsonify
import sqlite3 as sql
from wtforms import Form, TextField, PasswordField, validators, BooleanField
from passlib.hash import sha256_crypt
import flask_wtf
import gc
app = Flask(__name__)
app.secret_key = 'sikret ki'

DATABASE = '/Users/PeterPan/Documents/gameapp/userslist.db'


def database_command(command, *args): #*Args are to let assign optional arguments
    con = sql.connect('/Users/PeterPan/Documents/gameapp/userslist.db') # Establishing a connection with DB
    cur = con.cursor()
    cur.execute(command, args)
    rows = cur.fetchall() #Create a variable containing a DISCTIONARY with all data from command
    con.commit() # Save changes made to the DB
    con.close() # Close connection
    gc.collect() # Save memory
    return rows



class user(object):
    def __init__(self, username, usertype): # Not sure yet if helpful, moslty to determine if admin or not
        self.username = username
        self.type = usertype

def login_check(): # Function to call whenever checking if user is logged in
    if session.get('logged_in'): # If logged in
        user.username = session['username'] # Assign username to class user
        user.type = database_command("select user_type from users WHERE username = ?", user.username) #Assign user type by checking in DB
        return True
    else:
        return False

class RegistrationForm(Form): # All the rules by which registration works
    username = TextField('Username', [validators.Length(min = 4, max = 20)])
    email = TextField('Email Address', [validators.Length(min = 6, max = 50)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message = 'Passwords must match')
    ])
    confirm = PasswordField('Repeat Password') # Check if passwords match
    accept_tos = BooleanField('I accept the Terms of Service and Privacy Notice (updated Jan 22, 2015)',
                              [validators.Required()])

@app.route('/')

def home():

    return redirect('welcome')

@app.route('/welcome')
def tuna():
    posts = database_command("select * from posts")  # Load posts from DB

    if session.get('logged_in'): # Check if logged in
        login = session['username'] # Assign variable to username - It happened before creating user class and is too deeply in to correct now
        user.username = session['username'] # Oh, here I created the class
        user.type = database_command("select user_type from users WHERE username = ?", user.username) # And used it to check user's type
        posts = database_command("select * from posts") # Load posts from DB
        return render_template("welcome.html", login = login, type = user.type[0][0], posts = posts) # Pass variables to HTML


    else: #If not logged in
        return render_template("welcome.html", posts = posts)


@app.route('/login', methods = ['GET', 'POST']) # Login page - post method to let it pass information to server
def login():
    error = None
    if request.method == 'POST': # Check if correct method
        con = sql.connect('/Users/PeterPan/Documents/gameapp/userslist.db') #Before database_command
        cur = con.cursor() #Before database_command

        cur.execute("SELECT password FROM users WHERE username= ?", (request.form['username'],)) #If user exists, get password
        check_if_exists = cur.fetchall()

        if check_if_exists:

            if sha256_crypt.verify(request.form['password'], check_if_exists[0][0]): # Check hashed password
                flash('You succesfully logged in, good job nygga')
                session['logged_in'] = True # Change session status
                session['username'] = request.form['username'] # Assign username to session name
                return redirect(url_for('tuna')) # Redirect to the front page

            else:
                flash('Wrong password') # If paasword incorrect, try again
                return render_template('login.html')
        else:
            flash('User doesnt exist') # If User doesn't exist
            return render_template('login.html')
    return render_template('login.html', error=error)



@app.route('/table')
def table():

    if session.get('logged_in'):
        rows = database_command("select * from games") # Select all games and make a dictionary out of them

        return render_template("table.html", rows = rows, login = session['username']) # pass all to HTML
    else: # If not logged in
        flash('You are not logged in. Please log in to view rank')
        return redirect('welcome')
    print get_flashed_messages() # just testing I guess

@app.route('/logout')
def logout(): # Self explainatory
    if session.get('logged_in'):
        session['logged_in'] = False
        flash('You succesfully logged out')

        return redirect('welcome')

    else:
        return redirect('welcome')



@app.route('/register', methods = ["GET", "POST"])

def register():
        form = RegistrationForm(request.form) # Assign form information to RegistrationForm class

        if request.method == "POST" and form.validate:
            username = form.username.data # username is what user writes in HTML form with name username
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data))) # Hash the password

            con = sql.connect('/Users/PeterPan/Documents/gameapp/userslist.db') # Before database_command
            cur = con.cursor()
            cur.execute("select * from users where Username = ?", (username,))
            check_if_exists = cur.fetchall() # get all users with this username

            if int(len(check_if_exists)) > 0: # Check if anything got fetched = it would mean, that user already exists
                flash('User already exists')
                return render_template("register.html", form = form)

            else: # If doesn't yet exist

                cur.execute("insert into users (username, password, email) Values(?,?,?)", (username,password,email,))
                                                                                                # Create the user
                con.commit()
                flash('Succesfully reigstered, cocksucker.')
                con.close()
                gc.collect()

                session['logged_in'] = True # Log him in after registration
                session['username'] = username
                return redirect('/welcome')

        return render_template("register.html", form = form)
@app.route('/whatulike/', methods = ["GET", "POST"])
@app.route('/whatulike/<int:page>', methods = ["GET", "POST"])

def whatulike(page=1):

    if session.get('logged_in'):
        pages_number = database_command("select * from games")
        rows = database_command("select * from games limit 21 offset ?", page) # all games
        userid = database_command("""select user_id from users where username=?""", session['username']) # Get user id
        user_rating = database_command("""select games.title, usersgames.rating from games join usersgames on game_id =
                                        usersgames.game_title and usersgames.username=?""", userid[0][0]) # Get all
                                                                    # ratings of this user for all games that he rated

        for row in rows: # For every game
            newrating = []
            newrating.append(request.form.get(row[1])) # Get user's rating from form with name of that game
                                                        # ( name specified in HTML as game title )
            if newrating != None and request.method == "POST": # Not sure actually if still necessary

                for rating in newrating: # For every new rating that user gave on HTML ( can be multiple )
                    database_command("""INSERT INTO usersgames (username, game_title, rating)
                                      SELECT ?, ?, ? where not EXISTS
                                      (SELECT * from usersgames where username = ? and game_title = ?)"""
                                     , userid[0][0], row[0], rating, userid[0][0], row[0]) # If user didnt yet rate
                                                                                # this game, create new database entry
                    database_command(
                        """update usersgames set rating = ? where username = ? and game_title = ? and rating != ?""",
                        rating, userid[0][0], row[0], rating) # If user already rated that game, and now only changes the rating, update the DB

            else:
                return render_template("games_search.html", rows = rows, login=session['username'],
                                       user_rating = user_rating, pages_number=len(pages_number)/20)
        return redirect('whatulike')

    else:
        flash('You are not logged in. Please log in to view this page')
        return redirect('welcome')

@app.route('/postit', methods = ["GET","POST"])
def post_it():
    if request.method == "POST" and login_check(): # Ohh that's actually no good - not checking if user is an admin
        title = request.form['title']
        content = request.form["content"] # Get from HTML
        database_command("insert into posts (post_title, post_content, post_writer) values (?,?,?)", *(title, content,
                                                                                                    user.username,)) # Create new database entry

        return redirect('/welcome')

    elif login_check():
        return render_template("postit.html")


    else:
        return redirect("login")

@app.route('/user/<nickname>') # create a profile page

def user(nickname):
    if login_check():
        user = database_command("select * from users where username = ?", nickname) # Get user data from DB
        if user is None: # If no data from database, it means that there is no user with that username
            flash('User %s not found.' % nickname)
            return redirect(url_for('tuna'))

        return render_template('user.html',
                               username=nickname, avatar=user[0][5], email = user[0][3]) # Pass avatar, and email to HTML
    else:
        flash("Please log in to view user page")
        return redirect('/welcome')
@app.route('/post/<post_name>')

def post(post_name):
    article = database_command("select * from posts where post_title=?", post_name)

    return render_template('post.html', post = post_name, article = article, login=session['username'])




if __name__ == "__main__":
    app.run(host = '0.0.0.0', debug = True)