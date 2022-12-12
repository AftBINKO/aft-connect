from .bootstrap_types import *
from .db_session import create_session
from .models import User, Status


def check_otp(one_time_password):
    """Проверяет одноразовый пароль, и возвращает сообщение с id пользователя"""
    db_sess = create_session()

    data = {
        'type_message': None,
        'message': None
    }

    # noinspection PyUnresolvedReferences
    user = db_sess.query(User).filter(User.one_time_password == one_time_password).first()

    if user:
        user_status = db_sess.query(Status).filter(Status.id == user.status).first().title

        user.delete_one_time_password()
        db_sess.commit()

        if user_status != "deactive":
            return user.id, data

        data['type_message'] = WARNING
        data['message'] = 'Ваш аккаунт был деактивирован.'
    else:
        data['type_message'] = DANGER
        data['message'] = 'Неверный пароль.'

    return None, data
