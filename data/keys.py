from random import choices
from string import digits, ascii_uppercase
from json import loads

from .db_session import create_session
from .models import User


def generate_key():
    db_sess = create_session()

    users = db_sess.query(User).all()

    while True:
        key = "ACK-" + "".join(choices(digits + ascii_uppercase, k=16))

        flag = True
        for user in users:
            try:
                if loads(user.data)["auth_key"]["key"] == key:
                    flag = False

            except KeyError:
                pass

        if flag:
            return key
