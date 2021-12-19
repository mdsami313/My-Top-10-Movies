from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

API = "13044671ed2f0dc961c95ccbeb2795a1"

MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
Bootstrap(app)
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)
db.create_all()

class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")

class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()   
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)

@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movies = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movies.rating = float(form.rating.data)
        movies.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movies, form=form)

@app.route("/delete", methods=["GET", "POST"])
def delete_movie():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if request.method == "GET":
        db.session.delete(movie)
        db.session.commit()
    return redirect(url_for('home'))

@app.route("/add-movie", methods=["GET", "POSt"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_name = form.title.data
        query = movie_name
        response = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={API}&query={query}").json()
        movies = response['results']
        return render_template("select.html", movies=movies)
    return render_template("add.html", form=form)

@app.route("/find", methods=["GET", "POST"])
def find_movie():
    movie_api_id = request.args.get("movie_id")
    print(movie_api_id)
    movie_api_description = request.args.get("movie_description")
    if movie_api_id:     
        #The language parameter is optional, if you were making the website for a different audience 
        #e.g. Hindi speakers then you might choose "hi-IN"
        response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_api_id}?api_key={API}")
        data = response.json()
        new_movie = Movie(
            title=data["original_title"],
            #The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=movie_api_description
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))

if __name__ == "__main__":
    app.run(debug=True)
