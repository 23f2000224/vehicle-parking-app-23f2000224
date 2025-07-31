from models import db, ParkingLot, ParkingSpot, User, Ticket
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def populate_db():
    lot_data = [
        {
            'prime_location_name': 'Downtown Parking',
            'price': 40.00,
            'address': '123 Main St',
            'pin_code': '123456',
            'maximum_number_of_spots': 10
        },
        {
            'prime_location_name': 'Uptown Parking',
            'price': 55.00,
            'address': '456 High St',
            'pin_code': '654321',
            'maximum_number_of_spots': 8
        }
    ]
    lots = []
    for lot_info in lot_data:
        lot = ParkingLot.query.filter_by(prime_location_name=lot_info['prime_location_name']).first()
        if not lot:
            lot = ParkingLot(**lot_info)
            db.session.add(lot)
            db.session.commit()
        existing_spots = ParkingSpot.query.filter_by(lot_id=lot.id).count()
        spots_needed = lot_info['maximum_number_of_spots'] - existing_spots
        if spots_needed > 0:
            for i in range(spots_needed):
                spot = ParkingSpot(lot_id=lot.id, status='A')
                db.session.add(spot)
            db.session.commit()
        lots.append(lot)

    user_data = [
        {
            'username': 'john_doe',
            'password': 'password123',
            'fullname': 'John Doe',
            'address': '456 Elm St',
            'pincode': '654321',
        },
        {
            'username': 'jane_smith',
            'password': 'janesmith123',
            'fullname': 'Jane Smith',
            'address': '101 Maple Ave',
            'pincode': '111222',
        },
    ]

    users = []
    for u in user_data:
        user = User.query.filter_by(username=u['username']).first()
        if not user:
            user = User(
                username=u['username'],
                password_hash=generate_password_hash(u['password']),
                fullname=u['fullname'],
                address=u['address'],
                pincode=u['pincode'],
                is_admin=False
            )
            db.session.add(user)
            db.session.commit()
        users.append(user)

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

    # Create inactive tickets for each user
    ticket_data = [
        ('ABC123', 10, 2),  # vehicle, days_ago, hours_duration
        ('XYZ789', 7, 3),
        ('LMN456', 5, 4),
        ('JKL321', 3, 6),
        ('QWE987', 8, 1),
    ]
    
    base_date = datetime(2025, 7, 1, 10, 0, 0)  # July 1, 2025, 10:00 AM
    
    for i, user in enumerate(users):
        lot = lots[i % len(lots)]
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        
        for j, (vehicle, days_ago, duration) in enumerate(ticket_data):
            spot = spots[j % len(spots)]
            start_time = base_date - timedelta(days=days_ago, hours=duration)
            end_time = start_time + timedelta(hours=duration)
            
            # Check if ticket already exists
            existing_ticket = Ticket.query.filter_by(
                user_id=user.id,
                vehicle_number=vehicle,
                parking_timestamp=start_time
            ).first()
            
            if existing_ticket:
                continue
            
            ticket = Ticket(
                user_id=user.id,
                spot_id=spot.id,
                vehicle_number=vehicle,
                active=False,
                parking_timestamp=start_time,
                leaving_timestamp=end_time,
                parking_cost_per_unit_time=lot.price,
                total_cost=lot.price * duration,
                duration=duration
            )
            db.session.add(ticket)
    
    db.session.commit()