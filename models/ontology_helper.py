from owlready2 import *
import os

class OntologyHelper:
    def __init__(self):
        try:
            # Setting up the ontology path 
            onto_path.append("./ontology") 
            self.onto = get_ontology("math_tutor.owl").load()
            print("Ontology loaded successfully")
        except Exception as e:
            print(f"Error loading ontology: {e}")
            self.onto = None

    def get_problem_difficulty(self, problem_id):
        """Get difficulty level for a problem from ontology"""
        try:
            if not self.onto:
                return "Level1"
                
            problem = self.onto.search_one(iri=f"*{problem_id}")
            if problem:
                difficulty = problem.hasDifficulty[0]
                return str(difficulty.name)
        except Exception as e:
            print(f"Error getting difficulty: {e}")
        return "Level1"  # Default difficulty

    def get_problem_details(self, problem_id):
        """Get full problem details from ontology"""
        try:
            if not self.onto:
                return None
                
            problem = self.onto.search_one(iri=f"*{problem_id}")
            if problem:
                return {
                    'equation': problem.equation_string[0],
                    'solution': float(problem.solution_float[0]),
                    'difficulty': str(problem.hasDifficulty[0].name)
                }
        except Exception as e:
            print(f"Error getting problem details: {e}")
        return None

    def get_ai_model_details(self):
        """Get AI model information from ontology"""
        try:
            if not self.onto:
                return {
                    'bert': {
                        'version': 'bert-base-uncased',
                        'accuracy': 0.95
                    },
                    't5': {
                        'version': 'google/flan-t5-base'
                    }
                }
                
            bert_model = self.onto.search_one(type=self.onto.BERTModel)
            t5_model = self.onto.search_one(type=self.onto.T5Model)
            
            return {
                'bert': {
                    'version': bert_model.modelVersion_string[0],
                    'accuracy': float(bert_model.modelAccuracy_float[0])
                },
                't5': {
                    'version': t5_model.modelVersion_string[0]
                }
            }
        except Exception as e:
            print(f"Error getting AI model details: {e}")
            # Return default values if there's an error
            return {
                'bert': {
                    'version': 'bert-base-uncased',
                    'accuracy': 0.95
                },
                't5': {
                    'version': 'google/flan-t5-base'
                }
            }

    def update_user_level(self, username, new_level):
        """Update user level in ontology"""
        try:
            if not self.onto:
                return False
                
            user = self.onto.search_one(username_string=username)
            if user:
                user.level_integer = [new_level]
                self.onto.save()
                return True
        except Exception as e:
            print(f"Error updating user level: {e}")
        return False

    def ensure_ontology_directory(self):
        """Ensure the ontology directory exists"""
        ontology_dir = "./ontology"
        if not os.path.exists(ontology_dir):
            os.makedirs(ontology_dir)
            print(f"Created ontology directory at {ontology_dir}")