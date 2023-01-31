from flask import Flask, render_template, redirect, flash, url_for, request, abort
from flask_login import current_user, LoginManager, login_required, logout_user, login_user
from datetime import date, datetime
from json import loads, dumps
from dateutil.relativedelta import relativedelta
from string import ascii_letters, digits, punctuation

from flask_restful import Api
from pytils import numeral

from config import *
from data.auth_resources import *
from data.db_session import *
from data.forms import RegisterForm, LoginForm, EditPersonalInfoForm, ChangeEmailForm, \
    ChangePasswordForm, DeactivateForm, LoginOneTimePasswordForm
from data.models import *
from data.bootstrap_types import *
from data.one_time_password import check_otp
from data.keys import generate_key

app = Flask(__name__)
app.config.from_object('config')
api = Api(app)

login_manager = LoginManager()
login_manager.init_app(app)

global_init("db/users.sqlite3", DEBUG)
RUSSIAN_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
RUSSIAN_MONTHS = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь"
}


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()
    user = db_sess.query(User).get(user_id)

    if user:
        user_status = db_sess.query(Status).filter(Status.id == user.status).first()
        if user_status.access_login:
            return user

    return


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    db_sess = create_session()

    form = RegisterForm()
    data = {
        'form': form,
        'type_message': None,
        'message': None
    }

    if form.validate_on_submit():
        # noinspection PyUnresolvedReferences
        if db_sess.query(User).filter(User.email == form.email.data).first() or \
                db_sess.query(User).filter(User.login == form.login.data).first():
            data['type_message'] = WARNING
            data['message'] = "Такой пользователь уже есть."
        elif not (all([symbol in RUSSIAN_ALPHABET for symbol in
                       form.name.data + form.surname.data + form.patronymic.data]) or all(
            [symbol in ascii_letters for symbol in
             form.name.data + form.surname.data + form.patronymic.data])):
            data['type_message'] = DANGER
            data['message'] = "Поля ФИО заполнены неверно. Используйте либо буквы русского " \
                              "алфавита, либо английского."
        elif not all([symbol in ascii_letters + digits for symbol in form.login.data]):
            data['type_message'] = DANGER
            data['message'] = "Логин содержит некорректные символы."
        elif not all(
                [symbol in ascii_letters + digits + punctuation for symbol in form.password.data]):
            data['type_message'] = DANGER
            data['message'] = "Пароль содержит некорректные символы."
        elif form.password.data != form.password_again.data:
            data['type_message'] = WARNING
            data['message'] = "Пароли не совпадают."
        else:
            user = User()

            user.name = form.name.data.lower().capitalize()
            user.surname = form.surname.data.lower().capitalize()
            user.patronymic = form.patronymic.data.lower().capitalize()
            user.date_of_birth = str(form.date_of_birth.data)
            user.sex = form.sex.data != "Мужской"

            user.login = form.login.data.lower()
            user.email = form.email.data
            user.set_password(form.password.data)

            user_data = {
                "auth_key":
                    {
                        "key": generate_key(),
                        "is_active": True
                    }
            }
            user.data = dumps(user_data)

            db_sess.add(user)
            db_sess.commit()
            return redirect(url_for("profile"))
    return render_template('register.html', **data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    db_sess = create_session()

    form = LoginForm()
    data = {
        'form': form,
        'type_message': None,
        'message': None
    }

    if form.validate_on_submit():
        # noinspection PyUnresolvedReferences
        user = db_sess.query(User).filter(User.login == form.login.data.lower()).first()

        if user:
            user_status = db_sess.query(Status).filter(Status.id == user.status).first()

            if user_status.access_login:
                if user.check_password(form.password.data):
                    login_user(user, remember=form.remember_me.data)
                    return redirect(url_for("profile"))

                data['type_message'] = DANGER
                data['message'] = 'Неверный пароль.'
            else:
                if user_status.title == "deactive":
                    data['type_message'] = WARNING
                    data['message'] = 'Ваш аккаунт был деактивирован.'
                else:
                    data['type_message'] = DANGER
                    data['message'] = 'Не удалось выполнить вход.'
        else:
            data['type_message'] = DANGER
            data['message'] = 'Неверный логин.'

    return render_template('login.html', **data)


@app.route('/login/one_time_password', methods=['GET', 'POST'])
def login_one_time_password():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    db_sess = create_session()

    form = LoginOneTimePasswordForm()
    data = {
        'form': form
    }

    if form.validate_on_submit():
        user_id, message = check_otp(form.one_time_password.data)
        data.update(message)

        if user_id is not None:
            user = db_sess.query(User).filter(User.id == user_id).first()
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for("profile"))

    return render_template('login_one_time_password.html', **data)


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))
    return redirect(url_for("login"))


@app.route('/my', methods=['GET', 'POST'])
@login_required
def profile():
    date_of_birth = datetime.strptime(current_user.date_of_birth, '%Y-%m-%d').date()
    age = relativedelta(date.today(), date_of_birth).years
    naming = numeral.get_plural(age, "год, года, лет")

    db_sess = create_session()
    user_status = db_sess.query(Status).filter(Status.id == current_user.status).first()

    data = {
        'age': naming,
        'status': user_status
    }

    return render_template('profile.html', **data)


