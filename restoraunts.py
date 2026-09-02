from email.mime import image

from flask import Flask, render_template, g, request, redirect, url_for, session
from sqlalchemy import create_engine, String, Float, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker, DeclarativeBase
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import secrets
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
    active: Mapped[bool] = mapped_column(Boolean)
    details_description: Mapped[str] = mapped_column(String(500), nullable=True)

class Basket(Base):
    __tablename__ = "basket"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))

class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    sum:  Mapped[float] = mapped_column(Float)

@app.route("/")
def home():  
    return render_template("home.html")

@app.route("/menu")
@login_required
def menu():
    db = Session()
    dishes = db.query(Menu).filter(Menu.active == True).all()
    db.close()

    return render_template("menu.html", dishes=dishes)

@app.route("/error_basket_noy_products")
def error_basket_noy_products():
    return render_template("error_basket_noy_products.html")


@app.route("/basket")
@login_required
def basket():

    basket_ids = session.get("basket", [])

    db = Session()
    dishes = db.query(Menu).filter(Menu.id.in_(basket_ids)).all()
    db.close()

    return render_template("basket.html", dishes=dishes)



@app.route("/orders")
def orders():
    orders_ids = session.get("orders", [])
    db = Session()
    dishes = db.query(Menu).filter(Menu.id.in_(orders_ids)).all()
    db.close()

@app.route("/order/create", methods=["POST"])
def create_order():
    basket_ids = session.get("basket", [])
    session["orders"] = basket_ids
    session["basket"] = []
    return redirect(url_for("orders"))

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
        session.modified = True
    else:
        return redirect(url_for("error_basket_noy_products"))
    return redirect(url_for("basket"))

@app.route("/details_dishes/<dish_id>")
def details_dishes(dish_id):
    db = Session()
    dish = db.get(Menu, int(dish_id))
    db.close()
    return render_template("details_dishes.html", dishes=dish)


@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route('/menu_check', methods=['GET', 'POST'])
@login_required
def menu_check():
    if current_user.username != 'Admin':
        return redirect(url_for('home'))

    if request.method == 'POST':
        if request.form.get("csrf_token") != session['csrf_token']:
            return "Запит заблоковано!", 403

        position_id = request.form['pos_id']
        with Session() as cursor:
            position_obj = cursor.query(Menu).filter_by(id=position_id).first()
            if 'change_status' in request.form:
                position_obj.active = not position_obj.active
            elif 'delete_position' in request.form:
                cursor.delete(position_obj)
            cursor.commit()

    with Session() as cursor:
        all_positions = cursor.query(Menu).all()
    return render_template('check_menu.html', all_positions=all_positions, csrf_token=session["csrf_token"])

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
    session['csrf_token'] = secrets.token_hex(16)
    return redirect(url_for("menu"))

@app.route('/logout')
@login_required
def logout():
    logout_user()
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
                                                  " який тягнеться при розрізанні.", price=220.0, image="image1.jpg",
                 active=True,
                 details_description="Класична нью-йоркська основа з насиченим томатним соусом і подвійною моцарелою, "
                                     "а вздовж усього бортика — потрійна сирна начинка з моцарели, чеддеру та пармезану, "
                                     "яка тягнеться довгими нитками при кожному відкушуванні. Ідеальний вибір для тих, "
                                     "хто любить, коли сиру багато. Вага: 480 г · Калорійність: 1120 ккал"),
            Menu(name="Мед і перець", description="піца з пеппероні та руколою,"
                                                  " бортик покритий тонким шаром "
                                                  "меду з чорним перцем — солодко-гострий контраст.", price=240.0,
                 image="image2.jpg", active=True,
                 details_description="Гостра пепероні та свіжа рукола на щільній основі створюють насичений смаковий "
                                     "контраст, а тонкий шар меду з чорним перцем уздовж бортика додає несподівану "
                                     "солодко-пряну нотку. Ця піца — для тих, хто любить грати на контрастах смаку "
                                     "в одній страві. Вага: 460 г · Калорійність: 1050 ккал"),
            Menu(name="Часниковий бургер-бортик", description="бортик фарширований часниковим маслом"
                                                              " і посипаний пармезаном та зеленню,"
                                                              " під нього — піца з беконом і карамелізованою цибулею.",
                 price=250.0, image="image3.jpg", active=True,
                 details_description="Бортик, щедро фарширований ароматним часниковим маслом і посипаний пармезаном "
                                     "та свіжою зеленню, перетворює звичну піцу на щось середнє між піцою і бургером. "
                                     "Під ним ховається соковита начинка з хрусткого бекону та карамелізованої цибулі, "
                                     "що додає легку солодкість. Вага: 510 г · Калорійність: 1240 ккал"),
            Menu(name="Шоколадна Межа", description="на десертній піці з бананом і горіхами бортик"
                                                    " обмазаний розтопленим темним шоколадом"
                                                    " і посипаний кокосовою стружкою.", price=200.0,
                 image="image4.jpg", active=True,
                 details_description="Десертна піца для справжніх солодкоежок: м'яке тісто з шматочками банана "
                                     "та горіхів, а бортик щедро обмазаний розтопленим темним шоколадом і посипаний "
                                     "кокосовою стружкою. Чудовий варіант, щоб завершити вечерю чимось незвичним. "
                                     "Вага: 420 г · Калорійність: 1180 ккал"),
            Menu(name="Огняний краєчок", description="гострий бортик з халапеньйо та сирним соусом чіпотле,"
                                                     " під ним — піца з куркою-барбекю та червоною цибулею.",
                 price=260.0, image="image5.jpg", active=True,
                 details_description="Для любителів гострого: бортик з халапеньйо та насиченим сирним соусом чіпотле "
                                     "обрамляє піцу з ніжною куркою барбекю та хрусткою червоною цибулею. Пікантний "
                                     "присмак чіпотле відчувається в кожному шматочку. "
                                     "Вага: 470 г · Калорійність: 1090 ккал"),
        ])
        db.commit()
    db.close()

    app.run(debug=True)
    