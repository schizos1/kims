from .. import db

class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    concepts = db.relationship('Concept', backref='subject', lazy=True, cascade="all, delete-orphan")

class Concept(db.Model):
    __tablename__ = 'concept'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    steps = db.relationship('Step', backref='concept', lazy=True, order_by="Step.step_order", cascade="all, delete-orphan")
    questions = db.relationship('Question', backref='concept', lazy=True, cascade="all, delete-orphan")

class Step(db.Model):
    __tablename__ = 'step'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    step_order = db.Column(db.Integer, nullable=False)
    concept_id = db.Column(db.Integer, db.ForeignKey('concept.id'), nullable=False)

class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(100), nullable=True)
    question_type = db.Column(db.String(50), nullable=False, default='multiple_choice')

    option1 = db.Column(db.String(500), nullable=True)
    option2 = db.Column(db.String(500), nullable=True)
    option3 = db.Column(db.String(500), nullable=True)
    option4 = db.Column(db.String(500), nullable=True)

    option1_img = db.Column(db.String(100), nullable=True)
    option2_img = db.Column(db.String(100), nullable=True)
    option3_img = db.Column(db.String(100), nullable=True)
    option4_img = db.Column(db.String(100), nullable=True)

    answer = db.Column(db.String(200), nullable=True)
    source_type = db.Column(db.String(50), nullable=False, default='manual_admin')
    concept_id = db.Column(db.Integer, db.ForeignKey('concept.id'), nullable=False)

    answers = db.relationship('StudyHistory', backref='question', lazy='dynamic', cascade="all, delete-orphan")

class StudyHistory(db.Model):
    __tablename__ = 'study_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    submitted_answer = db.Column(db.String(200), nullable=True)
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.now())
    mistake_status = db.Column(db.String(50), default='active', nullable=False)