@app.route('/admin_panel', methods=['GET', 'POST'])
@login_required
def admin_panel():
    db_sess = create_session()
    user_status = db_sess.query(Status).filter(Status.id == current_user.status).first()

    if user_status.access_admin_panel:
        data = {
            "users": db_sess.query(User).filter(User.id != current_user.id),
            "statuses": db_sess.query(Status).all()
        }

        if request.method == "POST":
            d = dict(request.form)
            print(d)
            for header in d.keys():
                match header:

                    case "del_otp_user_id":
                        user = db_sess.query(User).filter(
                            User.id == int(d["del_otp_user_id"])
                        ).first()
                        user.delete_one_time_password()

                    case "activate":
                        user = db_sess.query(User).filter(User.id == int(d["activate"])).first()
                        status = db_sess.query(Status).filter(Status.title == "default").first()
                        user.status = status.id

                    case "deactivate":
                        user = db_sess.query(User).filter(User.id == int(d["deactivate"])).first()
                        status = db_sess.query(Status).filter(Status.title == "deactive").first()
                        user.status = status.id

                    case "give_permissions":
                        user = db_sess.query(User).filter(
                            User.id == int(d["give_permissions"])
                        ).first()
                        status = db_sess.query(Status).filter(Status.title == "moderator").first()
                        user.status = status.id

                    case "remove_permissions":
                        user = db_sess.query(User).filter(
                            User.id == int(d["remove_permissions"])
                        ).first()
                        status = db_sess.query(Status).filter(Status.title == "default").first()
                        user.status = status.id

            db_sess.commit()

        return render_template('admin_panel.html', **data)

    abort(403)


@app.route('/my/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    db_sess = create_session()

    form = EditPersonalInfoForm()
    data = {
        'form': form,
        'type_message': None,
        'message': None
    }

    if form.validate_on_submit():
        # noinspection PyUnresolvedReferences
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        name = form.name.data.lower().capitalize() if form.name.data else user.name
        surname = form.surname.data.lower().capitalize() if form.surname.data else user.surname
        patronymic = form.patronymic.data.lower(
        ).capitalize() if form.patronymic.data else user.patronymic

        if not (all([symbol in RUSSIAN_ALPHABET for symbol in name + surname + patronymic]) or all(
                [symbol in ascii_letters for symbol in name + surname + patronymic])):
            data['type_message'] = DANGER
            data['message'] = "Поля ФИО заполнены неверно. Используйте либо буквы русского " \
                              "алфавита, либо английского."
        else:
            user.name = name
            user.surname = surname
            user.patronymic = patronymic

            user.date_of_birth = form.date_of_birth.data \
                if form.date_of_birth.data else user.date_of_birth
            user.sex = form.sex.data != "Мужской"

            db_sess.commit()
            return redirect(url_for("profile"))

    return render_template('edit_profile.html', **data)


@app.route('/my/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    db_sess = create_session()

    form = ChangeEmailForm()
    data = {
        'form': form,
        'type_message': None,
        'message': None
    }

    if form.validate_on_submit():
        # noinspection PyUnresolvedReferences
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        if user.email != form.old_email.data:
            data['type_message'] = DANGER
            data['message'] = "Неверная почта."
        else:
            user.email = form.new_email.data

            db_sess.commit()
            return redirect(url_for("profile"))

    return render_template('change_email.html', **data)


@app.route('/my/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    db_sess = create_session()

    form = ChangePasswordForm()
    data = {
        'form': form,
        'type_message': None,
        'message': None
    }

    if form.validate_on_submit():
        # noinspection PyUnresolvedReferences
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        if not all([symbol in ascii_letters + digits + punctuation for symbol in
                    form.new_password.data]):
            data['type_message'] = DANGER
            data['message'] = "Пароль содержит некорректные символы."
        elif form.new_password.data != form.new_password_again.data:
            data['type_message'] = WARNING
            data['message'] = "Пароли не совпадают."
        elif not user.check_password(form.old_password.data):
            data['type_message'] = DANGER
            data['message'] = "Неверный пароль."
        elif form.old_password.data == form.new_password.data:
            data['type_message'] = WARNING
            data['message'] = "Новый пароль совпадает со старым."
        else:
            user.set_password(form.new_password.data)

            db_sess.commit()
            return redirect(url_for("profile"))

    return render_template('change_password.html', **data)


@app.route('/my/deactivate', methods=['GET', 'POST'])
@login_required
def deactivate_account():
    db_sess = create_session()

    form = DeactivateForm()
    # noinspection PyUnresolvedReferences
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    text = f'Я ПРОЧИТАЛ{"А" if user.sex else ""} СООБЩЕНИЕ ВЫШЕ И ПОНИМАЮ ВСЕ РИСКИ'
    data = {
        'form': form,
        'verification_text': text,
        'type_message': None,
        'message': None
    }
    if form.validate_on_submit():
        if form.text.data != text:
            data['type_message'] = DANGER
            data['message'] = "Неправильно набран текст."
        else:
            user.status = db_sess.query(Status).filter(Status.title == "deactive").first().id
            user.delete_one_time_password()

            user_data = loads(user.data)
            user_data["auth_key"]["is_active"] = False
            user.data = dumps(user_data)

            db_sess.commit()

            logout()

    return render_template('deactivation.html', **data)


@app.route('/my/generate_one_time_password', methods=['GET', 'POST'])
@login_required
def generate_one_time_password():
    db_sess = create_session()
    # noinspection PyUnresolvedReferences
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.generate_one_time_password()
    db_sess.commit()

    return redirect(url_for('profile'))


@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for('login'))


@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html')


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html')


@app.errorhandler(500)
def crash(error):
    return render_template('500.html')


if __name__ == '__main__':
    api.add_resource(UserResource, "/api/get_user_data")
    app.run(debug=DEBUG)
