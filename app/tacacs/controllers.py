from flask import Blueprint, request, render_template, \
                  flash, g, session, redirect, url_for, jsonify
from app import db

# System libraries
import os
import re
import secrets
from datetime import datetime

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

# System
import sys
# Logging
import logging

# Configure logging to console and file
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("tacacs.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Blueprint
mod_tac_plus = Blueprint('tac_plus', __name__, url_prefix='/tac_plus')

@mod_tac_plus.route('/configurations/', methods=['GET'])
def configurations():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	configurations = Configuration.query.all();
	return render_template("tacacs/configurations.html", configurations=configurations, status = request.args.get("status", None));

@mod_tac_plus.route('/add_configuration/', methods=['GET', 'POST'])
def add_configuration():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		return render_template("tacacs/add_configuration.html");
	else:
		configuration = Configuration();
		configuration.name = request.form.get("configuration_name", "");
		db.session.add(configuration);
		db.session.commit();
		return redirect(url_for("tac_plus.configurations"));

@mod_tac_plus.route('/edit_configuration/', methods=['GET', 'POST'])
def edit_configuration():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		try:
			configuration = Configuration.query.filter_by(id=request.args.get("config_id", None)).one();
			configuration_groups = ConfigurationGroups.query.filter_by(configuration_id = configuration.id) \
				.join(Group) \
				.all()
			groups = []
			for configuration_group in configuration_groups:
				groups.append(configuration_group.group);
			configuration_users = ConfigurationUsers.query.filter_by(configuration_id = configuration.id) \
				.join(TacacsUser) \
				.all()
			users = []
			for configuration_user in configuration_users:
				users.append(configuration_user.user);
			return render_template("tacacs/edit_configuration.html", configuration=configuration, groups=groups, users=users);
		except Exception as e:
			logging.debug(e);
			return redirect(url_for("tac_plus.configurations"));
	else:
		configuration = Configuration.query.filter_by(id=request.form.get("configuration_id", None)).one();
		configuration.name = request.form.get("name", "");
		db.session.commit();
		return redirect(url_for("tac_plus.configurations"));

@mod_tac_plus.route('/delete_configuration/', methods=['GET'])
def delete_configuration():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))

	try:
		configuration = Configuration.query.filter_by(id=request.args.get("config_id", None)).one();
		db.session.delete(configuration)
		db.session.commit();
	except:
		pass
	return redirect(url_for("tac_plus.configurations"));

@mod_tac_plus.route("/groups/", methods=["GET"])
def groups():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	groups = Group.query.all();
	return render_template("tacacs/groups.html", groups = groups);

@mod_tac_plus.route("/users/", methods=["GET"])
def users():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	users = TacacsUser.query.all();
	return render_template("tacacs/users.html", users = users)

@mod_tac_plus.route("/commands/", methods=["GET"])
def commands():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	commands = Command.query.all();
	return render_template("tacacs/commands.html", commands = commands)

@mod_tac_plus.route("/delete_command/", methods=["GET"])
def delete_command():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	try:
		command = Command.query.filter_by(id=request.args.get("command_id", "")).one();
		if command:
			db.session.delete(command);
			db.session.commit();
	except:
		pass
	return redirect(url_for('tac_plus.commands'))

@mod_tac_plus.route("/edit_command/", methods=["GET", "POST"])
def edit_command():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		try:
			command = Command.query.filter_by(id=request.args.get("command_id", "")).one();
			return render_template("tacacs/edit_command.html", command=command)
		except:
			return redirect(url_for('tac_plus.commands'))
	else:
		try:
			command = Command.query.filter_by(id=request.form.get("command_id", "")).one();
			command.name = request.form.get("command_name", "");
			command.permit_regex = request.form.get("permit_regex", "");
			command.deny_regex = request.form.get("deny_regex", "");
			command.permit_message = request.form.get("permit_message", "");
			command.deny_message = request.form.get("deny_message", "");		
			db.session.commit();
			return redirect(url_for('tac_plus.commands'))
		except Exception as e: 
			logging.debug(e);
			return redirect(url_for('tac_plus.commands'))
		return redirect(url_for('tac_plus.commands'))	
	


@mod_tac_plus.route("/add_command/", methods=["GET", "POST"])
def add_command():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		return render_template("tacacs/add_command.html")
	else:
		command = Command();
		command.name = request.form.get("command_name", "")
		command.permit_regex = request.form.get("permit_regex", "")
		command.permit_message = request.form.get("permit_message", "")
		command.deny_regex = request.form.get("deny_regex", "")
		command.deny_message = request.form.get("deny_message", "")
		db.session.add(command);
		db.session.commit();
		return redirect(url_for('tac_plus.commands'))


