from flask import current_app as app, jsonify, request, render_template, flash, redirect, url_for
from models import db
from flask_login import login_user, login_required, current_user
from models.models import ParkingLot, ParkingSpot, User, ReserveParkingSpot
from werkzeug.security import generate_password_hash

