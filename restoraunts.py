from flask import Flask, render_template, g, request, redirect, url_for, session
from sqlalchemy import create_engine, String, Float, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker, DeclarativeBase

app = Flask(__name__)
PG_USER = "qvlax"
PG_PASSWORD = "123"
PG_DBNAME = "restoraunt"

engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@localhost:5432/{PG_DBNAME}", echo=False)
Session = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    def create_db(self):
        Base.metadata.create_all(engine)

    def drop_db(self):
        Base.metadata.drop_all(engine)

@app.route("/")
def home():  
    return render_template("home.html")

@app.route("/menu")
def menu():
    return render_template("menu.html")

@app.route("/basket")
def basket():
    return render_template("basket.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
        
    username = request.form.get("username")
    password = request.form.get("password")
    
    db = Session()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    
    if not user:
        return "User is not registered "
    if password != user.password:
        return "Wrong password "
    
    session['user_id'] = user.id
    session['username'] = user.username
    return redirect(url_for("home")) 

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
        
    username = request.form.get("username")
    password = request.form.get("password")
    
    db = Session() 
    user_exists = db.query(User).filter(User.username == username).first()
    
    if user_exists:
        db.close()
        return "такий нікнейм вже існує"
    
    new_user = User(username=username, password=password)
    db.add(new_user)
    db.commit()
    
    session['user_id'] = new_user.id
    session['username'] = new_user.username
    db.close()
    
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True)
    