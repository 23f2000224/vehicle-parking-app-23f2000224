from functools import wraps
from .controller_common import *
import matplotlib.pyplot as plt
import io
import base64

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('This page is only accessible to administrators.', 'warning')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    parking_lots = ParkingLot.query.all()
    return render_template('admin/dashboard.html', parking_lots=parking_lots)


@app.route('/admin/summary', methods=['GET', 'POST'])
@admin_required
def admin_summary():
    try:
        if not ParkingLot.query.first():
            flash('No parking lots available to generate summary.', 'warning')
            return redirect(url_for('admin_dashboard'))

        parking_lots = ParkingLot.query.all()
        
        revenue_data = {}
        total_revenue = 0
        for lot in parking_lots:
            revenue = db.session.query(db.func.sum(Ticket.total_cost))\
                .join(ParkingSpot)\
                .filter(ParkingSpot.lot_id == lot.id)\
                .scalar() or 0
            revenue_data[lot.prime_location_name] = float(revenue)
            total_revenue += float(revenue)

        revenue_plot = None 

        if total_revenue > 0:
            plt.figure(figsize=(10, 6))
            plt.pie(revenue_data.values(), labels=revenue_data.keys(), autopct='%1.1f%%', pctdistance=0.85, textprops={'fontsize': 18})
            plt.gca().add_artist(plt.Circle((0,0), 0.70, fc='white'))
            plt.text(0, 0, f'\u20b9{total_revenue:.2f}\nTotal', ha='center', va='center', fontsize=21, fontweight='bold')
            plt.title('Revenue Distribution by Parking Lot', fontsize=24, fontweight='bold')

            revenue_img = io.BytesIO()
            plt.savefig(revenue_img, format='png', bbox_inches='tight')
            revenue_img.seek(0)
            plt.close() 

            revenue_plot = base64.b64encode(revenue_img.getvalue()).decode()
        else:
            app.logger.warning("Total revenue is zero. Skipping revenue distribution plot generation.")
            flash('No revenue generated yet to display a revenue distribution chart.', 'info')

        lot_names = []
        occupied_spots = []
        available_spots = []
        total_spots = 0
        total_occupied = 0
        
        for lot in parking_lots:
            occupied = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
            available = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
            total = occupied + available
            
            lot_names.append(lot.prime_location_name)
            occupied_spots.append(occupied)
            available_spots.append(available)
            
            total_spots += total
            total_occupied += occupied
        
        spots_plot = None
        if lot_names:
            plt.figure(figsize=(12, 6))
            x = range(len(lot_names))
            width = 0.35
            
            plt.bar([i - width/2 for i in x], occupied_spots, width, label='Occupied', color='#dc3545', alpha=0.8)
            plt.bar([i + width/2 for i in x], available_spots, width, label='Available', color='#28a745', alpha=0.8)
            
            plt.xlabel('Parking Lots', fontsize=21, fontweight='bold')
            plt.ylabel('Number of Spots', fontsize=21, fontweight='bold')
            plt.title('Parking Spots Distribution by Lot', fontsize=24, fontweight='bold')
            plt.xticks(x, lot_names, fontsize=18)
            plt.yticks(fontsize=18)
            plt.legend(fontsize=18)
            plt.tight_layout()
            
            spots_img = io.BytesIO()
            plt.savefig(spots_img, format='png', bbox_inches='tight', dpi=100)
            spots_img.seek(0)
            plt.close()
            
            spots_plot = base64.b64encode(spots_img.getvalue()).decode()
        
        summary_stats = {
            'total_revenue': f"\u20b9{total_revenue:.2f}",
            'total_spots': total_spots,
            'total_occupied': total_occupied,
            'total_available': total_spots - total_occupied,
            'overall_occupancy': (total_occupied/total_spots*100) if total_spots > 0 else 0
        }

        return render_template(
            'admin/summary.html',
            revenue_plot=revenue_plot,
            spots_plot=spots_plot,
            summary_stats=summary_stats
        )
        
    except Exception as e:
        app.logger.error(f"Error generating admin summary: {str(e)}")
        flash('Error generating summary. Please try again later.', 'error')
        return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/search', methods=['GET', 'POST'])
@admin_required
def admin_search():
    if request.method == 'POST':
        search_type = request.form.get('search_type')
        if search_type == 'parking_lot':
            search_query = request.form.get('search_query')
            parking_lots = ParkingLot.query.filter(
                ParkingLot.prime_location_name.ilike(f'%{search_query}%')
            ).all()
            return render_template('admin/search.html', parking_lots=parking_lots, search_query=search_query)
        elif search_type == 'user':
            search_query = request.form.get('search_query')
            users = User.query.filter(User.username.ilike(f'%{search_query}%')).all()
            return render_template('admin/search.html', users=users, search_query=search_query)
    return render_template('admin/search.html')

    
@app.route("/admin/users")
@admin_required
def users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)


def create_parking_spots(lot):
    try:
        for spot_number in range(lot.maximum_number_of_spots):
            spot = ParkingSpot(lot_id=lot.id, status='A')
            db.session.add(spot)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

