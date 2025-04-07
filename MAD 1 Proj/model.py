from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime

db=SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(100),nullable=False,unique=True)
    password=db.Column(db.String(50),nullable=False)
    full_name=db.Column(db.String(50),nullable=False)
    dob=db.Column(db.Date,nullable=False)
    is_admin=db.Column(db.Boolean,default=False,nullable=False)    
    is_active=db.Column(db.Boolean,default=True,nullable=False)
    
    score=db.relationship('Scores',backref='user',lazy=True, cascade='all, delete-orphan')
    userresponse=db.relationship('UserResponse',backref='user',lazy=True,cascade='all, delete-orphan')
    
    
class Chapter(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50),nullable=False)
    description=db.Column(db.String(500),nullable=True)
    subject_id=db.Column(db.Integer,db.ForeignKey('subject.id'),nullable=False)

    quiz=db.relationship('Quiz',backref='chapter',lazy=True,cascade='all, delete-orphan')
   
class Quiz(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    chapter_id=db.Column(db.Integer,db.ForeignKey('chapter.id'),nullable=False)
    quiz_title=db.Column(db.String(100),nullable=False)
    date_of_quiz=db.Column(db.Date,nullable=False)
    time_duration=db.Column(db.Time,nullable=False)
    remarks=db.Column(db.String(200),nullable=True)

    scores=db.relationship('Scores',backref='quiz',lazy=True,cascade='all, delete-orphan')
    question=db.relationship('Questions',backref='quiz',lazy=True,cascade='all, delete-orphan')
    userresponse=db.relationship('UserResponse',backref='quiz',cascade='all, delete-orphan')
    
    
class Scores(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    quiz_id=db.Column(db.Integer,db.ForeignKey('quiz.id'),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    time_stamp=db.Column(db.DateTime,nullable=False)
    total_score=db.Column(db.Integer,nullable=False)
    
    userresponse=db.relationship('UserResponse',backref='scores',cascade='all, delete-orphan')
    
class UserResponse(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    quiz_id=db.Column(db.Integer,db.ForeignKey('quiz.id'),nullable=False)
    selected_option=db.Column(db.String,nullable=True)
    scores_id=db.Column(db.Integer,db.ForeignKey('scores.id'))
    
class Questions(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    quiz_id=db.Column(db.Integer,db.ForeignKey('quiz.id'),nullable=False)
    question_statement=db.Column(db.String(150),nullable=False)
    option_1 = db.Column(db.String(100), nullable=False)
    option_2 = db.Column(db.String(100), nullable=False)
    option_3 = db.Column(db.String(100), nullable=False)
    option_4 = db.Column(db.String(100), nullable=False)
    correct_option = db.Column(db.String, nullable=False)
  
class Subject(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(20),nullable=False)
    description=db.Column(db.String(500),nullable=True)
    
    chapter=db.relationship('Chapter',backref='subject',lazy=True,cascade='all, delete-orphan')
    

with app.app_context():
    db.create_all()
    def newadmin():
        admin=User.query.filter_by(is_admin=True).first()
        if not admin:
            user=User(username='happytth@gmail.com',password=generate_password_hash('admin'),full_name='Admin',dob=datetime.strptime('2004-09-21',"%Y-%m-%d").date(),is_admin=True,is_active=True)
            db.session.add(user)
            db.session.commit()
    newadmin()
        