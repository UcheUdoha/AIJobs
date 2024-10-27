import os
import psycopg2
from psycopg2.extras import RealDictCursor

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            port=os.environ['PGPORT']
        )

    def save_resume(self, user_id, resume_text, extracted_skills):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO resumes (user_id, resume_text, skills)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (user_id, resume_text, extracted_skills)
            )
            self.conn.commit()
            return cur.fetchone()[0]

    def get_jobs(self, search_query=None, location=None):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = "SELECT * FROM jobs WHERE 1=1"
            params = []
            
            if search_query:
                query += " AND (title ILIKE %s OR description ILIKE %s)"
                params.extend([f'%{search_query}%', f'%{search_query}%'])
            
            if location:
                query += " AND location ILIKE %s"
                params.append(f'%{location}%')
            
            cur.execute(query, params)
            return cur.fetchall()

    def save_bookmark(self, user_id, job_id):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bookmarks (user_id, job_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, job_id) DO NOTHING
                """,
                (user_id, job_id)
            )
            self.conn.commit()

    def get_bookmarks(self, user_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT j.* FROM jobs j
                JOIN bookmarks b ON j.id = b.job_id
                WHERE b.user_id = %s
                """,
                (user_id,)
            )
            return cur.fetchall()
