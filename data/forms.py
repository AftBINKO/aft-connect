from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, EmailField, BooleanField, DateField, \
    SelectField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    surname = StringField('Фамилия', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    patronymic = StringField('Отчество')
    date_of_birth = DateField('Дата рождения', validators=[DataRequired()])
    sex = SelectField('Пол', choices=["Мужской", "Женский"])

    email = EmailField('Почта', validators=[DataRequired()])
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class EditPersonalInfoForm(FlaskForm):
    surname = StringField('Фамилия')
    name = StringField('Имя')
    patronymic = StringField('Отчество')
    date_of_birth = DateField('Дата рождения')
    sex = SelectField('Пол', choices=["Мужской", "Женский"])
    submit = SubmitField('Подтвердить')


class ChangeEmailForm(FlaskForm):
    old_email = EmailField('Старая почта', validators=[DataRequired()])
    new_email = EmailField('Новая почта', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Старый пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired()])
    new_password_again = PasswordField('Повторите новый пароль', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')
