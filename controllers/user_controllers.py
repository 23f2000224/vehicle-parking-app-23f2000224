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
    
    available_spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()
    if not available_spot:
        flash('No parking spots available in this lot.', 'error')
        return redirect(url_for('user_dashboard'))
    
    lot = ParkingLot.query.get(lot_id)
    ticket = Ticket(
        spot_id=available_spot.id,
        user_id=current_user.id,
        vehicle_number=vehicle_number,
        parking_timestamp=datetime.now(),
        parking_cost_per_unit_time=lot.price,
        active=True
    )
    
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
    duration = (leaving_time - ticket.parking_timestamp).total_seconds() / 3600
    total_cost = duration * ticket.parking_cost_per_unit_time

    ticket.active = False
    ticket.leaving_timestamp = leaving_time
    ticket.total_cost = total_cost
    ticket.duration = duration
    ticket.spot.status = 'A'
    
    db.session.commit()
    flash(f'Parking spot released. Total cost: 9{total_cost:.2f}', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/history')
@user_required
def parking_history():
    tickets = (Ticket.query
              .filter_by(user_id=current_user.id)
              .order_by(Ticket.parking_timestamp.desc())
              .limit(50)
              .all())
    return render_template('user/history.html', tickets=tickets, user=current_user.username)

@app.route('/user/summary')
@user_required
def user_summary():
    try:
        tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.parking_timestamp.asc()).all()
        
        if not tickets:
            flash('No parking history available.', 'info')
            return redirect(url_for('user_dashboard'))

        plt.figure(figsize=(10, 6))
        dates = [ticket.parking_timestamp.strftime('%Y-%m-%d') for ticket in tickets]
        costs = [ticket.total_cost if ticket.total_cost else 0 for ticket in tickets]
        
        plt.bar(dates, costs, color='#007bff', alpha=0.85)
        plt.title('Parking Cost History', fontsize=24, fontweight='bold')
        plt.xlabel('Date', fontsize=21, fontweight='bold')
        plt.ylabel('Cost (9)', fontsize=21, fontweight='bold')
        plt.xticks(fontsize=18, rotation=0)
        plt.yticks(fontsize=18)
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close('all')
        
        plot_url = base64.b64encode(img.getvalue()).decode()
        
        total_spent = sum(costs)
        avg_cost = total_spent / len(tickets) if tickets else 0
        
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
            'total_spent': f"9{total_spent:.2f}",
            'avg_cost': f"9{avg_cost:.2f}",
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

    leaving_time = datetime.now()
    duration = Decimal(str((leaving_time - ticket.parking_timestamp).total_seconds() / 3600))
    total_cost = duration * ticket.parking_cost_per_unit_time

    ticket.active = False
    ticket.leaving_timestamp = leaving_time
    ticket.total_cost = total_cost
    ticket.duration = duration
    ticket.spot.status = 'A'
    
    db.session.commit()
    flash(f'Parking spot released. Total cost: 9{total_cost:.2f}', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/find', methods=['GET', 'POST'])
@user_required
def find_parking():
    if request.method == 'POST':
        search_query = request.form.get('search_query', '')
        search_type = request.form.get('search_type', 'location')
        
        base_query = (db.session.query(ParkingLot)
                     .join(ParkingSpot)
                     .filter(ParkingSpot.status == 'A')
                     .group_by(ParkingLot.id)
                     .having(db.func.count(ParkingSpot.id) > 0))
        
        if search_type == 'location':
            parking_lots = base_query.filter(
                ParkingLot.prime_location_name.ilike(f'%{search_query}%')
            ).all()
        else:
            parking_lots = base_query.filter(
                ParkingLot.pin_code.ilike(f'%{search_query}%')
            ).all()
        
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