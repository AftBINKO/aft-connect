from os import remove
from os.path import exists
from json import dump, load

from data.db_session import *
from data.models import *

path, tmp = "db/users.sqlite3", "tmp/tmp.json"


def migrate():
    if not exists(tmp):
        global_init(path)
        db_sess = create_session()
        users = [usr.to_dict() for usr in db_sess.query(User).all()]
        with open(tmp, 'x', encoding='utf-8') as json:
            dump(users, json, indent=4, ensure_ascii=False)

        print("Edit you model and restart the script")
    else:
        if exists(path):
            remove(path)

        global_init(path)
        db_sess = create_session()

        with open(tmp, 'r', encoding='utf-8') as json:
            users = load(json)

        columns = User().get_columns()

        for user in users:
            user: dict
            user_data = {}

            for key in user.keys():
                if key in columns:
                    user_data[key] = user[key]
            user_model = User(**user_data)
            db_sess.add(user_model)
        db_sess.commit()

        remove(tmp)
        print("Success")


if __name__ == '__main__':
    migrate()
