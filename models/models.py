from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash

db = SQLAlchemy()

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    address = db.Column(db.Text, nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    maximum_number_of_spots = db.Column(db.Integer, nullable=False)
    # Add additional fields as needed

    spots = db.relationship('ParkingSpot', backref='lot', lazy=True)

    def __repr__(self):
        return f"<ParkingLot {self.prime_location_name} ({self.address})>"


class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), nullable=False, default='A')  # 'O' or 'A'
    # Add additional fields as needed

    reservations = db.relationship('ReserveParkingSpot', backref='spot', lazy=True)

    def __repr__(self):
        return f"<Spot {self.id} in {self.lot.prime_location_name} - {self.status}>"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    # Add additional fields as needed (username, email, etc.)
    username = db.Column(db.String(80), unique=True, nullable=False)
    fullname = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    parking_reservations = db.relationship('ReserveParkingSpot', backref='user', lazy=True)
    password_hash = db.Column(db.String(128), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ReserveParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False)
    leaving_timestamp = db.Column(db.DateTime, nullable=False)
    parking_cost_per_unit_time = db.Column(db.Numeric(8, 2), nullable=False)
    # Add additional fields as needed

    def __repr__(self):
        return f"<Reservation {self.id} by User {self.user_id} for Spot {self.spot_id}>"