from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap5 import Bootstrap
from flask_moment import Moment

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bootstrap = Bootstrap()
moment = Moment()
