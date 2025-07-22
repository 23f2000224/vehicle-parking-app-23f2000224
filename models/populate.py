from models import db, ParkingLot, ParkingSpot, User, Ticket
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def populate_db():
    # Create a parking lot if it doesn't exist
    parking_lot = ParkingLot.query.filter_by(prime_location_name='Downtown Parking').first()
    if not parking_lot:
        parking_lot = ParkingLot(
            prime_location_name='Downtown Parking',
            price=25.00,
            address='123 Main St',
            pin_code='123456',
            maximum_number_of_spots=10
        )
        db.session.add(parking_lot)
        db.session.commit()

        # Create parking spots only if the lot was just created
        for i in range(1, 11):
            spot = ParkingSpot(lot_id=parking_lot.id, status='A')
            db.session.add(spot)
        db.session.commit()

    # Create a regular user if not exists
    user = User.query.filter_by(username='john_doe').first()
    if not user:
        user = User(
            username='john_doe',
            password_hash=generate_password_hash('password123'),
            fullname='John Doe',
            address='456 Elm St',
            pincode='654321',
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()

    # Create an admin user if not exists
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            fullname='Admin User',
            address='789 Oak St',
            pincode='789012',
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()

    # Reserve a parking spot for john_doe if not already reserved
    user = User.query.filter_by(username='john_doe').first()
    parking_lot = ParkingLot.query.filter_by(prime_location_name='Downtown Parking').first()
    spot = ParkingSpot.query.filter_by(lot_id=parking_lot.id).first()
    existing_ticket = Ticket.query.filter_by(user_id=user.id, spot_id=spot.id).first()
    if not existing_ticket:
        ticket = Ticket(
            user_id=user.id,
            spot_id=spot.id,
            vehicle_number='ABC123',
            active=False,
            parking_timestamp=datetime.now() - timedelta(hours=1),
            leaving_timestamp=datetime.now(),
            parking_cost_per_unit_time=50.00
        )
        db.session.add(ticket)
        db.session.commit()