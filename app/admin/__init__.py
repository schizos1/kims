from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

from . import routes  # 반드시 routes import 있어야 함!