@mod_tac_plus.route("/add_group/", methods=["GET", "POST"])
def add_group():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		return render_template("tacacs/add_group.html")
	else:
		group = Group();
		group.name = request.form.get("group_name", "")
		group.valid_until = datetime.strptime(request.form.get("valid_until", ""), "%Y-%m-%d")
		group.cmd_default_policy = request.form.get("cmd_default_policy", "")
		group.default_privilege = request.form.get("default_privilege", "")
		group.is_enable_pass = True if request.form.get("is_enable_pass", "") == "on" else False;
		group.enable_pass = request.form.get("enable_pass", "");
		db.session.add(group);
		db.session.commit();
		return redirect(url_for('tac_plus.groups'))

@mod_tac_plus.route("/delete_group/", methods=["GET"])
def delete_group():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	try:
		group = Group.query.filter_by(id=request.args.get("group_id", "")).one();
		if group:
			db.session.delete(group);
			db.session.commit();
	except:
		pass
	return redirect(url_for('tac_plus.groups'))

@mod_tac_plus.route("/add_command_to_group/", methods=["GET"])
def add_command_to_group():
	if not session.get("user_id", None):
		return jsonify([]), 403;
	found = False
	try:
		group_command = GroupCommands.query.filter_by(group_id = request.args.get("group_id", None), \
			command_id = request.args.get("command_id", None)).all();
		if len(group_command) > 0:
			found = True;
	except Exception as e:
		pass
	if found:
		return jsonify([]);
	group_command = GroupCommands();
	group_command.group_id = request.args.get("group_id", None)
	group_command.command_id = request.args.get("command_id", None)
	db.session.add(group_command)
	db.session.commit();
	return jsonify([]);

@mod_tac_plus.route("/add_group_to_configuration/", methods=["GET"])
def add_group_to_configuration():
	if not session.get("user_id", None):
		return jsonify([]), 403;
	found = False
	try:
		group_configuration = ConfigurationGroups.query.filter_by(configuration_id = request.args.get("config_id", None), \
			group_id = request.args.get("group_id", None)).all();
		if len(group_configuration) > 0:
			found = True;
	except Exception as e:
		pass
	if found:
		return jsonify([]);
	group_configuration = ConfigurationGroups();
	group_configuration.group_id = request.args.get("group_id", None)
	group_configuration.configuration_id = request.args.get("config_id", None)
	db.session.add(group_configuration)
	db.session.commit();
	return jsonify([]);

@mod_tac_plus.route("/add_user_to_configuration/", methods=["GET"])
def add_user_to_configuration():
	if not session.get("user_id", None):
		return jsonify([]), 403;
	found = False
	try:
		user_configuration = ConfigurationUsers.query.filter_by(configuration_id = request.args.get("config_id", None), \
			user_id = request.args.get("user_id", None)).all();
		if len(user_configuration) > 0:
			found = True;
	except Exception as e:
		logging.debug(e)
		pass
	if found:
		return jsonify([]);
	user_configuration = ConfigurationUsers();
	user_configuration.user_id = request.args.get("user_id", None)
	user_configuration.configuration_id = request.args.get("config_id", None)
	db.session.add(user_configuration);
	db.session.commit();
	return jsonify([]);

@mod_tac_plus.route("/delete_command_from_group/", methods=["GET"])
def delete_command_from_group():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if not session.get("csrf_token", None):
		return jsonify([]), 403;
	#if request.args.get("csrf_token", None) != session["csrf_token"]:
	#	return jsonify([]), 403;
	group_command = GroupCommands.query.filter_by(group_id=request.args.get("group_id", ""), \
		command_id=request.args.get("command_id", "")).one();
	if group_command:
		db.session.delete(group_command);
		db.session.commit();
	return redirect(url_for('tac_plus.edit_group', group_id = request.args.get("group_id", "")))

@mod_tac_plus.route("/delete_group_from_configuration/", methods=["GET"])
def delete_group_from_configuration():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if not session.get("csrf_token", None):
		return jsonify([]), 403;
	#if request.args.get("csrf_token", None) != session["csrf_token"]:
	#	return jsonify([]), 403;
	group_configuration = ConfigurationGroups.query.filter_by(group_id=request.args.get("group_id", ""), \
		configuration_id=request.args.get("config_id", "")).one();
	if group_configuration:
		db.session.delete(group_configuration);
		db.session.commit();
	return redirect(url_for('tac_plus.edit_configuration', config_id = request.args.get("config_id", "")))

