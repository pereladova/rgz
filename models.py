from . import db
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Time, Date, ForeignKey
from sqlalchemy.orm import relationship

class users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    login = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    is_superuser = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"id:{self.id}, username:{self.username}"
        
class session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie = db.Column(db.String(255))
    time = db.Column(db.Time, nullable=False)
    date = db.Column(db.Date)
    seats = db.relationship('Place', backref='session', lazy='dynamic')

    def __repr__(self):
        return f"id:{self.id},movie:{self.movie}, time:{self.time}, date:{self.date}"

class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    row = db.Column(db.Integer)
    seat_number = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)

    def __repr__(self):
        return f"id: {self.id}, row: {self.row}, seat_number: {self.seat_number}"