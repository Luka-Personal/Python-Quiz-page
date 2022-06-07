import random
import re

import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, UserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = "BTU"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)
email_regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, autoincrement=True ,primary_key=True)
    nickname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)


db.create_all()

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def validate_data(nickname, email, pass1, pass2):
    valid = True

    if len(nickname) < 3:
        flash('Nickname Must Be At Least 3 Characters', category='error')
        valid = False
    if not re.search(email_regex, email):
        flash('Enter A Valid Email', category='error')
        valid = False
    user = User.query.filter_by(email=email).first()
    if user:
        flash('Email Already Used', category='error')
        valid = False
    if len(pass1) < 3:
        flash('Password Must Be At Least 3 Characters', category='error')
        valid = False
    if pass1 != pass2:
        flash('Passwords Don\'t Match', category='error')
        valid = False
    return valid


@app.route('/')
def home():
    return render_template('home.html', user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('home'))
            else:
                flash('Incorrect password', category='error')
        else:
            flash('No User With This Email', category='error')

    return render_template("login.html", user=current_user)


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == "POST":
        email = request.form.get('email')
        nickname = request.form.get('nickname')
        password1 = request.form.get('password')
        password2 = request.form.get('repeat-password')

        if validate_data(nickname, email, password1, password2):
            password = generate_password_hash(password1)
            user = User(nickname=nickname, email=email, password=password)
            db.session.add(user)
            login_user(user, remember=True)
            flash('Registered Successfully!', category='success')
            return redirect(url_for("home"))
        else:
            return redirect(url_for('register'))
    return render_template('register.html', user=current_user)


@app.route('/meme')
def meme():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    res = requests.get('https://api.imgflip.com/get_memes')
    raw_memes = res.json()
    random_meme = random.choice(raw_memes['data']['memes'])
    return render_template('meme.html', user=current_user, url=random_meme['url'])


@app.route('/quote')
def quote():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    content = requests.get(f'https://quotes.toscrape.com/random')
    bs = BeautifulSoup(content.text, 'html.parser')
    quote_block = bs.find('div', class_='quote')
    quote_dict = {'quote': quote_block.find('span', class_='text').text,
                  'author': quote_block.find('small', class_='author').text}
    return render_template('quote.html', user=current_user, quote=quote_dict)


if __name__ == "__main__":
    app.run(debug=True)
