from functools import wraps
from .controller_common import *

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    parking_lots = ParkingLot.query.all()
    return render_template('admin/dashboard.html', parking_lots=parking_lots)


@app.route('/admin/summary', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_summary():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        parking_lots = ParkingLot.query.all()
        return render_template('admin/summary.html', parking_lots=parking_lots, start_date=start_date, end_date=end_date)
    else:
        parking_lots = ParkingLot.query.all()
        return render_template('admin/summary.html', parking_lots=parking_lots)


@app.route('/admin/search', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_search():
    if request.method == 'POST':
        search_type  = request.form.get('search_type')
        if search_type == 'parking_lot':
            search_query = request.form.get('search_query')
            parking_lots = ParkingLot.query.filter(ParkingLot.name.ilike(f'%{search_query}%')).all()
            return render_template('admin/search.html', parking_lots=parking_lots, search_query=search_query)
        elif search_type == 'user':
            search_query = request.form.get('search_query')
            users = User.query.filter(User.username.ilike(f'%{search_query}%')).all()
            return render_template('admin/search.html', users=users, search_query=search_query)
    return render_template('admin/search.html')

    
@app.route("/admin/users")
@login_required
@admin_required
def users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)


@app.route("/admin/add_parking_lot", methods=['GET', 'POST'])
@login_required
@admin_required
def add_parking_lot():
    if request.method == 'POST':
        prime_location_name = request.form['prime_location_name']
        price = request.form['price']
        address = request.form['address']
        pin_code = request.form['pin_code']
        maximum_number_of_spots = request.form['maximum_number_of_spots']

        new_lot = ParkingLot(
            prime_location_name=prime_location_name,
            price=price,
            address=address,
            pin_code=pin_code,
            maximum_number_of_spots=maximum_number_of_spots
        )
        db.session.add(new_lot)
        db.session.commit()
        flash('Parking lot added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/parking/create_lot.html')

@app.route("/admin/edit_parking_lot/<int:lot_id>", methods=['GET', 'POST'])
@login_required
@admin_required
def edit_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    if request.method == 'POST':
        lot.prime_location_name = request.form['prime_location_name']
        lot.price = request.form['price']
        lot.address = request.form['address']
        lot.pin_code = request.form['pin_code']
        lot.maximum_number_of_spots = request.form['maximum_number_of_spots']

        db.session.commit()
        flash('Parking lot updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/parking/edit_lot.html', lot=lot)

@app.route("/admin/delete_parking_lot/<int:lot_id>", methods=['POST'])
@login_required
@admin_required
def delete_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    db.session.delete(lot)
    db.session.commit()
    flash('Parking lot deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))