import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_reviews")
def get_reviews():
    """
    This function allows the user to retrieve the reviews from the db and render it
    into the the respective html file
    """
    reviews = list(mongo.db.reviews.find())
    return render_template("reviews.html", reviews=reviews)
    

@app.route("/search", methods=["GET", "POST"])
def search():
    """
    This function enables the functionality of the search bar provided
    on the reviews main page. 
    It searches for the key words within the db and retrives all the results 
    with the correspondent keys onto the html template. 
    """
    # enables search for reviews within the db
    query = request.form.get("query")
    reviews = list(mongo.db.reviews.find({"$text": {"$search": query}}))
    return render_template("reviews.html", reviews=reviews)


@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    """
    This function is used for registration process.
    First, it checks if the username is already in use in db.
    If so, it will display a message telling the new user that this particular
    user name already exists, and if not the new user will register successfully
    and will be added to the db.

    The new user is also put into a 'session' cookie whenever logged in. 
    When logged out, the user 'session' cookie will end as well until logged in again.
    """
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("sign_up"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("sign_up.html")



@app.route("/sign_in", methods=["GET", "POST"])
def sign_in():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("sign_in"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("sign_in"))

    return render_template("sign_in.html")


@app.route("/profile/", methods=["GET", "POST"])
def profile():
    if session["user"]:
        return render_template("profile.html", username=session["user"])

    return redirect(url_for("sign_in"))


@app.route("/sign_out")
def sign_out():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("sign_in"))


@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    if request.method == "POST":
        reviews = {
            "genre_type": request.form.get("genre_type"),
            "game_reviewed": request.form.get("game_reviewed"),
            "review_description": request.form.get("review_description"),
            "review_post_date": request.form.get("review_post_date"),
            "created_by": session["user"]
        }
        mongo.db.reviews.insert_one(reviews)
        flash("Review Added Successfully")
        return redirect(url_for("add_review"))

    genres = mongo.db.genres.find().sort("genre_type", 1)
    return render_template("add_review.html", genres=genres)


@app.route("/review/<review_id>", methods=["GET", "POST"])
def review_detail(review_id):
    review = mongo.db.reviews.find_one_or_404({"_id": ObjectId(review_id)})
    genres = mongo.db.genres.find().sort("genre_type", 1)
    return render_template("review_detail.html", review=review, genres=genres)


@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if 'user' not in session:
        return redirect(url_for('sign_in'))
    review = mongo.db.reviews.find_one_or_404(
        {"_id": ObjectId(review_id), "created_by": session["user"]}
    )
    if request.method == "POST":
        submit = {  
            "genre_type": request.form.get("genre_type"),
            "game_reviewed": request.form.get("game_reviewed"),
            "review_description": request.form.get("review_description"),
            "review_post_date": request.form.get("review_post_date"),
            "created_by": session["user"]
        }
        mongo.db.reviews.update({"_id": ObjectId(review_id)}, submit)
        flash("Review Updated Successfully")

    genres = mongo.db.genres.find().sort("genre_type", 1)
    return render_template("edit_review.html", review=review, genres=genres)


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    review = mongo.db.review.find_one(
        {"_id": ObjectId(review_id)})
    if review['created_by'] == session["user"]:
        mongo.db.reviews.remove({"_id": ObjectId(review_id)})
        flash("Review Deleted Successfully")
    return redirect(url_for("get_reviews"))

    
@app.route("/add_genres")
def add_genres():
    genres = list(mongo.db.genres.find().sort("genre_type", 1))
    return render_template("genres.html", genres=genres)


@app.route("/add_genre", methods=["GET", "POST"])
def add_genre():
    if request.method == "POST":
        genre = {
            "genre_type": request.form.get("genre_type")
        }
        mongo.db.genres.insert_one(genre)
        flash("New Game Genre Added")
        return redirect(url_for("add_genres"))

    return render_template("add_genre.html")


@app.route("/edit_genre/<genre_id>", methods=["GET", "POST"])
def edit_genre(genre_id):
    if request.method == "POST":
        submit = {
            "genre_type": request.form.get("genre_type")
        }
        mongo.db.genres.update({"_id": ObjectId(genre_id)}, submit)
        flash("Genre Successfully Updated")
        return redirect(url_for("add_genres"))

    genre = mongo.db.genres.find_one({"_id": ObjectId(genre_id)})
    return render_template("edit_genre.html", genre=genre)


@app.route("/delete_genre/<genre_id>")
def delete_genre(genre_id):
    mongo.db.genres.remove({"_id": ObjectId(genre_id)})
    flash("Genre Successfully Deleted")
    return redirect(url_for("add_genres"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
