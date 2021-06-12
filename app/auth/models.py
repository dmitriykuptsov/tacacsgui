# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db

# Define a base model for other database tables to inherit
class Base(db.Model):

    __abstract__  = True

    id            = db.Column(db.Integer, primary_key=True)
    date_created  = db.Column(db.DateTime,  default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                                           onupdate=db.func.current_timestamp())

# Define a User model
class User(Base):

    __tablename__ = 'auth_user'

    # User Name
    username = db.Column(db.String(128),  nullable=False)

    # Identification Data: password
    password = db.Column(db.String(192),  nullable=False)

    # Salt
    salt = db.Column(db.String(128),      nullable=False)

    # New instance instantiation procedure
    def __init__(self, username, password):

        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % (self.name)
