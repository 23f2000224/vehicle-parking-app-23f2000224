from .controller_common import *


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')
        
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form_data = request.form.to_dict()

        # Check if the username already exists
        if User.query.filter_by(username=form_data['username']).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        # Create new user with hashed password
        new_user = User(
            username=form_data['username'],
            password_hash=generate_password_hash(form_data['password']),
            fullname=form_data['fullname'],
            address=form_data['address'],
            pincode=form_data['pincode'],
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# edit profile 
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        current_user.username = form_data['username']
        if form_data['password']:
            current_user.password_hash = generate_password_hash(form_data['password'])
        current_user.fullname = form_data['fullname']
        current_user.address = form_data['address']
        current_user.pincode = form_data['pincode']
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('edit_profile.html', user=current_user)


@app.route('/logout')
@login_required
def logout():
    from flask_login import logout_user
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))