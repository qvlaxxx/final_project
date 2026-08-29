from email.mime import image

from flask import Flask, render_template, g, request, redirect, url_for, session
from sqlalchemy import create_engine, String, Float, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker, DeclarativeBase
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Будь ласка, увійдіть, щоб отримати доступ до цієї сторінки.'

app = Flask(__name__)
login_manager.init_app(app)
app.secret_key = "dev-secret-key-123"
PG_USER = "postgres"
PG_PASSWORD = "123"
PG_DBNAME = "restoraunt"

engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@localhost:5432/{PG_DBNAME}", echo=False)
Session = sessionmaker(bind=engine)

@login_manager.user_loader
def load_user(user_id):
    db = Session()
    user = db.get(User, int(user_id))
    db.close()
    return user

class Base(DeclarativeBase):
    def create_db(self):
        Base.metadata.create_all(engine)

    def drop_db(self):
        Base.metadata.drop_all(engine)

class User(Base,UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)

class Menu(Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(300), nullable=True)
    price: Mapped[float] = mapped_column(Float)
    image: Mapped[str] = mapped_column(String(200), nullable=True)

class Basket(Base):
    __tablename__ = "basket"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))

@app.route("/")
def home():  
    return render_template("home.html")

@app.route("/menu")
@login_required
def menu():

    db = Session()
    dishes = db.query(Menu).all()
    db.close()

    return render_template("menu.html", dishes=dishes)


@app.route("/basket")
@login_required
def basket():

    basket_ids = session.get("basket", [])

    db = Session()
    dishes = db.query(Menu).filter(Menu.id.in_(basket_ids)).all()
    db.close()

    return render_template("basket.html", dishes=dishes)


@app.route("/basket/add", methods=["POST"])
def add_to_basket():
    dish_id = request.form.get("dish_id")

    basket = session.get("basket", [])
    basket.append(dish_id)
    session["basket"] = basket

    return redirect(url_for("basket"))

@app.route("/basket/del", methods=["POST"])
def delete_to_basket():
    dish_id = request.form.get("dish_id")
    if dish_id in session.get("basket", []):
        session["basket"].remove(dish_id)
    else:
        return redirect(url_for("error_basket_noy_products"))
    return redirect(url_for("basket"))


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

    login_user(user)
    return redirect(url_for("menu"))

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Очищає сесію користувача
    return redirect(url_for('login'))

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

    login_user(new_user)
    db.close()
    
    return redirect(url_for("menu"))

if __name__ == '__main__':
    Base.metadata.create_all(engine)

    db = Session()
    if not db.query(Menu).first():
        db.add_all([
            Menu(name="Сирний вибух", description="класична піца з томатами й моцарелою,"
                                                  " а бортик фарширований потрійним сиром "
                                                  "(моцарела, чеддер, пармезан),"
                                                  " який тягнеться при розрізанні.", price=220.0, image="image1.jpg"),
            Menu(name="Мед і перець", description="піца з пеппероні та руколою,"
                                                  " бортик покритий тонким шаром "
                                                  "меду з чорним перцем — солодко-гострий контраст.", price=240.0,
                 image="image2.jpg"),
            Menu(name="Часниковий бургер-бортик", description="бортик фарширований часниковим маслом"
                                                              " і посипаний пармезаном та зеленню,"
                                                              " під нього — піца з беконом і карамелізованою цибулею.",
                 price=250.0, image="image3.jpg"),
            Menu(name="Шоколадна Межа", description="на десертній піці з бананом і горіхами бортик"
                                                    " обмазаний розтопленим темним шоколадом"
                                                    " і посипаний кокосовою стружкою.", price=200.0,
                  image="image4.jpg"),
            Menu(name="Огняний краєчок", description="гострий бортик з халапеньйо та сирним соусом чіпотле,"
                                                     " під ним — піца з куркою-барбекю та червоною цибулею.",
                 price=260.0, image="image5.jpg"),
        ])
        db.commit()
    db.close()

    app.run(debug=True)
    