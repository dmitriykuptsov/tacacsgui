# Import flask and template operators
from flask import Flask, render_template

# Import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy

# Define the WSGI application object
app = Flask(__name__, static_folder = 'templates/static')

# Configurations
app.config.from_object('config')

# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)

# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
	return render_template('404.html'), 404

# Import a module / component using its blueprint handler variable
from app.auth.controllers import mod_auth
from app.tacacs.controllers import mod_tac_plus 
from app.statistics.controllers import mod_tac_plus_statistiscs

# Register blueprint(s)
app.register_blueprint(mod_auth)
app.register_blueprint(mod_tac_plus)
app.register_blueprint(mod_tac_plus_statistiscs)
