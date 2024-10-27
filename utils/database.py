import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            port=os.environ['PGPORT']
        )

    def update_user_email(self, user_id: int, email: str) -> bool:
        """Update user's email address"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET email = %s WHERE id = %s",
                    (email, user_id)
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"Error updating user email: {str(e)}")
            self.conn.rollback()
            return False

    def get_user_email(self, user_id: int) -> Optional[str]:
        """Get user's email address"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT email FROM users WHERE id = %s",
                    (user_id,)
                )
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error getting user email: {str(e)}")
            return None

    def get_email_preferences(self, user_id: int) -> Dict:
        """Get user's email preferences"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM email_preferences
                    WHERE user_id = %s
                    """,
                    (user_id,)
                )
                result = cur.fetchone()
                if not result:
                    # Create default preferences if not exists
                    cur.execute(
                        """
                        INSERT INTO email_preferences (user_id, is_enabled, min_match_score)
                        VALUES (%s, true, 70)
                        RETURNING *
                        """,
                        (user_id,)
                    )
                    result = cur.fetchone()
                    self.conn.commit()
                return dict(result)
        except Exception as e:
            print(f"Error getting email preferences: {str(e)}")
            return {"is_enabled": True, "min_match_score": 70}

    def update_email_preferences(self, user_id: int, is_enabled: bool, min_match_score: int) -> bool:
        """Update user's email preferences"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO email_preferences (user_id, is_enabled, min_match_score)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        is_enabled = EXCLUDED.is_enabled,
                        min_match_score = EXCLUDED.min_match_score
                    """,
                    (user_id, is_enabled, min_match_score)
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"Error updating email preferences: {str(e)}")
            self.conn.rollback()
            return False

    def save_resume(self, user_id: int, resume_text: str, extracted_skills: List[str], 
                   location: Optional[str] = None, file_path: Optional[str] = None, 
                   file_type: Optional[str] = None) -> int:
        """Save resume to database"""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO resumes (user_id, resume_text, skills, location, file_url, file_type)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (user_id, resume_text, extracted_skills, location, file_path, file_type)
            )
            self.conn.commit()
            return cur.fetchone()[0]

    def get_jobs(self, search_query: Optional[str] = None, location: Optional[str] = None,
                resume_location: Optional[str] = None) -> List[Dict]:
        """Get jobs with search and location filtering"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT j.*,
                CASE 
                    WHEN %s IS NOT NULL AND location ILIKE %s THEN 1.0
                    WHEN %s IS NOT NULL AND (
                        location ILIKE %s OR 
                        location ILIKE %s OR 
                        %s ILIKE ANY(STRING_TO_ARRAY(location, ', '))
                    ) THEN 0.5
                    ELSE 0.0
                END as location_score
                FROM jobs j
                WHERE 1=1
            """
            params = [
                resume_location, f'%{resume_location}%',
                resume_location, f'%{resume_location}%',
                f'%{resume_location}%', resume_location
            ]
            
            if search_query:
                query += " AND (title ILIKE %s OR description ILIKE %s)"
                params.extend([f'%{search_query}%', f'%{search_query}%'])
            
            if location:
                query += " AND location ILIKE %s"
                params.append(f'%{location}%')
            
            cur.execute(query, params)
            return cur.fetchall()

    def get_bookmarks(self, user_id: int) -> List[Dict]:
        """Get user's bookmarked jobs"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT j.*
                    FROM jobs j
                    JOIN bookmarks b ON j.id = b.job_id
                    WHERE b.user_id = %s
                    ORDER BY b.created_at DESC
                """, (user_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"Error getting bookmarks: {str(e)}")
            return []

    def save_bookmark(self, user_id: int, job_id: int) -> bool:
        """Save a job bookmark"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO bookmarks (user_id, job_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, job_id) DO NOTHING
                """, (user_id, job_id))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"Error saving bookmark: {str(e)}")
            self.conn.rollback()
            return False

    def get_unnotified_matches(self, user_id: int, min_score: float) -> List[Dict]:
        """Get unnotified job matches above minimum score"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT j.*, jm.match_score
                FROM jobs j
                JOIN job_matches jm ON j.id = jm.job_id
                WHERE jm.user_id = %s
                AND jm.match_score >= %s
                AND jm.is_notified = false
                ORDER BY jm.match_score DESC
                """,
                (user_id, min_score)
            )
            return cur.fetchall()

    def mark_matches_as_notified(self, user_id: int, job_ids: List[int]) -> None:
        """Mark job matches as notified"""
        if not job_ids:
            return
            
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE job_matches
                SET is_notified = true
                WHERE user_id = %s AND job_id = ANY(%s)
                """,
                (user_id, job_ids)
            )
            self.conn.commit()

    def save_job_match(self, user_id: int, job_id: int, match_score: float) -> None:
        """Save or update job match score"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO job_matches (user_id, job_id, match_score)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, job_id)
                    DO UPDATE SET match_score = EXCLUDED.match_score
                """, (user_id, job_id, match_score))
                self.conn.commit()
        except Exception as e:
            print(f"Error saving job match: {str(e)}")
            self.conn.rollback()
