from .controller_common import *
from decimal import Decimal

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        if current_user.is_admin:
            flash('This page is only accessible to regular users.', 'warning')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/user/dashboard')
@user_required
def user_dashboard():
    tickets = Ticket.query.filter_by(user_id=current_user.id).all()
    parking_lots = ParkingLot.query.all()
    return render_template('user/dashboard.html', tickets=tickets, parking_lots=parking_lots, user=current_user.username)

@app.route('/user/park', methods=['POST'])
@user_required
def park_vehicle():
    form_data = request.form.to_dict()
    lot_id = form_data['lot_id']
    vehicle_number = form_data['vehicle_number']
    
    # Find first available spot
    available_spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()
    if not available_spot:
        flash('No parking spots available in this lot.', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Create parking ticket
    lot = ParkingLot.query.get(lot_id)
    ticket = Ticket(
        spot_id=available_spot.id,
        user_id=current_user.id,
        vehicle_number=vehicle_number,
        parking_timestamp=datetime.now(),
        parking_cost_per_unit_time=lot.price,
        active=True
    )
    
    # Update spot status
    available_spot.status = 'O'
    
    db.session.add(ticket)
    db.session.commit()
    
    flash('Vehicle parked successfully!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/release/<int:ticket_id>', methods=['POST'])
@user_required
def release_spot(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.user_id != current_user.id:
        flash('Unauthorized action', 'error')
        return redirect(url_for('user_dashboard'))
    
    leaving_time = datetime.now()
    duration = (leaving_time - ticket.parking_timestamp).total_seconds() / 3600  # hours
    total_cost = duration * ticket.parking_cost_per_unit_time

    ticket.active = False
    ticket.leaving_timestamp = leaving_time
    ticket.total_cost = total_cost
    ticket.duration = duration
    ticket.spot.status = 'A'
    
    db.session.commit()
    flash(f'Parking spot released. Total cost: ₹{total_cost:.2f}', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/history')
@user_required
def parking_history():
    tickets = (Ticket.query
              .filter_by(user_id=current_user.id)
              .order_by(Ticket.parking_timestamp.desc())
              .limit(50)  # Limit to recent 50 tickets for better performance
              .all())
    return render_template('user/history.html', tickets=tickets, user=current_user.username)

@app.route('/user/summary')
@user_required
def user_summary():
    try:
        # Get user's parking history
        tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.parking_timestamp.asc()).all()
        
        if not tickets:
            flash('No parking history available.', 'info')
            return redirect(url_for('user_dashboard'))

        # Create visualization
        plt.figure(figsize=(10, 6))
        dates = [ticket.parking_timestamp for ticket in tickets]
        costs = [ticket.total_cost if ticket.total_cost else 0 for ticket in tickets]
        
        plt.plot(dates, costs, marker='o')
        plt.title('Parking Cost History')
        plt.xlabel('Date')
        plt.ylabel('Cost (₹)')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save plot to memory
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close('all')  # Close all figures
        
        # Convert plot to base64 string
        plot_url = base64.b64encode(img.getvalue()).decode()
        
        # Calculate statistics
        total_spent = sum(costs)
        avg_cost = total_spent / len(tickets) if tickets else 0
        
        # Fix the query with explicit joins
        most_used_lot = (
            db.session.query(
                ParkingLot.prime_location_name,
                db.func.count(Ticket.id).label('ticket_count')
            )
            .select_from(Ticket)
            .join(ParkingSpot, Ticket.spot_id == ParkingSpot.id)
            .join(ParkingLot, ParkingSpot.lot_id == ParkingLot.id)
            .filter(Ticket.user_id == current_user.id)
            .group_by(ParkingLot.prime_location_name)
            .order_by(db.text('ticket_count DESC'))
            .first()
        )

        stats = {
            'total_parkings': len(tickets),
            'total_spent': f"₹{total_spent:.2f}",
            'avg_cost': f"₹{avg_cost:.2f}",
            'most_used_lot': most_used_lot[0] if most_used_lot else "N/A"
        }
        
        return render_template('user/summary.html', plot_url=plot_url, stats=stats, user=current_user.username)
        
    except Exception as e:
        app.logger.error(f"Error generating summary: {str(e)}")
        flash('Error generating summary. Please try again later.', 'error')
        return redirect(url_for('user_dashboard'))
    
@app.route('/user/book_parking/<int:record_id>', methods=['POST'])
@user_required
def book_parking(record_id):
    ticket = Ticket.query.get_or_404(record_id)
    if ticket.user_id != current_user.id:
        flash('Unauthorized action', 'error')
        return redirect(url_for('user_dashboard'))
    
    if ticket.active:
        flash('This parking spot is already booked.', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Mark the ticket as active
    ticket.active = True
    db.session.commit()
    
    flash('Parking spot booked successfully!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/release_parking/<int:record_id>', methods=['GET', 'POST'])
@user_required
def release_parking(record_id):
    ticket = Ticket.query.get_or_404(record_id)
    if ticket.user_id != current_user.id:
        flash('Unauthorized action', 'error')
        return redirect(url_for('user_dashboard'))

    if request.method == 'GET':
        return render_template('user/parking/release.html', ticket=ticket, user=current_user.username)

    if not ticket.active:
        flash('This parking spot is not booked.', 'error')
        return redirect(url_for('user_dashboard'))

    # Release the parking spot
    leaving_time = datetime.now()
    duration = Decimal(str((leaving_time - ticket.parking_timestamp).total_seconds() / 3600))  # Convert float to Decimal
    total_cost = duration * ticket.parking_cost_per_unit_time

    ticket.active = False
    ticket.leaving_timestamp = leaving_time
    ticket.total_cost = total_cost
    ticket.duration = duration
    ticket.spot.status = 'A'
    
    db.session.commit()
    flash(f'Parking spot released. Total cost: ₹{total_cost:.2f}', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/find', methods=['GET', 'POST'])
@user_required
def find_parking():
    if request.method == 'POST':
        search_query = request.form.get('search_query', '')
        search_type = request.form.get('search_type', 'location')
        
        # Base query for parking lots with available spots
        base_query = (db.session.query(ParkingLot)
                     .join(ParkingSpot)
                     .filter(ParkingSpot.status == 'A')
                     .group_by(ParkingLot.id)
                     .having(db.func.count(ParkingSpot.id) > 0))
        
        # Apply search filter
        if search_type == 'location':
            parking_lots = base_query.filter(
                ParkingLot.prime_location_name.ilike(f'%{search_query}%')
            ).all()
        else:  # pin_code
            parking_lots = base_query.filter(
                ParkingLot.pin_code.ilike(f'%{search_query}%')
            ).all()
        
        # Get available spots count for each lot
        lots_with_spots = []
        for lot in parking_lots:
            available_spots = ParkingSpot.query.filter_by(
                lot_id=lot.id, 
                status='A'
            ).count()
            lots_with_spots.append({
                'lot': lot,
                'available_spots': available_spots
            })
        
        return render_template(
            'user/find.html',
            lots_with_spots=lots_with_spots,
            search_query=search_query,
            search_type=search_type,
            user=current_user.username
        )
    
    return render_template('user/find.html', user=current_user.username)

@app.route('/user/view_ticket/<int:ticket_id>')
@user_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('user_dashboard'))
    return render_template('user/view_ticket.html', ticket=ticket, user=current_user.username)