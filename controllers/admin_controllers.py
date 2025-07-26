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
            plt.pie(revenue_data.values(), labels=revenue_data.keys(), autopct='%1.1f%%', pctdistance=0.85)
            plt.gca().add_artist(plt.Circle((0,0), 0.70, fc='white'))
            plt.text(0, 0, f'₹{total_revenue:.2f}\nTotal', ha='center', va='center')
            plt.title('Revenue Distribution by Parking Lot')

            # Save revenue plot
            revenue_img = io.BytesIO()
            plt.savefig(revenue_img, format='png', bbox_inches='tight')
            revenue_img.seek(0)
            plt.close() # Close the plot to free up memory

            revenue_plot = base64.b64encode(revenue_img.getvalue()).decode()
        else:
            # Log a warning if no revenue to plot, and keep revenue_plot as None
            app.logger.warning("Total revenue is zero. Skipping revenue distribution plot generation.")
            flash('No revenue generated yet to display a revenue distribution chart.', 'info')
       

        return render_template(
            'admin/summary.html',
            revenue_plot=revenue_plot
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
    """Create parking spots for a given parking lot"""
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

            # Validate required fields
            required_fields = ['prime_location_name', 'price', 'address', 'pin_code', 'maximum_number_of_spots']
            for field in required_fields:
                if not form_data.get(field):
                    flash(f'The field {field} is required.', 'error')
                    return render_template('admin/parking/create_lot.html')

            # Convert to appropriate types and validate values
            prime_location_name = form_data['prime_location_name']
            price = float(form_data['price'])
            address = form_data['address']
            pin_code = form_data['pin_code']
            maximum_number_of_spots = int(form_data['maximum_number_of_spots'])

            # Validate price and maximum_number_of_spots
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

            # Create parking spots for the new lot
            # Assuming create_parking_spots function exists and takes the new_lot object
            create_parking_spots(new_lot)

            flash('Parking lot and spots created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except ValueError:
            # This will catch errors if price or max_spots cannot be converted to float/int
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

            # Validate required fields
            required_fields = ['prime_location_name', 'price', 'address', 'pin_code', 'maximum_number_of_spots']
            for field in required_fields:
                if not form_data.get(field):
                    flash(f'The field {field} is required.', 'error')
                    return render_template('admin/parking/edit_lot.html', lot=lot)

            # Convert to appropriate types and validate values
            new_price = float(form_data['price'])
            new_max_spots = int(form_data['maximum_number_of_spots'])

            # Validate price and maximum_number_of_spots
            if new_price <= 0:
                flash('Price must be greater than 0.', 'error')
                return render_template('admin/parking/edit_lot.html', lot=lot)

            if new_max_spots <= 0:
                flash('Maximum number of spots must be greater than 0.', 'error')
                return render_template('admin/parking/edit_lot.html', lot=lot)

            # Handle spot reduction if needed
            if new_max_spots < lot.maximum_number_of_spots:
                success, message = lot.safely_reduce_spots(new_max_spots)
                if not success:
                    flash(message, 'error')
                    return render_template('admin/parking/edit_lot.html', lot=lot)

            # Update lot details
            lot.prime_location_name = form_data['prime_location_name']
            lot.price = new_price # Use the validated price
            lot.address = form_data['address']
            lot.pin_code = form_data['pin_code']
            lot.maximum_number_of_spots = new_max_spots # Use the validated spots

            # If increasing spots, create new ones
            if new_max_spots > len(lot.spots):
                spots_to_add = new_max_spots - len(lot.spots)
                for _ in range(spots_to_add):
                    new_spot = ParkingSpot(lot_id=lot.id, status='A')
                    db.session.add(new_spot)

            db.session.commit()
            flash('Parking lot updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))

        except ValueError:
            # This will catch errors if price or max_spots cannot be converted to float/int
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
        # Check if lot has any active tickets
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
    return render_template('admin/parking/spot_details.html', lot=lot, spot=spot, active_ticket=active_ticket)

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
