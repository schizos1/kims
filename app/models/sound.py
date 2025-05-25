from .. import db

class SoundEffect(db.Model):
    __tablename__ = 'sound_effect'
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(50), unique=True, nullable=False)  # ex: 'quiz_correct', 'trophy_earned'
    filename = db.Column(db.String(100), nullable=False)  # 실제 오디오 파일 이름
    description = db.Column(db.String(200), nullable=True)  # 관리용 설명
