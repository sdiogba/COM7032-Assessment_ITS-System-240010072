from transformers import pipeline, AutoTokenizer, T5ForConditionalGeneration
import numpy as np
import torch
import random

class AIHelper:
    def __init__(self):
        try:
            # Initialize T5 model for question generation
            self.tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
            self.model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-base")
            
            # Initialize BERT for difficulty analysis
            self.understanding_model = pipeline(
                "text-classification",
                model="bert-base-uncased",
                return_all_scores=True
            )
            print("AI models initialized successfully")
        except Exception as e:
            print(f"AI Model initialization error: {e}")
            self.model = None
            self.understanding_model = None

    def generate_equation(self, level, previous_performance):
        """Generate equation based on level and student performance"""
        try:
            # Define templates for each level
            templates = {
                1: [
                    ("x + {a} = {b}", lambda: (random.randint(1, 10), random.randint(11, 20))),
                    ("{a}x = {b}", lambda: (random.randint(1, 5), random.randint(5, 15)))
                ],
                2: [
                    ("x - {a} = {b}", lambda: (random.randint(1, 20), random.randint(-10, 10))),
                    ("{a}x + {b} = {c}", lambda: (random.randint(2, 5), random.randint(1, 10), random.randint(20, 50)))
                ],
                3: [
                    ("{a}x - {b} = {c}", lambda: (random.randint(-10, -1), random.randint(-20, 20), random.randint(-50, 50))),
                    ("x/{a} + {b} = {c}", lambda: (random.randint(2, 5), random.randint(-10, 10), random.randint(-20, 20)))
                ]
            }

            # Select template based on level and performance
            level_templates = templates.get(level, templates[1])
            template, value_generator = random.choice(level_templates)
            
            # Generate values
            values = value_generator()
            
            # Create equation
            if len(values) == 2:
                a, b = values
                equation = template.format(a=a, b=b)
                if "+" in equation:
                    solution = b - a
                elif "-" in equation:
                    solution = b + a
                else:  # multiplication
                    solution = b / a
            else:
                a, b, c = values
                equation = template.format(a=a, b=b, c=c)
                if "/" in equation:
                    solution = (c - b) * a
                else:
                    solution = (c - b) / a

            return {
                'equation': equation,
                'solution': round(solution, 2),
                'difficulty': level
            }
            
        except Exception as e:
            print(f"Error in equation generation: {e}")
            return self._generate_fallback_equation(level)

    def _generate_fallback_equation(self, level):
        """Generate a fallback equation if main generation fails"""
        if level == 1:
            a = random.randint(1, 10)
            b = random.randint(1, 20)
            return {
                'equation': f"x + {a} = {b}",
                'solution': b - a,
                'difficulty': 1
            }
        elif level == 2:
            a = random.randint(2, 5)
            b = random.randint(-20, 20)
            c = random.randint(1, 10)
            return {
                'equation': f"{a}x + {b} = {c}",
                'solution': round((c - b) / a, 2),
                'difficulty': 2
            }
        else:
            a = random.randint(-10, -1)
            b = random.randint(-20, 20)
            c = random.randint(-50, 50)
            return {
                'equation': f"{a}x + {b} = {c}",
                'solution': round((c - b) / a, 2),
                'difficulty': 3
            }

    def analyze_understanding(self, answer, correct_answer, time_taken):
        """Generate personalized feedback based on student's answer"""
        try:
            error = abs(float(answer) - float(correct_answer))
            
            # Time-based feedback
            time_feedback = ""
            if time_taken > 120:
                time_feedback = " Try to work a bit faster while maintaining accuracy."
            elif time_taken < 10:
                time_feedback = " Good speed, but make sure to double-check your work."
                
            # Accuracy-based feedback
            if error < 0.01:
                if time_taken < 30:
                    return f"Excellent work! You solved it quickly and accurately.{time_feedback}"
                else:
                    return f"Good job! You got the right answer.{time_feedback}"
            elif error < 1:
                return f"Close! Double-check your calculations.{time_feedback}"
            elif error < 5:
                return f"You're on the right track, but review your steps carefully.{time_feedback}"
            else:
                return "Let's break this down step by step. Remember to check your work."
                
        except Exception as e:
            print(f"Error in understanding analysis: {e}")
            return "Keep practicing! Every problem helps you improve."

    def get_solution_steps(self, equation, incorrect_answer):
        """Generate solution steps for the equation"""
        try:
            # Parse equation
            parts = equation.replace(" ", "").split("=")
            if len(parts) != 2:
                return ["Invalid equation format"]

            left_side = parts[0]
            right_side = float(parts[1])

            # Parse left side
            if "+" in left_side:
                var_term, const_term = left_side.split("+")
                const = float(const_term)
                operation = "+"
            elif "-" in left_side and left_side[0] != "-":
                var_term, const_term = left_side.split("-")
                const = -float(const_term)
                operation = "-"
            else:
                var_term = left_side
                const = 0
                operation = ""

            # Get coefficient
            if var_term == "x":
                coeff = 1
            elif var_term == "-x":
                coeff = -1
            else:
                coeff = float(var_term.replace("x", ""))

            # Generate steps
            steps = [
                f"1. Original equation: {equation}",
                f"2. Move {abs(const)} to the right side:",
                f"   x = {right_side} {'-' if operation == '+' else '+'} {abs(const)}",
                f"3. Simplify:",
                f"   x = {right_side - const}"
            ]

            #  hint based on student's answer
            try:
                student_val = float(incorrect_answer)
                if abs(student_val + (right_side - const)) < 0.01:
                    steps.append("Hint: Check your signs - did you subtract instead of add?")
                elif abs(student_val - const) < 0.01:
                    steps.append("Hint: Remember to subtract the constant from both sides.")
                else:
                    steps.append("Hint: Double-check your arithmetic.")
            except:
                pass

            return steps

        except Exception as e:
            print(f"Error generating solution steps: {e}")
            return ["Let's solve this step by step.",
                    "1. Move all numbers to the right side",
                    "2. Combine like terms",
                    "3. Divide both sides by the coefficient of x"]