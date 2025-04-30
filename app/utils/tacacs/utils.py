import crypt
import sys
import subprocess
import hashlib
from datetime import datetime

def encrypt_password(password):
	return crypt.crypt(password, crypt.mksalt(crypt.METHOD_MD5))

def csrf_token():
	return secrets.token_hex(nbytes=16)

def is_valid_session(session, token):
	if not session.get("scrf_token", None):
		return False
	if session.get("scrf_token", None) != token:
		return False
	return True;

def check_password(password_hash, salt, password):
	m = hashlib.sha256()
	m.update(password + salt)
	obtained = m.hexdigest();
	return obtained == password_hash

def build_configuration_file(
	system, configuration, 
	groups, users, config_template_file, 
	user_template_file, group_template_file, 
	command_template_file, output_file):
	"""
	Builds configuration file
	"""
	config_template = open(config_template_file, "r").read();
	group_template = open(group_template_file, "r").read();
	user_template = open(user_template_file, "r").read();
	command_template = open(command_template_file, "r").read();

	config_template = config_template.replace("##listen_port", str(system.port_number))
	config_template = config_template.replace("##authentication_log", "/".join([system.log_files_path, "authentication.log"]))
	config_template = config_template.replace("##accounting_log", "/".join([system.log_files_path, "accounting.log"]))
	config_template = config_template.replace("##authorization_log", "/".join([system.log_files_path, "authorization.log"]))
	config_template = config_template.replace("##mavis_module", system.mavis_exec)
	config_template = config_template.replace("##login_backend", "mavis")
	config_template = config_template.replace("##default_host", system.host_ip)
	config_template = config_template.replace("##authentication_key", system.auth_key)

	groups_compiled = "";
	for group in groups:
		group_template_current = "%s" % group_template;
		
		group_template_current = group_template_current.replace("##group_name", group["group"].name)
		
		if group["group"].is_enable_pass:
			enable_pass_str = "enable = clear " + group["group"].enable_pass
			group_template_current = group_template_current.replace("##enable_password", enable_pass_str)
		
		group_template_current = group_template_current.replace("##default_cmd", group["group"].cmd_default_policy)
		group_template_current = group_template_current.replace("##valid_until", group["group"].valid_until.strftime("%Y-%m-%d"))
		group_template_current = group_template_current.replace("##privilege_level", str(group["group"].default_privilege))
		
		commands_compiled = "";

		commands_groupped = {}
		for command in group["commands"]:
			if command.name not in commands_groupped.keys():
				commands_groupped[command.name] = []
			commands_groupped[command.name].append(command)



		for command_name in commands_groupped.keys():
			command_template_current = "%s" % command_template;
			command_template_current = command_template_current.replace("##command_name", command_name)	
			permit_regex = ""
			deny_regex = ""
			for command in commands_groupped[command_name]:
				permit_regex += "permit " + command.permit_regex + "\n"
			for command in commands_groupped[command_name]:
				if command.deny_regex != "":
					deny_regex += "deny " + command.deny_regex + "\n"
				else:
					deny_regex += "deny .\n"
			command_template_current = command_template_current.replace("##permit", permit_regex)
			command_template_current = command_template_current.replace("##deny", deny_regex)
			commands_compiled += command_template_current + "\n\n";
		group_template_current = group_template_current.replace("##cmds", commands_compiled)
		groups_compiled += group_template_current + "\n";

	users_compiled = "";
	for user in users:
		user_template_current = "%s" % user_template;
		
		user_template_current = user_template_current.replace("##username", user["user"].name)
		user_template_current = user_template_current.replace("##encrypted_password", str(user["user"].password))
		user_groups_compiled = "";
		for group in user["groups"]:
			user_groups_compiled += "member = " + group.name + "\n";
		user_template_current = user_template_current.replace("##groups", user_groups_compiled)
		users_compiled += user_template_current + "\n";

	print(groups_compiled)
	print(users_compiled)
	config_template = config_template.replace("##groups", groups_compiled)
	config_template = config_template.replace("##users", users_compiled)

	with open(output_file, "w+") as fd:
		fd.write(config_template);
		fd.flush();
		fd.close();
	return;

def verify_the_configuration(configuration_file):
	if subprocess.call(["/usr/local/sbin/tac_plus", "-P", configuration_file]) == 0:
		return True
	return False

def deploy_configuration(configuration_file):
	copy_status = (subprocess.call(["cp", "-v", configuration_file, "/usr/local/etc/tac_plus.cfg"]) == 0)
	restart_status = (subprocess.call(["/etc/init.d/tac_plus", "restart"]) == 0)
	return (copy_status and restart_status)
