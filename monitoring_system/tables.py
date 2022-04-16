from flask_app import db


class Metrics(db.Model):
    time = db.Column(db.TIMESTAMP, primary_key=True)
    t = db.Column(db.String(80), nullable=False)
    h = db.Column(db.String(80), nullable=False)


class Delay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    delay = db.Column(db.String(80), nullable=False)
