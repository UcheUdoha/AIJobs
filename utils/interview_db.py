from typing import List, Dict, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

class InterviewDB:
    def __init__(self, db):
        self.db = db
        
    def get_questions(self, category: Optional[str] = None, 
                     difficulty: Optional[str] = None,
                     limit: Optional[int] = None) -> List[Dict]:
        """Get interview questions with optional filtering"""
        try:
            with self.db.get_cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM interview_questions WHERE 1=1"
                params = []
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                    
                if difficulty:
                    query += " AND difficulty = %s"
                    params.append(difficulty)
                    
                query += " ORDER BY RANDOM()"
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                    
                cur.execute(query, tuple(params) if params else None)
                return cur.fetchall()
        except Exception as e:
            print(f"Error getting interview questions: {str(e)}")
            return []

    def get_questions_by_skills(self, skills: List[str], limit: Optional[int] = None) -> List[Dict]:
        """Get questions that match the given skills"""
        try:
            with self.db.get_cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT * FROM interview_questions
                    WHERE skill_tags && %s
                    ORDER BY RANDOM()
                """
                if limit:
                    query += " LIMIT %s"
                    cur.execute(query, (skills, limit))
                else:
                    cur.execute(query, (skills,))
                return cur.fetchall()
        except Exception as e:
            print(f"Error getting questions by skills: {str(e)}")
            return []

    def get_questions_by_experience_level(self, experience_level: str, 
                                        limit: Optional[int] = None) -> List[Dict]:
        """Get questions for a specific experience level"""
        try:
            with self.db.get_cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT * FROM interview_questions
                    WHERE experience_level = %s
                    ORDER BY RANDOM()
                """
                if limit:
                    query += " LIMIT %s"
                    cur.execute(query, (experience_level, limit))
                else:
                    cur.execute(query, (experience_level,))
                return cur.fetchall()
        except Exception as e:
            print(f"Error getting questions by experience level: {str(e)}")
            return []
            
    def save_response(self, user_id: int, question_id: int, response: str, 
                     ai_feedback: str, score: int) -> Optional[int]:
        """Save user's interview response and feedback"""
        try:
            with self.db.get_cursor() as cur:
                cur.execute("""
                    INSERT INTO interview_responses 
                    (user_id, question_id, response, ai_feedback, score)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, question_id, response, ai_feedback, score))
                
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error saving interview response: {str(e)}")
            return None
            
    def get_user_progress(self, user_id: int) -> Dict[str, Any]:
        """Get user's interview practice progress and stats"""
        try:
            with self.db.get_cursor(cursor_factory=RealDictCursor) as cur:
                # Get overall stats
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_responses,
                        AVG(score) as avg_score,
                        MAX(score) as highest_score,
                        COUNT(DISTINCT question_id) as unique_questions,
                        MAX(created_at) as last_practice
                    FROM interview_responses
                    WHERE user_id = %s
                """, (user_id,))
                stats = cur.fetchone()
                
                # Get category breakdown
                cur.execute("""
                    SELECT 
                        q.category,
                        COUNT(*) as attempts,
                        AVG(r.score) as avg_score,
                        MAX(r.score) as highest_score
                    FROM interview_responses r
                    JOIN interview_questions q ON r.question_id = q.id
                    WHERE r.user_id = %s
                    GROUP BY q.category
                    ORDER BY avg_score DESC
                """, (user_id,))
                categories = cur.fetchall()
                
                # Get recent improvement trend
                cur.execute("""
                    SELECT 
                        DATE_TRUNC('day', created_at) as practice_date,
                        AVG(score) as avg_score
                    FROM interview_responses
                    WHERE user_id = %s
                    GROUP BY DATE_TRUNC('day', created_at)
                    ORDER BY practice_date DESC
                    LIMIT 10
                """, (user_id,))
                improvement_trend = cur.fetchall()
                
                return {
                    'stats': stats,
                    'categories': categories,
                    'improvement_trend': improvement_trend
                }
        except Exception as e:
            print(f"Error getting user progress: {str(e)}")
            return {
                'stats': None,
                'categories': [],
                'improvement_trend': []
            }

    def get_user_responses(self, user_id: int) -> List[Dict]:
        """Get user's previous responses with question details"""
        try:
            with self.db.get_cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        r.*,
                        q.question,
                        q.category,
                        q.difficulty,
                        q.skill_tags,
                        q.experience_level
                    FROM interview_responses r
                    JOIN interview_questions q ON r.question_id = q.id
                    WHERE r.user_id = %s
                    ORDER BY r.created_at DESC
                """, (user_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"Error getting user responses: {str(e)}")
            return []
