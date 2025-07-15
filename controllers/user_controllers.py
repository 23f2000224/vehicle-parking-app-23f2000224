from .controller_common import *

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    user_reservations = ReserveParkingSpot.query.filter_by(user_id=current_user.id).limit(3).all()
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        parking_lots = ParkingSpot.query.filter(
            (ParkingSpot.location.ilike(f'%{search_query}%')) |
            (ParkingSpot.pincode.ilike(f'%{search_query}%'))
        ).limit(3).all()
        return render_template('user/dashboard.html', reservations=user_reservations, search_query=search_query, parking_lots=parking_lots, user=current_user.username)

    return render_template('user/dashboard.html', reservations=user_reservations, user=current_user.username)


@app.route("/user/summary", methods=['GET', 'POST'])
@login_required
def user_summary():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        user_reservations = ReserveParkingSpot.query.filter_by(user_id=current_user.id).all()
        return render_template('user/summary.html',
        reservations=user_reservations, start_date=start_date, end_date=end_date, user = current_user.username)
    else:
        user_reservations = ReserveParkingSpot.query.filter_by(user_id=current_user.id).all()
        return render_template('user/summary.html', reservations=user_reservations, user = current_user.username)

    
@app.route("/user/parking/book")
def book_parking():
    if request.method == 'POST':
        pass
    return render_template('user/parking/book.html', user=current_user.username)


@app.route("/user/parking/release")
def release_parking():
    if request.method == 'POST':
        pass
    return render_template('user/parking/release.html', user=current_user.username)