@mod_tac_plus.route("/delete_user_from_configuration/", methods=["GET"])
def delete_user_from_configuration():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if not session.get("csrf_token", None):
		return jsonify([]), 403;
	#if request.args.get("csrf_token", None) != session["csrf_token"]:
	#	return jsonify([]), 403;
	user_configuration = ConfigurationUsers.query.filter_by(user_id=request.args.get("user_id", ""), \
		configuration_id=request.args.get("config_id", "")).one();
	if user_configuration:
		db.session.delete(user_configuration);
		db.session.commit();
	return redirect(url_for('tac_plus.edit_configuration', config_id = request.args.get("config_id", "")))

@mod_tac_plus.route("/add_group_to_user/", methods=["GET"])
def add_group_to_user():
	if not session.get("user_id", None):
		return jsonify([]), 403;
	if not session.get("csrf_token", None):
		return jsonify([]), 403;
	#if request.args.get("csrf_token", None) != session["csrf_token"]:
	#	return jsonify([]), 403;
	user_groups = TacacsUserGroups()
	user_groups.user_id = request.args.get("user_id", None)
	user_groups.group_id = request.args.get("group_id", None)
	db.session.add(user_groups)
	db.session.commit();
	return jsonify([]);

@mod_tac_plus.route("/delete_group_from_user/", methods=["GET"])
def delete_group_from_user():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	user_group = TacacsUserGroups.query.filter_by(user_id=request.args.get("user_id", ""), \
		group_id=request.args.get("group_id", "")).one();
	if user_group:
		db.session.delete(user_group);
		db.session.commit();
	return redirect(url_for('tac_plus.edit_user', user_id = request.args.get("user_id", "")))

@mod_tac_plus.route("/add_user/", methods=["GET", "POST"])
def add_user():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		return render_template("tacacs/add_user.html")
	else:
		user = TacacsUser();
		user.name = request.form.get("user_name", "")
		user.password = request.form.get("password", "")
		db.session.add(user);
		db.session.commit();
		return redirect(url_for('tac_plus.users'))

@mod_tac_plus.route("/delete_user/", methods=["GET"])
def delete_user():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	try:
		user_configurations = ConfigurationUsers.query.filter_by(user_id=request.args.get("user_id", "")).all();
		for user_configuration in user_configurations:
			db.session.delete(user_configuration);
			db.session.commit();
		user_groups = TacacsUserGroups.query.filter_by(user_id=request.args.get("user_id", "")).all();
		for user_group in user_groups:
			db.session.delete(user_group)
			db.session.commit();
		user = TacacsUser.query.filter_by(id=request.args.get("user_id", "")).one();
		if user:
			db.session.delete(user);
			db.session.commit();
	except Exception as e:
		pass
	return redirect(url_for('tac_plus.users'));

@mod_tac_plus.route("/groups_json/", methods=["GET", "POST"])
def groups_json():
	if not session.get("user_id", None):
		return jsonify({}), 403;
	try:
		groups = Group.query.filter(Group.name.like("%{}%".format(request.args.get("group", "")))).all();
		result = [];
		for group in groups:
			result.append({
				"id": group.id,
				"name": group.name
				});
		return jsonify(result);
	except:
		return jsonify([]);

@mod_tac_plus.route("/users_json/", methods=["GET"])
def users_json():
	if not session.get("user_id", None):
		return jsonify({}), 403;
	try:
		users = TacacsUser.query.filter(TacacsUser.name.like("%{}%".format(request.args.get("user", "")))).all();
		result = [];
		for user in users:
			result.append({
				"id": user.id,
				"name": user.name
				});
		return jsonify(result);
	except:
		return jsonify([]);


@mod_tac_plus.route("/edit_user/", methods=["GET", "POST"])
def edit_user():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		try:
			user = TacacsUser.query.filter_by(id=request.args.get("user_id", "")).one();
			user_groups = TacacsUserGroups.query.filter_by(user_id = user.id) \
				.join(Group) \
				.all()
			groups = []
			for user_group in user_groups:
				groups.append(user_group.group);
			return render_template("tacacs/edit_user.html", user=user, groups = groups)
		except Exception as e:
			logging.debug(e);
			return redirect(url_for('tac_plus.users'))
	else:
		try:
			user = TacacsUser.query.filter_by(id=request.form.get("user_id", "")).one();
			user.name = request.form.get("user_name", "");
			user.password = request.form.get("password", "");
			db.session.commit();
			return redirect(url_for('tac_plus.users'))
		except Exception as e:
			logging.debug(e);
			return redirect(url_for('tac_plus.users'))
		return redirect(url_for('tac_plus.users'))

