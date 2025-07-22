from .controller_common import *

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    records = Ticket.query.filter_by(user_id=current_user.id).limit(3).all()
    return render_template('user/dashboard.html', records=records, user=current_user.username)

@app.route('/user/search', methods=['GET', 'POST'])
@login_required
def user_search():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        parking_lots = ParkingSpot.query.filter(
            (ParkingSpot.location.ilike(f'%{search_query}%')) |
            (ParkingSpot.pincode.ilike(f'%{search_query}%'))
        ).all()
        return render_template('user/search.html', parking_lots=parking_lots, search_query=search_query, user=current_user.username)
    
    return render_template('user/search.html', user=current_user.username)

@app.route("/user/summary", methods=['GET', 'POST'])
@login_required
def user_summary():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        user_tickets = Ticket.query.filter_by(user_id=current_user.id).all()
        return render_template('user/summary.html',
        reservations=user_tickets, start_date=start_date, end_date=end_date, user=current_user.username)
    else:
        user_tickets = Ticket.query.filter_by(user_id=current_user.id).all()
        return render_template('user/summary.html', reservations=user_tickets, user=current_user.username)

    
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