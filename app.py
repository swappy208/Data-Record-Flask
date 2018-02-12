from flask import Flask, render_template, flash, redirect, session, url_for, logging, request
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

# create an instance of flask
app = Flask(__name__)

# config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Abcd<1234'
app.config['MYSQL_DB'] = 'datarecordapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize MySQL
mysql = MySQL(app)

# UNREQUIRED: thearticles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
     # create cursor
    cur = mysql.connection.cursor()

    #get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result>0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('articles.html', msg=msg)
    #close connection
    cur.close()

@app.route('/article/<string:id>/')
def article(id):
     # create cursor
    cur = mysql.connection.cursor()

    #get articles
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()


    return render_template('article.html', article = article)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=100)])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message = 'Passwords do not match')])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # save to db
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('index'))
    return render_template('register.html', form = form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        #Create Cursor
        cur = mysql.connection.cursor()

        # User by Username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            # Compare passwords
            if sha256_crypt.verify(password_candidate, password):
                app.logger.info('PASSWORD MATCHED')
                session['logged_in'] = True
                session['username'] = username
                session['name'] = data['name']

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error='Invalid Login'
                app.logger.info('PASSWORD NOT MATCHED')
                return render_template('login.html', error=error)
            cur.close()
        else:
            app.logger.info('NO USER')
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')

#check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login to Enter', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/dashboard')
@is_logged_in
def dashboard():
    # create cursor
    cur = mysql.connection.cursor()

    #get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result>0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html', msg=msg)
    #close connection
    cur.close()

#article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=255)])
    body = TextAreaField('Body', [validators.Length(min=30)])

@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s,%s,%s)", (title, body, session['username']))
        mysql.connection.commit()
        cur.close()
        flash('Article successfully created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)

