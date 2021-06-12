from app import db

class Base(db.Model):

	__abstract__  = True

	id            = db.Column(db.Integer, primary_key=True)
	date_created  = db.Column(db.DateTime,  default=db.func.current_timestamp())
	date_modified = db.Column(db.DateTime,  default=db.func.current_timestamp(), 
		onupdate=db.func.current_timestamp())

class System(Base):

	__tablename__ = "tac_plus_system";

	id                 = db.Column(db.Integer,      primary_key=True)

	# Log files path
	log_files_path     = db.Column(db.String(128),  nullable=False, default="/var/log/tac_plus/")

	# Configuration file location
	cfg_file_path      = db.Column(db.String(128),  nullable=False, default="/usr/local/etc/tac_plus.cfg")

	# Listen port
	port_number        = db.Column(db.Integer,      nullable=False, default=49);

	# Mavis module password verificatin script
	mavis_exec         = db.Column(db.String(128),  nullable=False, default="/usr/local/lib/mavis/mavis_tacplus_passwd.pl")

	# Host IP
	host_ip            = db.Column(db.String(128),  nullable=False, default="0.0.0.0/0")

	# Authentication key
	auth_key           = db.Column(db.String(128),  nullable=False, default="my key")

	# Login backend
	login_backend      = db.Column(db.String(128),  nullable=False, default="mavis")


class Configuration(Base):

	__tablename__ = "tac_plus_cfg"

	id                 = db.Column(db.Integer,      primary_key=True)

	# Name
	name               = db.Column(db.String(128),  nullable=False)

	# Deployed/Not deployed
	deployed           = db.Column(db.Boolean,      nullable=False, default=False)

class ConfigurationGroups(Base):

	__tablename__ = "tac_plus_config_groups";

	id                 = db.Column(db.Integer,      primary_key=True)
	group_id           = db.Column(db.Integer, db.ForeignKey('tac_plus_groups.id'), nullable=False)
	configuration_id   = db.Column(db.Integer, db.ForeignKey('tac_plus_cfg.id'), nullable=False)

	configuration      = db.relationship("Configuration", backref="configuration_group")
	group              = db.relationship("Group", backref="configuration_group_1")

class ConfigurationUsers(Base):

	__tablename__ = "tac_plus_config_users";

	id                 = db.Column(db.Integer,      primary_key=True)
	user_id            = db.Column(db.Integer, db.ForeignKey('tac_plus_users.id'), nullable=False)
	configuration_id   = db.Column(db.Integer, db.ForeignKey('tac_plus_cfg.id'), nullable=False)

	configuration      = db.relationship("Configuration", backref="configuration_user")
	user               = db.relationship("TacacsUser", backref="configuration_user_1")


class Group(Base):

	__tablename__ = "tac_plus_groups"

	id                 = db.Column(db.Integer,      primary_key=True)
	name               = db.Column(db.String(128),  nullable=False)
	valid_until        = db.Column(db.DateTime,     nullable=False)
	cmd_default_policy = db.Column(db.String(128),  nullable=False)
	default_privilege  = db.Column(db.Integer,      nullable=False)

class GroupCommands(Base):
	__tablename__ = "tac_plus_group_commands"

	id                 = db.Column(db.Integer,      primary_key=True)
	group_id           = db.Column(db.Integer, db.ForeignKey('tac_plus_groups.id'), nullable=False)
	command_id         = db.Column(db.Integer, db.ForeignKey('tac_plus_commands.id'), nullable=False)
	group              = db.relationship("Group", backref="group")
	command            = db.relationship("Command", backref="command")

class Command(Base):

	__tablename__ = "tac_plus_commands"

	id                 = db.Column(db.Integer,      primary_key=True)
	name               = db.Column(db.String(128),  nullable=False)
	permit_regex       = db.Column(db.String(512),  nullable=False)
	deny_regex         = db.Column(db.String(512),  nullable=False)
	permit_message     = db.Column(db.String(512),  nullable=False)
	deny_message       = db.Column(db.String(512),  nullable=False)

class TacacsUser(Base):

	__tablename__ = "tac_plus_users"

	id                 = db.Column(db.Integer,      primary_key=True)
	name               = db.Column(db.String(128),  nullable=False)
	password           = db.Column(db.String(128),  nullable=False)


class TacacsUserGroups(Base):

	__tablename__ = "tac_plus_user_groups"

	id                 = db.Column(db.Integer,      primary_key=True)
	group_id           = db.Column(db.Integer, db.ForeignKey('tac_plus_groups.id'), nullable=False)
	user_id            = db.Column(db.Integer, db.ForeignKey('tac_plus_users.id'), nullable=False)
	group              = db.relationship("Group", backref="user_group")
	user               = db.relationship("TacacsUser", backref="user")

