# Import flask dependencies
from flask import Blueprint, request, render_template, \
                  flash, g, session, redirect, url_for

# Import password / encryption helper tools
#from werkzeug.security import generate_password_hash, check_password_hash


# Import the database object from the main app module
from app import db

# Import module models (i.e. User)
from app.auth.models import User

# Secrets
import secrets

# Import utils
from app.utils.tacacs.utils import check_password

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_auth = Blueprint('auth', __name__, url_prefix='/auth')

# Set the route and accepted methods
@mod_auth.route('/signin/', methods=['GET', 'POST'])
def signin():
    error = None;
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username", None)).first()
        if user and check_password(user.password, user.salt.encode("UTF-8"), request.form.get("password", "").encode("UTF-8")):
            session["user_id"] = user.id
            session["csrf_token"] = secrets.token_hex(nbytes=16)
            flash('Welcome %s' % user.username)
            return redirect(url_for('tac_plus.configurations'))
        error = 'Wrong username or password'
    return render_template("auth/signin.html", error=error)

@mod_auth.route('/logout/', methods=['GET'])
def logout():
    session.clear();
    return redirect(url_for('auth.signin'))