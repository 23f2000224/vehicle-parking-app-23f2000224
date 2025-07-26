from flask import current_app as app, jsonify, request, render_template, flash, redirect, url_for
from models import db
from flask_login import login_user, login_required, current_user
from models.models import ParkingLot, ParkingSpot, User, Ticket
from werkzeug.security import generate_password_hash
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.dates import DateFormatter
import os
from functools import wraps
