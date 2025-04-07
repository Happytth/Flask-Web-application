from flask import Flask,render_template,request,flash,url_for,redirect,session
from app import app
from model import User,db,Chapter,Quiz,Scores,Questions,Subject,UserResponse
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime
from functools import wraps

def auth_req(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])
        if not user or not user.is_active :  
            flash('Your account has been blocked by the admin', category='danger')
            session.clear()
            return redirect(url_for('login'))

        return func(*args, **kwargs)
    return decorated


def admin_req(func):
    @wraps(func)
    def decorated(*args,**kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash('You are not an admin')
            return redirect(url_for('login'))    

        return func(*args,**kwargs)
    return decorated


@app.route('/',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        user=User.query.filter_by(username=username).first()
        
        if not user:
            flash('Username does not exists')
            return render_template('login.html')
        
        if user.is_active==False:
            flash('You have been blocked by admin','danger')
            return render_template('login.html')
            
        if not check_password_hash(user.password,password):
            flash('Incorrect Password')
            return redirect(url_for('login'))
        
        session['user_id']=user.id
        session['username']=user.username
        session['full_name']=user.full_name
        flash('Logged in successfully','success')
        return redirect(url_for('profile'))
    
    else:
        return render_template('login.html')
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        confirm_password=request.form.get('confirm_password')
        full_name=request.form.get('full_name')
        dob = datetime.strptime(request.form.get('dob'), "%Y-%m-%d").date()

        user=User.query.filter_by(username=username).first()
        full_name=full_name.upper()
        if user:
            flash('Username already exists')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
    
        user=User(username=username,password=generate_password_hash(password),full_name=full_name,dob=dob)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    
    else:
        return render_template('register.html')


@app.route('/profile')
@auth_req
def profile():
    user=User.query.get(session['user_id'])
    return render_template('profile.html',user=user)

@app.route('/profile',methods=['POST'])
@auth_req
def profile_post():
    user=User.query.get(session['user_id'])
    username=request.form.get('username')
    cpassword=request.form.get('c_password')
    npassword=request.form.get('n_password')
    cnpassword=request.form.get('cn_password')
    
    if not username or not cpassword or not npassword or not cnpassword:
        flash('Please fill all fields')
        return redirect(url_for('profile'))
    
    if not check_password_hash(user.password,cpassword):
        flash('Incorrect Password')
        return redirect(url_for('profile'))
    
    if check_password_hash(cpassword,npassword):
        flash('New password cannot be the same as current password')
        return redirect(url_for('profile'))
    
    if username!=user.username:
        user1=User.query.filter_by(username=username).first()
        if user1:
            flash('Username already exists')
            return redirect(url_for('profile'))
        
    user.password=generate_password_hash(npassword)
    user.username=username
    
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))
    

@app.route('/logout')
@auth_req
def logout():
    session.pop('user_id',None)
    session.pop('username',None)
    session.pop('full_name',None)
    flash('Logged out successfully')
    return redirect(url_for('login'))

@app.route('/admin_dashboard',methods=['GET','POST'])
@admin_req
def admin_dashboard():
    user = User.query.get(session['user_id'])
    
    active_users_count = User.query.filter_by(is_active=True).count()
    subjects_count = Subject.query.count()
    quizzes_count = Quiz.query.count()

    return render_template('admin_dashboard.html',user=user,active_users_count=active_users_count-1,subjects_count=subjects_count,quizzes_count=quizzes_count)


@app.route('/subject', methods=['GET', 'POST'])
@admin_req
def subject():
    if request.method == 'GET':
        subjects = Subject.query.all()
        user = User.query.get(session['user_id'])
        return render_template('subject.html', subjects=subjects, user=user)

    else:
        subject_name = request.form.get('subject_name')
        description = request.form.get('subject_description')

        subject = Subject(name=subject_name, description=description)
        db.session.add(subject)
        db.session.commit()

        flash('Subject added successfully', 'success')
        return redirect(url_for('subject'))
    
@app.route('/subject_edit/<int:id>', methods=['GET', 'POST'])
@admin_req
def subject_edit(id):
    subject = Subject.query.get_or_404(id)

    if request.method == 'POST':
        if request.form.get('name'):
            subject.name = request.form.get('name')
        if request.form.get('subject_description'):
            subject.description = request.form.get('subject_description')
        db.session.commit()
        flash('Subject updated successfully', 'success')
        return redirect(url_for('subject'))

    return render_template('subject_edit.html', subject=subject)