@mod_tac_plus.route("/commands_json/", methods=["GET", "POST"])
def commands_json():
	if not session.get("user_id", None):
		return jsonify({}), 403;
	try:
		commands = Command.query.filter(Command.name.like("%{}%".format(request.args.get("cmd", "")))).all();
		result = [];
		for command in commands:
			result.append({
				"id": command.id,
				"name": command.name,
				"permit_regex": command.permit_regex,
				"deny_regex": command.deny_regex
				});
		return jsonify(result);
	except:
		return jsonify([])

@mod_tac_plus.route("/add_acl_to_group/", methods=["GET"])
def add_acl_to_group():
	if not session.get("user_id", None):
		return jsonify({}), 403;
	try:
		acl = GroupACL()
		acl.access = request.args.get("acl_access", "")
		acl.group_id = request.args.get("group_id", "")
		acl.ip = request.args.get("acl_ip", "")
		acl.mask = request.args.get("acl_mask", "")
		db.session.add(acl)
		db.session.commit();
		return jsonify({});
	except Exception as e:
		print(e)
		return jsonify({})

@mod_tac_plus.route("/delete_acl_from_group/", methods=["GET", "POST"])
def delete_acl_from_group():
	if not session.get("user_id", None):
		return jsonify({}), 403;
	try:
		acl = GroupACL.query.filter_by(group_id = request.args.get("group_id", ""), \
								 id = request.args.get("acl_id", "")).first()
		db.session.delete(acl)
		db.session.commit();
		return jsonify({});
	except:
		return jsonify({})

@mod_tac_plus.route("/edit_group/", methods=["GET", "POST"])
def edit_group():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		try:
			group = Group.query.filter_by(id=request.args.get("group_id", "")).one();
			group_commands = GroupCommands.query.filter_by(group_id = group.id) \
				.join(Command) \
				.all()
			group_acls = GroupACL.query.filter_by(group_id = request.args.get("group_id", "")).all()	
			
			commands = []
			for group_command in group_commands:
				commands.append(group_command.command);
			
			acls = []
			for acl in group_acls:
				acls.append(acl)

			group.valid_until = group.valid_until.strftime("%Y-%m-%d");
			
			return render_template("tacacs/edit_group.html", group=group, commands = commands, acls=acls)
		except Exception as e:
			print(e)
			return redirect(url_for('tac_plus.groups'))
	else:
		try:
			group = Group.query.filter_by(id=request.form.get("group_id", "")).one();
			group.name = request.form.get("group_name", "");
			group.valid_until = datetime.strptime(request.form.get("valid_until", ""), "%Y-%m-%d")
			group.cmd_default_policy = request.form.get("cmd_default_policy", "");
			group.default_privilege = request.form.get("default_privilege", "");
			group.is_enable_pass = True if request.form.get("is_enable_pass", "") == "on" else False;
			group.enable_pass = request.form.get("enable_pass", "");
			db.session.commit();
			return redirect(url_for('tac_plus.groups'))
		except Exception as e:
			return redirect(url_for('tac_plus.groups'))
		return redirect(url_for('tac_plus.groups'))

@mod_tac_plus.route('/system/', methods=['GET', 'POST'])
def system():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		system = System.query.filter().first();
		if not system:
			system = System();
			db.session.add(system);
			db.session.commit();
		return render_template("tacacs/system.html", system=system);
	else:
		system = System.query.filter_by(id=request.form.get("system_id", "")).one();
		system.log_files_path = request.form.get("log_files_path", "/var/log/tac_plus/");
		system.cfg_file_path = request.form.get("cfg_file_path", "/usr/local/etc/tac_plus.cfg");
		system.port_number = int(request.form.get("port_number", 49))
		system.mavis_exec = request.form.get("mavis_exec", "/usr/local/lib/mavis/mavis_tacplus_passwd.pl")
		system.host_ip = request.form.get("host_ip", "0.0.0.0/0")
		system.auth_key = request.form.get("auth_key", "my key")
		system.login_backend = "mavis";
		db.session.commit();
		return render_template("tacacs/system.html", system=system);

