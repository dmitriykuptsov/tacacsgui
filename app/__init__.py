# Import flask and template operators
from flask import Flask, render_template, redirect, url_for

from apscheduler.schedulers.background import BackgroundScheduler

# System libraries
import os
import re
import secrets
from datetime import datetime

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

@app.route("/")
def index():
	return redirect(url_for("auth.signin"))

# Import a module / component using its blueprint handler variable
from app.auth.controllers import mod_auth
from app.tacacs.controllers import mod_tac_plus
from app.statistics.controllers import mod_tac_plus_statistiscs

# Register blueprint(s)
app.register_blueprint(mod_auth)
app.register_blueprint(mod_tac_plus)
app.register_blueprint(mod_tac_plus_statistiscs)

# Database models
from app.tacacs.models import System
from app.tacacs.models import Configuration
from app.tacacs.models import ConfigurationGroups
from app.tacacs.models import ConfigurationUsers
from app.tacacs.models import Group
from app.tacacs.models import GroupCommands
from app.tacacs.models import TacacsUserGroups
from app.tacacs.models import Command
from app.tacacs.models import TacacsUser
from app.tacacs.models import UserACL
from app.tacacs.models import GroupACL

# Utils
from app.utils.tacacs.utils import encrypt_password
from app.utils.tacacs.utils import build_configuration_file, verify_the_configuration, deploy_configuration

# Automatically deploys the configuration every 1 minute
def auto_deploy():
	with app.app_context():

		first_configuration_id = None;
		configuration_id = None;
		configurations = Configuration.query.all();
		for configuration in configurations:
			if not first_configuration_id:
				first_configuration_id = configuration.id;
			if configuration.deployed:
				configuration_id = configuration.id;
			configuration.deployed = False
			db.session.commit();
		if not configuration_id:
			configuration_id = first_configuration_id;
		system = System.query.first();
		if not system:
			print("Exiting no system configuration found...")
			return;
		configuration = None;
		try:
			configuration = Configuration.query.filter_by(id = configuration_id).one();
			configuration.deployed = True;
			db.session.commit();
		except Exception as e:
			return;
		configuration_groups = ConfigurationGroups.query.filter_by(configuration_id = configuration_id).all();
		groups = [];
		for configuration_group in configuration_groups:
			group = {
				"group": configuration_group.group,
				"commands": [],
				"acls": []
			}
			commands = GroupCommands.query.filter_by(group_id = configuration_group.group.id).all();
			for command in commands:
				group["commands"].append(command.command);
			acls = GroupACL.query.filter_by(group_id = configuration_group.group.id).all();
			for acl in acls:
				group["acls"].append(acl);
			groups.append(group);

		configuration_users = ConfigurationUsers.query.filter_by(configuration_id = configuration_id).all();
		users = [];
		for configuration_user in configuration_users:
			user = {
				"user": configuration_user.user,
				"groups": [],
				"acls": []
			}
			user_groups = TacacsUserGroups.query.filter_by(user_id = configuration_user.user.id)
			for user_group in user_groups:
				user["groups"].append(user_group.group);
			acls = UserACL.query.filter_by(user_id = configuration_user.user.id).all();
			for acl in acls:
				user["acls"].append(acl);
			users.append(user);

		temporary_configuration_file = "/var/tmp/" + secrets.token_hex(nbytes=16) + ".cfg";

		build_configuration_file(system, 
			configuration, 
			groups, 
			users, 
			"app/templates/tacacs/configuration.template", 
			"app/templates/tacacs/user.template",
			"app/templates/tacacs/group.template",
			"app/templates/tacacs/command.template", 
			temporary_configuration_file);
		if not verify_the_configuration(temporary_configuration_file):
			return; 
		os.rename(temporary_configuration_file, "/var/tmp/tac_plus.cfg");

sched = BackgroundScheduler(daemon=True);
sched.add_job(auto_deploy, "interval", minutes=1);
sched.start();
