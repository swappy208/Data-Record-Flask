from flask import Flask, render_template
from data import Articles
# create an instance of flask
app = Flask(__name__)

thearticles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html', articles = thearticles)

@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id = id)


if __name__ == '__main__':
    app.run(debug=True)

