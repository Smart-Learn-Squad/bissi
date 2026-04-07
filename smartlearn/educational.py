"""Educational tools module for Smartlearn.

Study aids and learning utilities for students.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


@dataclass
class StudyPlan:
    """Generated study plan."""
    subject: str
    topics: List[str]
    schedule: List[Dict]  # Daily study schedule
    estimated_hours: float
    difficulty: str


@dataclass
class QuizQuestion:
    """Quiz question with answer."""
    question: str
    options: List[str]
    correct_answer: int
    explanation: str
    topic: str


class StudyPlanner:
    """Create personalized study plans."""
    
    def __init__(self):
        self.subjects_db = {
            "mathematics": {
                "algebra": ["linear equations", "quadratic equations", "polynomials", "factoring"],
                "calculus": ["limits", "derivatives", "integrals", "applications"],
                "statistics": ["probability", "distributions", "hypothesis testing", "regression"],
            },
            "physics": {
                "mechanics": ["kinematics", "dynamics", "energy", "momentum"],
                "electromagnetism": ["electric fields", "magnetic fields", "circuits", "waves"],
                "thermodynamics": ["laws", "heat transfer", "entropy", "cycles"],
            },
            "chemistry": {
                "general": ["atomic structure", "periodic table", "bonding", "stoichiometry"],
                "organic": ["hydrocarbons", "functional groups", "reactions", "synthesis"],
            },
            "biology": {
                "cellular": ["cell structure", "metabolism", "division", "signaling"],
                "genetics": ["DNA", "RNA", "proteins", "inheritance", "biotechnology"],
                "ecology": ["ecosystems", "populations", "communities", "biodiversity"],
            },
            "computer_science": {
                "programming": ["variables", "control flow", "functions", "data structures"],
                "algorithms": ["sorting", "searching", "complexity", "optimization"],
                "databases": ["SQL", "normalization", "indexing", "transactions"],
            }
        }
    
    def create_plan(self, subject: str, topics: List[str], 
                    days_available: int, hours_per_day: float = 2,
                    difficulty: str = "medium") -> StudyPlan:
        """Generate study plan for subject/topics."""
        
        # Distribute topics across days
        daily_schedule = []
        total_hours = 0
        
        for day in range(days_available):
            day_topics = []
            day_hours = 0
            
            # Assign topics to this day
            for i, topic in enumerate(topics):
                if i % days_available == day:
                    hours = hours_per_day / max(1, len(topics) // days_available)
                    day_topics.append({
                        "topic": topic,
                        "hours": round(hours, 1),
                        "activities": ["read", "practice", "review"]
                    })
                    day_hours += hours
            
            if day_topics:
                daily_schedule.append({
                    "day": day + 1,
                    "date": (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
                    "topics": day_topics,
                    "total_hours": round(day_hours, 1)
                })
                total_hours += day_hours
        
        return StudyPlan(
            subject=subject,
            topics=topics,
            schedule=daily_schedule,
            estimated_hours=round(total_hours, 1),
            difficulty=difficulty
        )
    
    def suggest_topics(self, subject: str, level: str = "intermediate") -> List[str]:
        """Suggest topics based on subject and level."""
        if subject not in self.subjects_db:
            return []
        
        all_topics = []
        for category, topics in self.subjects_db[subject].items():
            all_topics.extend(topics)
        
        # Filter by level (placeholder logic)
        if level == "beginner":
            return all_topics[:len(all_topics)//3]
        elif level == "intermediate":
            return all_topics[:2*len(all_topics)//3]
        else:
            return all_topics


class QuizGenerator:
    """Generate practice quizzes."""
    
    def __init__(self):
        self.question_templates = {
            "conceptual": [
                ("What is the definition of {concept}?", 
                 ["{correct}", "{wrong1}", "{wrong2}", "{wrong3}"]),
                ("Which of the following best describes {concept}?",
                 ["{correct}", "{wrong1}", "{wrong2}", "{wrong3}"]),
            ],
            "application": [
                ("Given {scenario}, what is the {outcome}?",
                 ["{correct}", "{wrong1}", "{wrong2}", "{wrong3}"]),
            ],
            "comparison": [
                ("What is the main difference between {concept_a} and {concept_b}?",
                 ["{correct}", "{wrong1}", "{wrong2}", "{wrong3}"]),
            ]
        }
    
    def generate_quiz(self, topic: str, n_questions: int = 5,
                      question_types: List[str] = None) -> List[QuizQuestion]:
        """Generate quiz for a topic."""
        questions = []
        
        # Placeholder questions - in real implementation, 
        # this would use LLM or question database
        for i in range(n_questions):
            q = QuizQuestion(
                question=f"Sample question {i+1} about {topic}?",
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answer=0,
                explanation=f"This is the explanation for question {i+1}.",
                topic=topic
            )
            questions.append(q)
        
        return questions


class FlashcardMaker:
    """Create study flashcards."""
    
    def __init__(self):
        self.cards: List[Dict] = []
    
    def add_card(self, front: str, back: str, category: str = "",
                 tags: List[str] = None):
        """Add flashcard."""
        self.cards.append({
            "id": len(self.cards) + 1,
            "front": front,
            "back": back,
            "category": category,
            "tags": tags or [],
            "created": datetime.now().isoformat(),
            "review_count": 0,
            "last_reviewed": None
        })
    
    def get_cards(self, category: str = None, tags: List[str] = None) -> List[Dict]:
        """Get filtered flashcards."""
        filtered = self.cards
        
        if category:
            filtered = [c for c in filtered if c["category"] == category]
        
        if tags:
            filtered = [c for c in filtered if any(t in c["tags"] for t in tags)]
        
        return filtered
    
    def export_to_file(self, filepath: str):
        """Export flashcards to JSON."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.cards, f, indent=2)


class ExamTimer:
    """Exam countdown and timer."""
    
    def __init__(self, exam_date: datetime = None, duration_hours: float = 3):
        self.exam_date = exam_date
        self.duration_hours = duration_hours
    
    def days_remaining(self) -> Optional[int]:
        """Days until exam."""
        if not self.exam_date:
            return None
        return (self.exam_date - datetime.now()).days
    
    def time_per_question(self, n_questions: int) -> float:
        """Recommended time per question in minutes."""
        total_minutes = self.duration_hours * 60
        return total_minutes / n_questions if n_questions > 0 else 0


# Convenience functions
def create_study_schedule(subject: str, exam_date: str, 
                          topics: List[str]) -> StudyPlan:
    """Quick study plan creation."""
    planner = StudyPlanner()
    
    exam = datetime.strptime(exam_date, "%Y-%m-%d")
    days = (exam - datetime.now()).days
    
    return planner.create_plan(subject, topics, max(1, days))