@app.route('/subject/delete/<int:id>')
@admin_req
def sub_delete(id):
    sub=Subject.query.get_or_404(id)
    db.session.delete(sub)
    db.session.commit()
    flash('Subject deleted successfully',category='danger')
    return redirect(url_for('subject'))
    
@app.route('/chapter/<int:subject_id>', methods=['GET', 'POST'])
@admin_req
def chapter(subject_id):
    user = User.query.get(session['user_id'])
    subject = Subject.query.get(subject_id) 
    if not subject:
        flash('Subject not found', category='danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('chapter_description')

        if name:
            new_chapter = Chapter(name=name,subject_id=subject.id,description=description)
            db.session.add(new_chapter)
            db.session.commit()
            flash('Chapter added successfully', category='success')
            return redirect(url_for('chapter', subject_id=subject.id))
        

    return render_template('chapter.html', user=user, subject=subject)

@app.route('/chapter/delete/<int:id>')
@admin_req
def chap_del(id):
    chap=Chapter.query.get_or_404(id)
    subject_id=chap.subject_id
    db.session.delete(chap)
    db.session.commit()
    flash('Chapter deleted successfully','danger')
    return redirect(url_for('chapter',subject_id=subject_id))


@app.route('/chapter_edit/<int:chapter_id>', methods=['GET', 'POST'])
@admin_req
def chapter_edit(chapter_id):
    user = User.query.get(session['user_id'])
    chapter = Chapter.query.get(chapter_id)
    if request.method == 'POST':
        if request.form.get('name'):
            chapter.name = request.form.get('name')
        if request.form.get('chapter_description'):
            chapter.description = request.form.get('chapter_description')
            
        db.session.commit()
        flash('Chapter updated successfully', category='success')
        return redirect(url_for('chapter', subject_id=chapter.subject_id,chapter=chapter))
    return render_template('chapter_edit.html', user=user, chapter=chapter)

@app.route('/admin_user')
@admin_req
def admin_user():
    users=User.query.filter_by(is_admin=False).all()
    user = User.query.get(session['user_id'])
    return render_template('admin_user.html',users=users,user=user)   


@app.route('/admin_user/block/<int:id>')
@admin_req
def admin_user_block(id):
    user=User.query.get_or_404(id)
    user.is_active=False
    db.session.commit()
    flash('User blocked successfully')
    return redirect(url_for('admin_user'))

@app.route('/admin_user/unblock/<int:id>')
@admin_req
def admin_user_unblock(id):
    user=User.query.get_or_404(id)
    user.is_active=True
    db.session.commit()
    flash('User unblocked successfully', 'success')
    return redirect(url_for('admin_user'))


@app.route('/quiz',methods=['GET','POST'])
@admin_req
def quiz():
    user=User.query.get(session['user_id'])
    subjects=Subject.query.all()
    selected_subject=None
    selected_chapter=None
    chapters=[]
    if request.method=='POST':
        selected_subject=request.form.get('subject_choosen')
        if selected_subject:
            selected_chapter = request.form.get('chapter_choosen')
            chapters=Chapter.query.filter_by(subject_id=selected_subject).all()
            
            if selected_chapter:
                time_duration_str = request.form.get('time_duration')
                remarks = request.form.get('remarks')
                date_of_quiz_str = request.form.get('date_of_quiz')
                date_of_quiz = datetime.strptime(date_of_quiz_str, "%Y-%m-%d").date()
                time_duration = datetime.strptime(time_duration_str, "%H:%M").time()

                new=Quiz(chapter_id=int(selected_chapter),quiz_title=request.form.get('quiz_title'),date_of_quiz=date_of_quiz,time_duration=time_duration,remarks=remarks)
                db.session.add(new)
                db.session.commit()
                flash('Quiz Added Successfully',category='success')
                
                return redirect(url_for('quiz'))
    Quizzes=Quiz.query.all()        
    return render_template('quiz.html',user=user,subjects=subjects,selected_subject=selected_subject,chapters=chapters,Quizzes=Quizzes)

@app.route('/quiz/edit/<int:id>',methods=['GET','POST'])
@admin_req
def quiz_edit(id):
    quiz=Quiz.query.get_or_404(id)
    user=User.query.get(session['user_id'])    
    subjects=Subject.query.all()
    Quizzes=Quiz.query.all()
     
    if request.method=='POST':  
        quiz=Quiz.query.get(id)
        if request.form.get('quiz_title'):
            quiz.quiz_title=request.form.get('quiz_title')
        time_duration_str = request.form.get('time_duration')
        date_of_quiz_str = request.form.get('date_of_quiz')
        if date_of_quiz_str:
            date_of_quiz = datetime.strptime(date_of_quiz_str, "%Y-%m-%d").date()
            quiz.date_of_quiz=date_of_quiz
        if time_duration_str:
            time_duration = datetime.strptime(time_duration_str, "%H:%M").time()
            quiz.time_duration=time_duration
        if request.form.get('remarks'):   
            quiz.remarks=request.form.get('remarks')
        
        db.session.commit()
        flash('Quiz edited Sucessfully',category='success')
        return redirect(url_for('quiz'))
    return render_template('quiz_edit.html',quiz=quiz,user=user,Quizzes=Quizzes,subjects=subjects)

@app.route('/quiz/delete/<int:id>',methods=['POST','GET'])
@admin_req
def quiz_delete(id):
    user=Quiz.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('Quiz deleted successfully',category='danger')
    return redirect(url_for('quiz'))

@app.route('/question/<int:quiz_id>',methods=['GET','POST'])
@admin_req
def question(quiz_id):
    user=User.query.get(session['user_id'])
    quiz=Quiz.query.get(quiz_id)
    
    if request.method=='POST':
        question_statement=request.form.get('question_statement')
        option_1=request.form.get('option_1')
        option_2=request.form.get('option_2')
        option_3=request.form.get('option_3')
        option_4=request.form.get('option_4')
        correct_option=request.form.get('correct_option')
        
        if question_statement:
            new=Questions(quiz_id=quiz.id,question_statement=question_statement,option_1=option_1,option_2=option_2,option_3=option_3,option_4=option_4,correct_option=correct_option)
            db.session.add(new)
            db.session.commit()
            flash('Question added successfully',category='success')
            return redirect(url_for('question',quiz_id=quiz.id))
        
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()

    return render_template('question.html',user=user,quiz=quiz,questions=questions)
            
@app.route('/question/edit/<int:id>', methods=['GET', 'POST'])
@admin_req
def question_edit(id):
    question = Questions.query.get(id)
    user = User.query.get(session['user_id'])
    quiz = Quiz.query.get(question.quiz_id)  
    if request.method == 'POST':
        list1 = ['question_statement', 'option_1', 'option_2', 'option_3', 'option_4', 'correct_option']
        for i in list1:
            if request.form.get(i):
                setattr(question, i, request.form.get(i)) 
        db.session.commit()
        flash('Question edited successfully', category='success')
        return redirect(url_for('question', quiz_id=question.quiz_id))
    return render_template('question_edit.html', user=user, quiz=quiz, quiz_id=question.quiz_id,question=question)

        
@app.route('/question/delete/<int:id>')
@admin_req
def question_delete(id):
    question=Questions.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully',category='danger')
    return redirect(url_for('question',quiz_id=question.quiz_id))

@app.route('/user_quiz/<int:id>', methods=['GET', 'POST'])
@auth_req
def start_quiz(id):
    user = User.query.get(session['user_id'])
    quiz = Quiz.query.get(id)
    current_date = datetime.now().strftime("%d-%m-%Y")
    
    if request.method == 'POST':
        total_score = 0
        ques=0
        for question in quiz.question:
            ques+=1
            selected_option = request.form.get(f"question_{question.id}")
            is_correct = selected_option == question.correct_option if selected_option else False
            
            user_response = UserResponse(
                user_id=user.id,
                quiz_id=quiz.id,
                selected_option=selected_option
            )
            db.session.add(user_response)

            if is_correct:
                total_score += 1
        total_score=(total_score/ques)*100
        new_score = Scores(
            quiz_id=quiz.id,
            user_id=user.id,
            time_stamp=datetime.now(),
            total_score=total_score
        )
        db.session.add(new_score)
        db.session.commit()

        return redirect(url_for('user_dashboard', user=user))
    else:
        current_date = datetime.now().date()
        if current_date > quiz.date_of_quiz:
            flash('Quiz has expired', 'danger')
            return redirect(url_for('user_dashboard', user=user))
        return render_template('start_quiz.html', user=user, quiz=quiz)
    
@app.route('/user_dashboard', methods=['GET', 'POST'])
@auth_req
def user_dashboard():
    quizzes=Quiz.query.all()
    question_counts = {quiz.id: Questions.query.filter_by(quiz_id=quiz.id).count() for quiz in quizzes}

    user=User.query.get(session['user_id'])
    return render_template('user_dashboard.html',quizzes=quizzes,user=user,question_counts=question_counts)    
    
@app.route('/view_quiz/<int:id>')
@auth_req
def view_quiz(id):
    quiz=Quiz.query.get(id)
    quizzes=Quiz.query.all()
    question_counts = {quiz.id: Questions.query.filter_by(quiz_id=quiz.id).count() for quiz in quizzes}

    return render_template("quiz_view.html",quiz=quiz,question_counts=question_counts)

@app.route('/scores/<int:id>')
@auth_req
def score_view(id):
    scores = Scores.query.filter_by(user_id=id).all()
    user=User.query.get(session['user_id'])
    return render_template('scores.html',scores=scores,user=user)


from sqlalchemy import func
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

@app.route('/admin_summary')
@admin_req
def summary():
    user = User.query.get(session['user_id'])
    quiz_attendance = db.session.query(
        Quiz.id, Quiz.quiz_title, func.count(Scores.user_id).label('user_count')
    ).select_from(Quiz).join(Scores, Scores.quiz_id == Quiz.id).group_by(Quiz.id, Quiz.quiz_title).all()

    quizzes = [quiz.quiz_title for quiz in quiz_attendance]
    user_counts = [quiz.user_count for quiz in quiz_attendance]

    subject_quiz_count = db.session.query(
        Subject.name, func.count(Quiz.id).label('quiz_count')
    ).select_from(Subject).join(Chapter, Chapter.subject_id == Subject.id).join(Quiz, Quiz.chapter_id == Chapter.id).group_by(Subject.name).all()

    subjects = [subject.name for subject in subject_quiz_count]
    quiz_counts = [subject.quiz_count for subject in subject_quiz_count]

    scores=Scores.query.all()
    subject=Subject.query.all()
    if quizzes and user_counts:
        plt.figure(figsize=(8, 6))
        plt.bar(range(len(quizzes)), user_counts)
        plt.xticks(range(len(quizzes)), quizzes, rotation=45)
        plt.xlabel('Quiz Title')
        plt.ylabel('User Count')
        plt.title('Quiz Attendance')
        plt.tight_layout()
        plt.savefig('static/quiz_attendance.png')
        plt.close()

   
    plt.figure()
    plt.pie(quiz_counts, labels=subjects, autopct='%1.1f%%', startangle=140)
    plt.title('Subject Quiz Distribution')
    plt.tight_layout()
    plt.savefig('static/subject_quiz_distribution.png')
    plt.close()

    return render_template('admin_summary.html', quizzes=quizzes, scores=scores,subject=subject,user_counts=user_counts, subjects=subjects, quiz_counts=quiz_counts, user=user, zip=zip)

@app.route('/user_summary')
@auth_req
def usersummary():
    user = User.query.get(session['user_id'])
    
    user_scores = db.session.query(
        Quiz.quiz_title, Scores.total_score
    ).join(Scores, Scores.quiz_id == Quiz.id).filter(Scores.user_id == user.id).all()

    user_quizzes = [score.quiz_title for score in user_scores]
    user_scores_values = [score.total_score for score in user_scores]

    if user_quizzes and user_scores_values:
        plt.figure(figsize=(8, 6))
        plt.bar(range(len(user_quizzes)), user_scores_values, color='skyblue')
        plt.xticks(range(len(user_quizzes)), user_quizzes, rotation=45)
        plt.xlabel('Quiz Title')
        plt.ylabel('User Score')
        plt.title('User Quiz Performance')
        plt.tight_layout()
        plt.savefig('static/user_quiz_performance.png')
        plt.close()

    return render_template('user_summary.html', user_quizzes=user_quizzes, user_scores_values=user_scores_values, user=user)

@app.route('/search', methods=['GET'])
@auth_req
def search():
    user=User.query.get(session['user_id'])
    query = request.args.get('query', '').strip()
    
    if not query:
        flash("Please enter a search term.", "warning")
        #return redirect(url_for('profile'))
    
    subjects = Subject.query.filter(Subject.name.ilike(f"%{query}%")).all()
    quizzes = Quiz.query.filter(Quiz.quiz_title.ilike(f"%{query}%")).all()
    users = User.query.filter(
        db.or_(
            User.username.ilike(f"%{query}%"),
            User.full_name.ilike(f"%{query}%")
        )
    ).all()
    
    return render_template(
        'search_results.html', 
        subjects=subjects, 
        quizzes=quizzes, 
        users=users, 
        query=query,
        user=user
    )
