from .. import db

class Mascot(db.Model):
    __tablename__ = 'mascot'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    image_filename = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
