from flask import jsonify
from flask_login import current_user
from flask_restful import Resource
from .db_session import create_session
from .models import User

from json import loads


class UserResource(Resource):
    def get(self):
        db_sess = create_session()

        if current_user.is_authenticated:
            user = db_sess.query(User).filter(User.id == current_user.id).first()
        else:
            return jsonify({"message": "401 unauthorized"})

        data = user.to_dict(only=(
            "surname", "name", "patronymic", "date_of_birth", "sex", "email",
            "login", "active"
        ))
        data["data"] = loads(user.data)

        return jsonify({
            "message": "accepted",
            "user": data
        })
