from .controller_common import *

def check_admin():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('login'))
    return None


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('login'))

    parking_lots = ParkingLot.query.all()
    return render_template('admin/dashboard.html', parking_lots=parking_lots)


@app.route('/admin/summary', methods=['GET', 'POST'])
@login_required
def admin_summary():
    check_admin()
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
def admin_search():
    check_admin()
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
def users():
    check_admin()
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)


#summary done 
#dashboard done
#search in the works