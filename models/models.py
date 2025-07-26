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

    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, 
                          cascade='all, delete-orphan')

    def __repr__(self):
        return f"<ParkingLot {self.prime_location_name} ({self.address})>"

    def needs_spots(self):
        """Check if parking lot needs spots to be created"""
        return len(self.spots) < self.maximum_number_of_spots

    def remaining_spots_to_create(self):
        """Get number of spots that need to be created"""
        return self.maximum_number_of_spots - len(self.spots)

    def get_occupied_spots_count(self):
        """Get count of spots that are currently occupied"""
        return ParkingSpot.query.filter_by(lot_id=self.id, status='O').count()

    def can_reduce_spots(self, new_max_spots):
        """Check if spots can be reduced to new maximum"""
        occupied_spots = self.get_occupied_spots_count()
        return occupied_spots <= new_max_spots

    def safely_reduce_spots(self, new_max_spots):
        """Try to reduce spots to new maximum, return success status and message"""
        if not self.can_reduce_spots(new_max_spots):
            occupied = self.get_occupied_spots_count()
            return False, f"Cannot reduce spots below occupied count ({occupied} spots in use)"
            
        # Delete only available spots
        spots_to_delete = (ParkingSpot.query
                         .filter_by(lot_id=self.id, status='A')
                         .order_by(ParkingSpot.id.desc())
                         .limit(len(self.spots) - new_max_spots)
                         .all())
        
        for spot in spots_to_delete:
            db.session.delete(spot)
            
        return True, f"Successfully reduced to {new_max_spots} spots"


class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), nullable=False, default='A')  # 'O' or 'A'

    tickets = db.relationship('Ticket', backref='spot', lazy=True,
                            cascade='all, delete-orphan')

    def has_active_tickets(self):
        return any(ticket.active for ticket in self.tickets)

    def get_active_ticket(self):
        """Get the currently active ticket for this spot, if any"""
        return Ticket.query.filter_by(spot_id=self.id, active=True).first()

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
    parking_tickets = db.relationship('Ticket', backref='user', lazy=True)
    password_hash = db.Column(db.String(128), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)    
    
    def __repr__(self):
        return f"<User {self.username} ({self.fullname})>"

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False)
    leaving_timestamp = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # in hours
    total_cost = db.Column(db.Numeric(10, 2))
    parking_cost_per_unit_time = db.Column(db.Numeric(8, 2), nullable=False)

    def __repr__(self):
        return f"<Ticket {self.id} by User {self.user_id} for Spot {self.spot_id}>"