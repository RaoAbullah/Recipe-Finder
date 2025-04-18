from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import requests

app = Flask("RecipeFinder")
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

API_KEY = 'd010db4503814e108c4e9b93e3248b74'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipe_id = db.Column(db.Integer)
    title = db.Column(db.String(255))
    image_url = db.Column(db.String(255))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    url = f"https://api.spoonacular.com/recipes/complexSearch?query={query}&apiKey={API_KEY}&number=12"
    response = requests.get(url)
    data = response.json()
    recipes = data.get('results', [])
    return render_template('search_results.html', recipes=recipes)

@app.route('/suggest', methods=['POST'])
def suggest():
    ingredients = request.form['ingredients']
    url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients}&apiKey={API_KEY}&number=12"
    response = requests.get(url)
    data = response.json()
    return render_template('results.html', recipes=data)

@app.route('/favorites')
@login_required
def view_favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    return render_template('favorites.html', favorites=favorites)

@app.route('/save_favorite/<int:recipe_id>')
@login_required
def save_favorite(recipe_id):
    title = request.args.get('recipe_title')
    image_url = request.args.get('image_url')
    existing = Favorite.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    if not existing:
        new_fav = Favorite(user_id=current_user.id, recipe_id=recipe_id, title=title, image_url=image_url)
        db.session.add(new_fav)
        db.session.commit()
    return redirect(url_for('view_favorites'))

@app.route('/remove_favorite/<int:recipe_id>', methods=['POST'])
@login_required
def remove_favorite(recipe_id):
    favorite = Favorite.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
    return redirect(url_for('view_favorites'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)