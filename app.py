from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models.ai_helper import AIHelper
from models.tutor import MathTutor
from models.ontology_helper import OntologyHelper

# Create Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize systems
math_tutor = MathTutor()
ontology_helper = OntologyHelper()

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    level = db.Column(db.Integer, default=1)
    score = db.Column(db.Integer, default=0)
    total_problems = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

# Problem History Model
class ProblemHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    problem = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.Float, nullable=False)
    student_answer = db.Column(db.Float, nullable=True)
    is_correct = db.Column(db.Boolean, default=False)
    time_taken = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        
        session['username'] = username
        session['user_id'] = user.id
        user.last_active = datetime.utcnow()
        db.session.commit()
        
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('logout'))

    # Get recent problem history
    recent_problems = ProblemHistory.query.filter_by(user_id=user.id)\
        .order_by(ProblemHistory.created_at.desc())\
        .limit(5).all()
    
    # Get performance analysis
    performance = math_tutor.get_performance_analysis()
    
    return render_template('dashboard.html', 
                         user=user,
                         recent_problems=recent_problems,
                         performance=performance)

@app.route('/practice')
def practice():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('logout'))
        
    # Generate initial problem for the current level
    problem = math_tutor.generate_problem(user.level)
    session['current_problem'] = {
        'equation': problem['equation'],
        'solution': problem['solution'],
        'start_time': datetime.utcnow().timestamp()
    }
    
    return render_template('practice.html', user=user)

@app.route('/generate_problem')
def generate_problem():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'})
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'})
        
    # Generate problem using math tutor
    problem = math_tutor.generate_problem(user.level)
    
    # Enrich problem with ontology data if available
    problem_details = ontology_helper.get_problem_details(f"Problem_{user.level}")
    if problem_details:
        problem.update(problem_details)
    
    session['current_problem'] = {
        'equation': problem['equation'],
        'solution': problem['solution'],
        'start_time': datetime.utcnow().timestamp()
    }
    
    return jsonify({
        'equation': problem['equation'],
        'level': user.level
    })

@app.route('/check_answer', methods=['POST'])
def check_answer():
    if 'username' not in session or 'current_problem' not in session:
        return jsonify({'status': 'error', 'message': 'Session expired'})
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'})

    data = request.json
    try:
        user_answer = float(data.get('answer'))
        current_problem = session['current_problem']
        time_taken = data.get('time_taken', 0)
        
        # Use relative tolerance for decimal answers
        solution = float(current_problem['solution'])
        tolerance = 0.01
        is_correct = abs(user_answer - solution) <= tolerance

        # Save problem history
        history = ProblemHistory(
            user_id=user.id,
            problem=current_problem['equation'],
            answer=solution,
            student_answer=user_answer,
            is_correct=is_correct,
            time_taken=time_taken
        )
        db.session.add(history)

        # Update user progress
        user.total_problems += 1
        level_up_message = None
        
        if is_correct:
            user.correct_answers += 1
            current_score = user.score + 10

            # Handle level up condition
            if current_score >= 50 and user.level < 3:
                level_up_message = f'Congratulations! You\'ve completed Level {user.level}! Moving to Level {user.level + 1}'
                new_level = user.level + 1
                user.level = new_level
                user.score = 0
                
                # Update level in ontology
                ontology_helper.update_user_level(user.username, new_level)
                
                # Generate first problem of new level immediately
                new_problem = math_tutor.generate_problem(user.level)
                session['current_problem'] = {
                    'equation': new_problem['equation'],
                    'solution': new_problem['solution'],
                    'start_time': datetime.utcnow().timestamp()
                }
            else:
                user.score = current_score

        db.session.commit()

        # Get AI model info from ontology for feedback
        ai_models = ontology_helper.get_ai_model_details()
        
        if not is_correct:
            steps = math_tutor.get_solution_steps(current_problem['equation'], user_answer)
            feedback = {
                'message': "Let's solve this step by step:",
                'steps': steps,
                'explanation': 'Check your calculation and try again.',
                'ai_models': ai_models
            }
        else:
            feedback = f"Correct! Well done! (Analyzed by {ai_models['bert']['version']})"

        response_data = {
            'status': 'correct' if is_correct else 'incorrect',
            'feedback': feedback,
            'score': user.score,
            'level': user.level,
            'levelUp': level_up_message
        }

        if level_up_message:
            response_data['newProblem'] = session['current_problem']['equation']

        return jsonify(response_data)

    except (ValueError, TypeError) as e:
        print(f"Error in check_answer: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Invalid answer format'
        })

@app.route('/get_stats')
def get_stats():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'})

    performance = math_tutor.get_performance_analysis()
    
    return jsonify({
        'status': 'success',
        'stats': {
            'level': user.level,
            'score': user.score,
            'total_problems': user.total_problems,
            'accuracy': performance['accuracy'],
            'suggestion': performance['suggestion']
        }
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        ontology_helper.ensure_ontology_directory()
        # Create database tables
        db.create_all()
    app.run(debug=True)