@mod_tac_plus.route("/verify_configuration/", methods=["GET"])
def verify_configuration():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	configuration_id = request.args.get("config_id", "")
	if not re.match("[1-9]{1}[0-9]*", configuration_id):
		return redirect(url_for("tac_plus.configurations"));
	system = System.query.first();
	if not system:
		logging.debug("Exiting no system configuration found...")
		return redirect(url_for("tac_plus.configurations"));
	configuration = None;
	try:
		configuration = Configuration.query.filter_by(id = configuration_id).one();
	except Exception as e:
		logging.debug(e)
		return redirect(url_for("tac_plus.configurations"));
	configuration_groups = ConfigurationGroups.query.filter_by(configuration_id = configuration_id).all();

	groups = [];
	for configuration_group in configuration_groups:
		group = {
			"group": configuration_group.group,
			"commands": []
		}
		commands = GroupCommands.query.filter_by(group_id = configuration_group.group.id).all();
		for command in commands:
			group["commands"].append(command.command);
		groups.append(group);

	configuration_users = ConfigurationUsers.query.filter_by(configuration_id = configuration_id).all();
	users = [];
	for configuration_user in configuration_users:
		user = {
			"user": configuration_user.user,
			"groups": []
		}
		user_groups = TacacsUserGroups.query.filter_by(user_id = configuration_user.user.id)
		for user_group in user_groups:
			user["groups"].append(user_group.group);
		users.append(user);
	
	temporary_configuration_file = "/var/tmp/" + secrets.token_hex(nbytes=16) + ".cfg";
	#print("Doing %s " % (temporary_configuration_file, ));

	build_configuration_file(system, 
		configuration, 
		groups, 
		users, 
		"app/templates/tacacs/configuration.template", 
		"app/templates/tacacs/user.template",
		"app/templates/tacacs/group.template",
		"app/templates/tacacs/command.template", 
		temporary_configuration_file)
	status = "Build status: Configuration file is OK!";
	if not verify_the_configuration(temporary_configuration_file):
		status = "STATUS: Configuration file contains errors"
	os.remove(temporary_configuration_file);
	return redirect(url_for("tac_plus.configurations", status = status));

@mod_tac_plus.route("/deploy_configuration/", methods=["GET"])
def deploy_configuration_route():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	configuration_id = request.args.get("config_id", "")
	if not re.match("[1-9]{1}[0-9]*", configuration_id):
		return redirect(url_for("tac_plus.configurations"));
	configurations = Configuration.query.all();
	for configuration in configurations:
		configuration.deployed = False
		db.session.commit();
	system = System.query.first();
	if not system:
		logging.debug("Exiting no system configuration found...")
		return redirect(url_for("tac_plus.configurations"));
	configuration = None;
	try:
		configuration = Configuration.query.filter_by(id = configuration_id).one();
		configuration.deployed = True;
		db.session.commit();
	except Exception as e:
		return redirect(url_for("tac_plus.configurations"));
	configuration_groups = ConfigurationGroups.query.filter_by(configuration_id = configuration_id).all();
	groups = [];
	for configuration_group in configuration_groups:
		group = {
			"group": configuration_group.group,
			"commands": []
		}
		commands = GroupCommands.query.filter_by(group_id = configuration_group.group.id).all();
		for command in commands:
			group["commands"].append(command.command);
		groups.append(group);

	configuration_users = ConfigurationUsers.query.filter_by(configuration_id = configuration_id).all();
	users = [];
	for configuration_user in configuration_users:
		user = {
			"user": configuration_user.user,
			"groups": []
		}
		user_groups = TacacsUserGroups.query.filter_by(user_id = configuration_user.user.id)
		for user_group in user_groups:
			user["groups"].append(user_group.group);
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
		temporary_configuration_file)
	status = "Build status: Configuration file is OK! It will roughly take 1 minute for the configuration to take effect";
	if not verify_the_configuration(temporary_configuration_file):
		status = "STATUS: Configuration file contains errors"
		return redirect(url_for("tac_plus.configurations", status = status)); 
	os.rename(temporary_configuration_file, "/var/tmp/tac_plus.cfg"); 
	#status = "STATUS: Configuration was not deployed"
	#if deploy_configuration(temporary_configuration_file):
	#	status = "STATUS: Configuration was deployed. Everthing is OK!"
	#os.remove(temporary_configuration_file);
	return redirect(url_for("tac_plus.configurations", status = status));
