from sqlalchemy import Column, String, Integer, Date, Boolean, Text

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)

    surname = Column(String, nullable=False)
    name = Column(String, nullable=False)
    patronymic = Column(String)
    date_of_birth = Column(String, nullable=False)
    sex = Column(Boolean, nullable=False)

    email = Column(String, unique=True, nullable=False)
    login = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    data = Column(Text, default="{}")
    active = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<User {self.surname} {self.name}>"

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def get_columns(self):
        return [column.key for column in self.__table__.columns]