@app.route("/admin/add_parking_lot", methods=['GET', 'POST'])
@admin_required
def add_parking_lot():
    if request.method == 'POST':
        try:
            form_data = request.form.to_dict()

            required_fields = ['prime_location_name', 'price', 'address', 'pin_code', 'maximum_number_of_spots']
            for field in required_fields:
                if not form_data.get(field):
                    flash(f'The field {field} is required.', 'error')
                    return render_template('admin/parking/create_lot.html')

            prime_location_name = form_data['prime_location_name']
            price = float(form_data['price'])
            address = form_data['address']
            pin_code = form_data['pin_code']
            maximum_number_of_spots = int(form_data['maximum_number_of_spots'])

            if price <= 0:
                flash('Price must be greater than 0.', 'error')
                return render_template('admin/parking/create_lot.html')

            if maximum_number_of_spots <= 0:
                flash('Maximum number of spots must be greater than 0.', 'error')
                return render_template('admin/parking/create_lot.html')

            new_lot = ParkingLot(
                prime_location_name=prime_location_name,
                price=price,
                address=address,
                pin_code=pin_code,
                maximum_number_of_spots=maximum_number_of_spots
            )
            db.session.add(new_lot)
            db.session.commit()

            create_parking_spots(new_lot)

            flash('Parking lot and spots created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except ValueError:
            flash('Invalid input for price or maximum number of spots. Please enter valid numbers.', 'error')
            return render_template('admin/parking/create_lot.html')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating parking lot: {str(e)}', 'error')
            return render_template('admin/parking/create_lot.html')

    return render_template('admin/parking/create_lot.html')

@app.route("/admin/edit_parking_lot/<int:lot_id>", methods=['GET', 'POST'])
@admin_required
def edit_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    if request.method == 'POST':
        try:
            form_data = request.form.to_dict()

            required_fields = ['prime_location_name', 'price', 'address', 'pin_code', 'maximum_number_of_spots']
            for field in required_fields:
                if not form_data.get(field):
                    flash(f'The field {field} is required.', 'error')
                    return render_template('admin/parking/edit_lot.html', lot=lot)

            new_price = float(form_data['price'])
            new_max_spots = int(form_data['maximum_number_of_spots'])

            if new_price <= 0:
                flash('Price must be greater than 0.', 'error')
                return render_template('admin/parking/edit_lot.html', lot=lot)

            if new_max_spots <= 0:
                flash('Maximum number of spots must be greater than 0.', 'error')
                return render_template('admin/parking/edit_lot.html', lot=lot)

            if new_max_spots < lot.maximum_number_of_spots:
                success, message = lot.safely_reduce_spots(new_max_spots)
                if not success:
                    flash(message, 'error')
                    return render_template('admin/parking/edit_lot.html', lot=lot)

            lot.prime_location_name = form_data['prime_location_name']
            lot.price = new_price
            lot.address = form_data['address']
            lot.pin_code = form_data['pin_code']
            lot.maximum_number_of_spots = new_max_spots

            if new_max_spots > len(lot.spots):
                spots_to_add = new_max_spots - len(lot.spots)
                for _ in range(spots_to_add):
                    new_spot = ParkingSpot(lot_id=lot.id, status='A')
                    db.session.add(new_spot)

            db.session.commit()
            flash('Parking lot updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))

        except ValueError:
            flash('Invalid input for price or maximum number of spots. Please enter valid numbers.', 'error')
            return render_template('admin/parking/edit_lot.html', lot=lot)
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating parking lot: {str(e)}', 'error')
            return render_template('admin/parking/edit_lot.html', lot=lot)

    return render_template('admin/parking/edit_lot.html', lot=lot)

@app.route("/admin/delete_parking_lot/<int:lot_id>", methods=['POST'])
@admin_required
def delete_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    try:
        if any(spot.has_active_tickets() for spot in lot.spots):
            flash('Cannot delete parking lot with active tickets.', 'error')
            return redirect(url_for('admin_dashboard'))
            
        db.session.delete(lot)
        db.session.commit()
        flash('Parking lot deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting parking lot: {str(e)}', 'error')
        
    return redirect(url_for('admin_dashboard'))


@app.route("/admin/view_parking_spots/<int:lot_id>")
@admin_required
def view_parking_spots(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
    return render_template('admin/parking/view_spots.html', lot=lot, spots=spots)

@app.route("/admin/view_spot_details/<int:lot_id>/<int:spot_id>")
@admin_required
def view_spot_details(lot_id, spot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    if spot.lot_id != lot_id:
        abort(404)
    
    active_ticket = spot.get_active_ticket()
    
    if not active_ticket:
        flash('No active ticket found for this spot.', 'warning')
        return redirect(url_for('view_parking_spots', lot_id=lot_id))
    
    from datetime import datetime
    current_time = datetime.now()
    duration_hours = (current_time - active_ticket.parking_timestamp).total_seconds() / 3600
    # Ensure minimum charge for 1 hour
    if duration_hours < 1:
        duration_hours = 1.0
    estimated_cost = duration_hours * float(active_ticket.parking_cost_per_unit_time)
    
    return render_template('admin/parking/spot_details.html', 
                         lot=lot, 
                         spot=spot, 
                         active_ticket=active_ticket,
                         duration_hours=duration_hours,
                         estimated_cost=estimated_cost)

@app.route("/admin/delete_parking_spot/<int:lot_id>/<int:spot_id>", methods=['POST'])
@admin_required
def delete_parking_spot(lot_id, spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.lot_id != lot_id:
        abort(404)
    
    if spot.status == 'O':
        flash('Cannot delete an occupied parking spot.', 'error')
    else:
        try:
            db.session.delete(spot)
            db.session.commit()
            flash('Parking spot deleted successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting parking spot: {str(e)}', 'error')
    
    return redirect(url_for('view_parking_spots', lot_id=lot_id))
