from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, render_template, request, make_response, redirect, session, url_for, jsonify
from datetime import date, datetime
import psycopg2
from Db import db
from Db.models import users, session, Place
from flask_login import login_user, login_required, current_user, logout_user
from osnovnaiu import db
osnovnaiu = Blueprint('osnovnaiu', __name__)

@osnovnaiu.route('/')
@osnovnaiu.route('/osnovnaiu')
def index():
    # Проверяем, авторизован ли пользователь
    if not current_user.is_authenticated:
        return redirect(url_for('osnovnaiu.login'))
    
    username = users.query.filter_by(id=current_user.id).first().username

    sessions = session.query.all()

    return render_template('index.html', sessions=sessions, username=username)

@osnovnaiu.route('/register', methods=["GET", "POST"])
def register():
    errors = []

    if request.method == "GET":
        return render_template("register.html")

    username_form = request.form.get('username')
    password_form = request.form.get('password')
    login_form = request.form.get('login')
    is_admin_form = request.form.get('is_superuser')
    existing_user = users.query.filter_by(login=login_form).first()

    if login_form == '':
        errors.append('Логин не может быть пустым!')

    if username_form == '':
        errors.append('Имя пользователя не может быть пустым!')

    elif existing_user is not None:
        errors.append('Пользователь с таким именем уже существует!')

    elif len(password_form) < 5:
        errors.append('Пароль должен быть длиннее 5 символов!')

    else:
        user = users.query.filter_by(username=username_form).first()

        if user is not None:
            if user.is_superuser:
                errors.append('Пользователь уже является администратором!')
            else:
                hashed_password = generate_password_hash(password_form, method='pbkdf2')
                new_user = users(username=username_form, password=hashed_password, login=login_form, is_superuser=True if is_admin_form == '1' else False)
                db.session.add(new_user)
                db.session.commit()
                return redirect('/login')

        else:
            hashed_password = generate_password_hash(password_form, method='pbkdf2')
            new_user = users(username=username_form, password=hashed_password, login=login_form, is_superuser=True if is_admin_form == '1' else False)
            db.session.add(new_user)
            db.session.commit()
            return redirect('/login')

    if is_admin_form == '1':
        if users.query.filter_by(is_superuser=True).first() is not None:
            errors.append("В базе данных уже есть администратор!")

    return render_template('register.html', errors=errors)



@osnovnaiu.route('/login', methods=["GET", "POST"])
def login():
    errors = []

    if request.method == 'GET':
        return render_template("login.html")

    login_form = request.form.get("login")
    password_form = request.form.get("password")

    my_user = users.query.filter_by(login=login_form).first()

    if not login_form or not password_form:
        errors.append("Заполните все поля!")
        return render_template("login.html", errors=errors)

    if my_user is not None:
        if check_password_hash(my_user.password, password_form):
            login_user(my_user)
            return redirect('/add')
        else:
            errors.append("Неверный пароль!")
            return render_template("login.html", errors=errors)
    else:
        errors.append("Пользвателя с таким именем не существует!")
        return render_template("login.html", errors=errors)
        

@osnovnaiu.route("/osnovnaiu/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@osnovnaiu.route('/add', methods=["GET", "POST"])
def add():
    is_admin = current_user.is_authenticated and current_user.is_superuser
    if not is_admin:
        return redirect('/osnovnaiu')
    
    errors = []
    if request.method == "GET":
        return render_template("add.html")

    movie_name = request.form.get("movie")
    time_film = request.form.get("time")
    date_film = request.form.get("date")

    if not movie_name or not time_film or not date_film:
        errors.append("Заполните все поля!")
    else:
        time_film_parsed = datetime.strptime(time_film, "%H:%M")
        new_session = session(movie=movie_name, time=time_film_parsed, date=date_film)
        db.session.add(new_session)
        db.session.commit()

    return render_template("add.html", errors=errors)

@osnovnaiu.route("/edit_session/<int:id>", methods =["GET", "POST"])
def edit_session(id):
    # Проверяем, авторизован ли пользователь или имеет роль "администратор"
    if current_user.is_authenticated or current_user.is_superuser:

        # Получаем сеанс по идентификатору
        Session = session.query.get(id)

        # Если запрос GET, отображаем форму редактирования
        if request.method == "GET":
            return render_template("editsession.html", Session=Session)

        # Если запрос POST, обновляем данные сеанса
        if request.method == "POST":
            # Получаем данные из формы
            # Обновляем данные сеанса
            Session.movie = request.form.get("movie")
            Session.time = request.form.get("time")
            Session.date = request.form.get("date")

            # Сохраняем изменения в базе данных
            db.session.commit()

            # Перенаправляем на главную страницу
            return redirect("/osnovnaiu")

    # Если пользователь не авторизован, отображаем главную страницу
    else:
        return render_template("index.html",
                                username=current_user.username,
                                session=session.query.all())

  
@osnovnaiu.route("/delete_session/<int:id>", methods=["GET", "POST"])
def delete_session(id):
    if current_user.is_authenticated or current_user.is_superuser:
        Session = session.query.get(id)

        if request.method == "GET":
            return render_template("deletesession.html", Session=Session)

        if request.method == "POST":
            db.session.delete(Session)
            db.session.commit()

            return redirect("/osnovnaiu")
    else:
        return render_template("index.html", username=current_user.username, session=session.query.all())


@osnovnaiu.route("/show_seats/<int:id>", methods=["GET"])
def show_seats(id):
    if not current_user.is_authenticated:
        return redirect("/login")
    places = Place.query.filter_by(session_id=id).all()

    if current_user.is_authenticated:
        seat = next((place for place in places if place.row == row and place.seat_number == seat_number), None)
        is_occupied = seat is not None
    else:
        is_occupied = False
    seats_scheme = []
    for row in range(1, 4):
        for seat_number in range(1, 11):
            is_occupied = False
            username = None
            for place in places:
                if place.row == row and place.seat_number == seat_number:
                    is_occupied = True
                    username = place.user.username
                    break
            seats_scheme.append((row, seat_number, is_occupied, username))

    return render_template("seats_show.html", seats_scheme=seats_scheme, session_id=id, username=current_user.username)

@osnovnaiu.route("/book_seat/<int:id>", methods=["GET", "POST"])
def book_seat(id):
    if not current_user.is_authenticated:
        return redirect("/login")
    seat_numbers = request.form.getlist("seat_numbers")
    # Получаем данные из запроса POST
    if request.method == "POST":
        seat_numbers = request.form.getlist("seat_numbers")

    # Получаем список мест для сеанса
    places = Place.query.filter_by(session_id=id).all()

  # Проверяем, что места свободны
    for seat_number in seat_numbers:
        place = Place.query.filter_by(session_id=id, row=seat_number // 3, seat_number=seat_number % 3).first()
        if place is not None and place.user_id is not None:
            if current_user.is_admin or place.user_id == current_user.id:
                place.delete()
            else:
                return jsonify({"success": False, "error": "У вас нет прав на удаление этой брони."})

    # Проверяем, что пользователь не бронирует больше 5 мест
    if len(seat_numbers) > 5:
        return jsonify({"success": False, "error": "Вы не можете бронировать более 5 мест."})

    # Добавляем данные о бронировании
    for seat_number in seat_numbers:
        if current_user.is_admin:
            continue
        place = Place(session_id=id, row=seat_number // 3, seat_number=seat_number % 3, user_id=current_user.id)
        place.save()

    # Возвращаем HTML-ответ
    return render_template("seats_book.html", session_id=id, places=places, username=current_user.username)