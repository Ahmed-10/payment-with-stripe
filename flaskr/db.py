from flask_sqlalchemy import SQLAlchemy
from enum import Enum


db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    company = db.Column(db.String(50), nullable=False)

    def __init__(self, email, company):
        self.email = email
        self.company = company

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def rollback(self):
        db.session.rollback()

    def format(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'company': self.company,
        }


# INTEGRATION NOTE #1: add subscription models
# ----------------- start -----------------
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)
    stripe_id = db.Column(db.String(50), nullable=False, unique=True)
    mail = db.Column(db.String(50), nullable=False, unique=True)
    company = db.Column(db.String(50), nullable=False)
    package = db.Column(db.Integer, nullable=False)
    off_session = db.Column(db.Boolean)
    renew_date = db.Column(db.DateTime)

    def __init__(self, mail, company, user_id, stripe_id):
        self.mail = mail
        self.company = company
        self.user_id = user_id
        self.stripe_id = stripe_id
        self.package = 1

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def rollback(self):
        db.session.rollback(self)

    def format(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'mail': self.mail,
            'company': self.company,
            'stripe_id': self.stripe_id,
            'plan': str(self.package),
            'renew_date': self.renew_date,
        }


class Plans(db.Model):
    __tablename__ = 'plans'

    id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(50), nullable=False, unique=True)
    price = db.Column(db.Integer, nullable=False, unique=True)
    details = db.Column(db.Text, nullable=False)

    def __init__(self, plan_name, price, features):
        self.plan_name = plan_name
        self.price = price
        details = ''
        for feature in features:
            details = details + feature + '-'
        self.details = details

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def rollback(self):
        db.session.rollback(self)

    def format(self):
        return {
            'id': str(self.id),
            'plan_name': self.plan_name,
            'price': self.price,
            'features': self.details.split('-'),
        }

# ----------------- end -----------------