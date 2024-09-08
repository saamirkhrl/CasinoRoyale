# imports and the libraris needed
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_required, LoginManager, login_user, logout_user, current_user
from wtforms.validators import DataRequired, Length
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import random

# set up the app and db
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = '8578954739847593875938759835798357983776927498274987396573068398547982462947205870385789547398475938759387598357983579837769274982749873965730683985479824629472058703'
db = SQLAlchemy(app)

# login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)

# user database
class User(db.Model, UserMixin):
     id = db.Column(db.Integer, primary_key=True)
     username = db.Column(db.String, unique=True, nullable=False)
     password = db.Column(db.String, nullable=False)
     balance = db.Column(db.Integer, default=1500)
     about = db.Column(db.String(150))
     account_created = db.Column(db.String)

     def __repr__(self):
          return f'ID: {self.id}, Username: {self.username}, Balance: {self.balance}, Password: {self.password}, About: {self.about}, account_created: {self.account_created}'

# recent database
class RecentActivities(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resultgame = db.Column(db.Boolean)
    username = db.Column(db.String)
    desc = db.Column(db.String)
    amount = db.Column(db.String)
    date = db.Column(db.String)

    def __repr__(self):
        return f'Username: {self.username}, Description: {self.desc}, Date: {self.date}, Amount: {self.amount}, Result: {self.resultgame}'

# login/register form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={"placeholder": "Enter your username ..."})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Enter your password ..."})
    submit = SubmitField('Log in')

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={"placeholder": "Choose a username ..."})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Choose a password ..."})
    password2 = PasswordField('Confirm your password', validators=[DataRequired()], render_kw={"placeholder": "Re-type your password ..."})
    submit = SubmitField('Sign up')

# editing about page 
class EditAbout(FlaskForm):
    about = StringField('Write about yourself...')

# user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# home route and logics
@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    user = User.query.get(current_user.id)
    recent_activites = RecentActivities.query.order_by(RecentActivities.id.desc()).all()
    editabout = EditAbout()
    if request.method == 'POST':
        new_about = request.form.get('about')
        if len(new_about) > 150:
            flash('About is too long, could not update', 'danger')
        else:
            user.about = new_about
            db.session.commit()
            flash('Updated your about!', 'success')
        return redirect(url_for('home'))
    return render_template('home.html', user=user, ediabout=editabout, recent_activites=recent_activites)

# about page and logics
@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')

# login route and logic
@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm() 
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Username does not exist. Try again?','danger')
        elif not check_password_hash(user.password, password):
            flash('Wrong username, try again.','danger')
        else:
            login_user(user)
            flash('Logged in succesfully!','success')
            return redirect(url_for('home'))
    return render_template('login.html', form=form)

# register route and logic
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = SignUpForm()
    if request.method == 'POST':
        username = request.form.get('username')
        password1 = request.form.get('password')
        password2 = request.form.get('password2')

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists, choose another one','danger')
        elif password1 != password2:
            flash('Both passwords must match','danger')
        else:
            hashed_password = generate_password_hash(password1)
            now = datetime.datetime.now()
            date = now.day
            month = now.month
            year = now.year
            new_user = User(username=username, balance=1500, password=hashed_password, about='No about yet.', account_created=f'{month}/{date}/{year}')
            db.session.add(new_user)
            db.session.commit()
            flash('Account created and redirecting to login now.','success')
            return redirect(url_for('login'))

    return render_template('register.html', form=form)

# leaderboard route and logic
@app.route('/leaderboard', methods=['POST', 'GET'])
def leaderboard():
    top_users = User.query.order_by(User.balance.desc()).all()
    return render_template('leaderboard.html', top_users=top_users)

# profile route and logic
@app.route('/profile/<int:user_id>', methods=['POST', 'GET'])
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)

# logging out
@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out','success')
    return redirect(url_for('login'))

# heads or tails game
@app.route('/games/headsortails', methods=['GET', 'POST'])
@login_required
def headstailsgame():
    user = User.query.get(current_user.id)
    if request.method == 'POST':
        now = datetime.datetime.now()
        date = now.day
        month = now.month
        year = now.year
        betAmount = request.form.get('bet')
        coin_face = request.form.get('coin_face')
        if user.balance < float(betAmount):
            flash('You cannot bet more than you have', 'danger')
        elif float(betAmount) <= 0:
            flash('You cannot bet less than or equal to 0')
        else:
            result = 'heads' if random.randint(0, 1) == 0 else 'tails'
            if coin_face == result:
                user.balance += float(betAmount)  
                recent = RecentActivities(username=user.username, desc='won Head or Tails', date=f'{month}/{date}/{year}', amount=betAmount, resultgame=True)
                db.session.add(recent)
                db.session.commit()
                flash(f'The coin landed on {result}! You won {betAmount}', 'success')
            else:
                user.balance -= float(betAmount) 
                recent = RecentActivities(username=user.username, desc='lost Head or Tails', date=f'{month}/{date}/{year}', amount=betAmount, resultgame=False)
                db.session.add(recent)
                db.session.commit()
                flash(f'The coin landed on {result}! You lost {betAmount}', 'danger')

            return redirect(url_for('headstailsgame'))
    
    return render_template('heads_tails.html', user=user)

# dice game and logics
@app.route('/games/dice', methods=['GET', 'POST'])
def dice():
    user = User.query.get(current_user.id)
    if request.method == 'POST':
        now = datetime.datetime.now()
        date = now.day
        month = now.month
        year = now.year
        bet_amount = float(request.form.get('bet'))
        face = request.form.get('dice_number')
        if bet_amount > user.balance:
            flash('You cannot bet more than you have','danger')
        else:
            random_number = random.randint(1, 6)
            result = 'win' if random_number == int(face) else 'lose' 
            if result == 'win':
                user.balance += float(bet_amount) 
                recent = RecentActivities(username=user.username, desc='won Dice', date=f'{month}/{date}/{year}', amount=bet_amount, resultgame=True)
                db.session.add(recent)
                db.session.commit()
                flash(f'You WON {bet_amount}! Dice landed on {random_number}, and you chose {face}', 'success')
            else:
                user.balance -= float(bet_amount)  
                recent = RecentActivities(username=user.username, desc='lost Dice', date=f'{month}/{date}/{year}', amount=bet_amount, resultgame=False)
                db.session.add(recent)
                db.session.commit()
                flash(f'You LOST {bet_amount}. Dice landed on {random_number}, and you chose {face}', 'danger')

        return redirect(url_for('dice'))

    return render_template('dice.html', user=user)

# transfer funds logics and route
@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    user = User.query.get(current_user.id)
    if request.method == 'POST':
        recipient = User.query.filter_by(username=request.form.get('recipient')).first()
        password = request.form.get('password')
        transfer_amount = float(request.form.get('amount'))
        if transfer_amount > user.balance:
            flash('You cannot give transfer more than you have', 'danger')
            return redirect(url_for('transfer'))
        elif not recipient:
            flash('That user does not exist. Usernames are case sensitive', 'danger')
            return redirect(url_for('transfer'))
        elif not check_password_hash(user.password, password):
            flash('Wrong password, try again', 'danger')
            return redirect(url_for('transfer'))
        else:
            user.balance -= float(transfer_amount) 
            recipient.balance += float(transfer_amount)  
            db.session.commit()
            flash(f'Successfully transferred {transfer_amount} to {recipient.username}', 'success')
            return redirect(url_for('transfer'))

    return render_template('transfer.html', user=user)

# creating the db and running the app
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
