import random
import numpy as np
from .ai_helper import AIHelper

class MathTutor:
    def __init__(self):
        self.ai_helper = AIHelper()
        self.student_history = {
            'recent_scores': [],
            'current_level': 1,
            'mistakes': [],
            'total_problems': 0,
            'last_explanation': None
        }

    def generate_problem(self, level):
        """Generate a math problem using AI"""
        try:
            # Calculate recent performance
            recent_performance = np.mean(self.student_history['recent_scores']) if self.student_history['recent_scores'] else 0.5
            
            # Generate problem using AI
            return self.ai_helper.generate_equation(level, recent_performance)
            
        except Exception as e:
            print(f"Problem generation error: {e}")
            return self._generate_safe_problem()

    def check_answer(self, student_answer, correct_answer, time_taken):
        """Check answer with improved feedback"""
        try:
            # Use relative tolerance for larger numbers
            if abs(correct_answer) > 100:
                tolerance = 0.01 * abs(correct_answer)
            else:
                tolerance = 0.01
                
            is_correct = abs(float(student_answer) - float(correct_answer)) <= tolerance
            self.update_history(is_correct, time_taken)
            
            if not is_correct:
                self.student_history['mistakes'].append({
                    'student_answer': float(student_answer),
                    'correct_answer': float(correct_answer),
                    'time_taken': time_taken
                })
            
            return is_correct
        except:
            return False

    def get_solution_steps(self, equation, incorrect_answer):
        """Get solution steps for incorrect answers"""
        return self.ai_helper.get_solution_steps(equation, incorrect_answer)

    def analyze_response(self, student_answer, correct_answer, time_taken):
        """Get personalized feedback"""
        return self.ai_helper.analyze_understanding(student_answer, correct_answer, time_taken)

    def update_history(self, is_correct, time_taken):
        """Update student's history"""
        try:
            self.student_history['total_problems'] += 1
            self.student_history['recent_scores'].append(1 if is_correct else 0)
            self.student_history['recent_scores'] = self.student_history['recent_scores'][-5:]  # Keep last 5 scores
            
            # Track time performance
            if 'time_history' not in self.student_history:
                self.student_history['time_history'] = []
            self.student_history['time_history'].append(time_taken)
            self.student_history['time_history'] = self.student_history['time_history'][-5:]
            
        except Exception as e:
            print(f"History update error: {e}")

    def get_performance_analysis(self):
        """Get detailed performance analysis"""
        try:
            recent_scores = self.student_history['recent_scores']
            accuracy = (sum(recent_scores) / len(recent_scores) * 100) if recent_scores else 0
            
            # Analyze time performance
            time_history = self.student_history.get('time_history', [])
            avg_time = sum(time_history) / len(time_history) if time_history else 0
            
            # Generate appropriate suggestion
            if accuracy >= 80:
                if avg_time < 30:
                    suggestion = "Excellent work! You're solving problems quickly and accurately."
                else:
                    suggestion = "Great accuracy! Try to improve your speed while maintaining accuracy."
            elif accuracy >= 60:
                if avg_time < 30:
                    suggestion = "Good speed! Focus on improving accuracy by double-checking your work."
                else:
                    suggestion = "You're making good progress. Keep practicing to improve both speed and accuracy."
            else:
                suggestion = "Take your time to understand each problem. Focus on the steps involved in solving them."
            
            return {
                'accuracy': round(accuracy, 2),
                'total_problems': self.student_history['total_problems'],
                'current_level': self.student_history.get('current_level', 1),
                'avg_time': round(avg_time, 1),
                'suggestion': suggestion
            }
        except Exception as e:
            print(f"Error in performance analysis: {e}")
            return {
                'accuracy': 0,
                'total_problems': 0,
                'current_level': 1,
                'avg_time': 0,
                'suggestion': "Keep practicing!"
            }

    def _generate_safe_problem(self):
        """Generate a safe fallback problem"""
        return {
            'equation': "x + 5 = 10",
            'solution': 5,
            'difficulty': 1
        }