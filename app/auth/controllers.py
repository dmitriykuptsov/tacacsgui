# Import flask dependencies
from flask import Blueprint, request, render_template, \
                  flash, g, session, redirect, url_for

# Import password / encryption helper tools
#from werkzeug.security import generate_password_hash, check_password_hash


# Import the database object from the main app module
from app import db

# Import module models (i.e. User)
from app.auth.models import User

# Import tacacs users
from app.tacacs.models import TacacsUser

# Secrets
import secrets

# Password encryption routines
import crypt

# Import utils
from app.utils.tacacs.utils import check_password

# Import regex stuff
import re

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_auth = Blueprint('auth', __name__, url_prefix='/auth')

# Set the route and accepted methods
@mod_auth.route("/signin/", methods=["GET", "POST"])
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

@mod_auth.route("/logout/", methods=["GET"])
def logout():
    session.clear();
    return redirect(url_for('auth.signin'))

@mod_auth.route("/reset_tacacs_password/", methods=["GET", "POST"])
def reset_tacacs_password():
    if request.method == "POST":
        user_name = request.form.get("username", "")
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        new_password_confirm = request.form.get("new_password_confirm", "")
        try:
            tacacs_user = TacacsUser.query.filter_by(name = user_name).one();
        except:
            return render_template("auth/reset_tacacs_password.html", error="User was not found in the database", status=None)
        if crypt.crypt(old_password, tacacs_user.password) != tacacs_user.password:
            return render_template("auth/reset_tacacs_password.html", error="Old password is incorrect", status=None)
        if not re.match(r"[a-zA-Z_$@0-9]{5,16}", new_password):
            return render_template("auth/reset_tacacs_password.html", error="Password is too easy. It should match the regex: [a-zA-Z_$@0-9]{5,16}", status=None)
        if new_password != new_password_confirm:
            return render_template("auth/reset_tacacs_password.html", error="Passwords do not match!", status=None)
        tacacs_user.password = crypt.crypt(new_password, salt=crypt.mksalt(crypt.METHOD_MD5))
        db.session.commit();
        return render_template("auth/reset_tacacs_password.html", error=None, status="Password was changed! Contact your administrator and ask to update the configuration file")
    else:
        return render_template("auth/reset_tacacs_password.html", error=None, status=None)
