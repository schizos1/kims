from .. import db

class PromptTemplate(db.Model):
    __tablename__ = 'prompt_template'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # 템플릿 이름 (예: "초등 수학 기본 v1")

    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)  # 특정 과목 전용
    subject = db.relationship('Subject')  # 과목 객체 직접 접근 가능

    content = db.Column(db.Text, nullable=False)  # 프롬프트 본문 (Jinja 스타일 변수 포함 가능)
    notes = db.Column(db.Text, nullable=True)  # 설명, 힌트
    is_default_for_subject = db.Column(db.Boolean, default=False)  # 해당 과목의 기본 템플릿인지 여부

    def __repr__(self):
        return f"<PromptTemplate {self.name}>"
