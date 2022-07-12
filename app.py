from flask import Flask, render_template, redirect, flash, url_for
from flask_login import current_user, LoginManager, login_required, logout_user, login_user

from config import *
from data.db_session import *
from data.forms import RegisterForm, LoginForm
from data.models import User
from data.bootstrap_types import *

app = Flask(__name__)
app.config.from_object('config')

login_manager = LoginManager()
login_manager.init_app(app)

global_init("db/users.sqlite3", True)


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect("/my")  # TODO: Заменить на url_for

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
        elif " " in form.password.data:
            data['type_message'] = DANGER
            data['message'] = "Пароль содержит пробел."
        elif form.password.data != form.password_again.data:
            data['type_message'] = DANGER
            data['message'] = "Пароли не совпадают."
        else:
            user = User()

            user.name = form.name.data
            user.surname = form.surname.data
            user.patronymic = form.patronymic.data
            user.date_of_birth = str(form.date_of_birth.data)
            user.sex = form.sex.data != "Мужской"

            user.login = form.login.data
            user.email = form.email.data
            user.set_password(form.password.data)

            db_sess.add(user)
            db_sess.commit()
            return redirect(url_for('index'))
    return render_template('register.html', **data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect("/my")  # TODO: Заменить на url_for

    db_sess = create_session()

    form = LoginForm()
    data = {
        'form': form,
        'type_message': None,
        'message': None
    }

    if form.validate_on_submit():
        # noinspection PyUnresolvedReferences
        user = db_sess.query(User).filter(User.login == form.login.data).first()

        if user:
            if user.active:
                if user.check_password(form.password.data):
                    login_user(user, remember=form.remember_me.data)
                    return redirect('/my')  # TODO: Заменить на url_for

                data['type_message'] = DANGER
                data['message'] = 'Неверный пароль.'
            else:
                data['type_message'] = WARNING
                data['message'] = 'Ваш аккаунт был удалён.'
        else:
            data['type_message'] = DANGER
            data['message'] = 'Неверный логин.'

    return render_template('login.html', **data)


if __name__ == '__main__':
    app.run(debug=DEBUG)
