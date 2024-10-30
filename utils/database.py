import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import List, Dict, Optional
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    _instance = None
    _lock = threading.Lock()
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Database, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize connection pool and settings"""
        try:
            if self._pool is None:
                self._pool = SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=os.environ['PGHOST'],
                    database=os.environ['PGDATABASE'],
                    user=os.environ['PGUSER'],
                    password=os.environ['PGPASSWORD'],
                    port=os.environ['PGPORT']
                )
            self._local = threading.local()
            self._local.connection = None
            self.query_timeout = 30  # 30 seconds timeout
        except Exception as e:
            logger.error(f"Error initializing database pool: {str(e)}")
            raise

    def get_connection(self):
        """Get a connection from the pool with thread-local storage"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            if self._pool is None:
                self._initialize()
            self._local.connection = self._pool.getconn()
        return self._local.connection

    def return_connection(self, conn):
        """Return a connection to the pool with safety checks"""
        try:
            if hasattr(self._local, 'connection') and self._local.connection is conn:
                if self._pool is not None:
                    self._pool.putconn(conn)
                self._local.connection = None
        except Exception as e:
            logger.error(f"Error returning connection to pool: {str(e)}")

    @property
    def conn(self):
        """Provide backward compatibility for conn attribute"""
        return self.get_connection()

    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """Get a database cursor with automatic cleanup and error handling"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                connection.commit()
            except Exception as e:
                connection.rollback()
                raise
            finally:
                cursor.close()
        except Exception as e:
            logger.error(f"Error in database operation: {str(e)}")
            raise
        finally:
            if connection is not None:
                self.return_connection(connection)

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[List]:
        """Execute a query with error handling and timeout"""
        try:
            with self.get_cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SET statement_timeout = {self.query_timeout * 1000}")
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                return None
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return None

    def save_resume(self, user_id: int, resume_text: str, extracted_skills: List[str],
                   location: str, file_path: str, file_type: str) -> Optional[int]:
        """Save resume data to database"""
        try:
            with self.get_cursor() as cur:
                cur.execute("""
                    INSERT INTO resumes 
                    (user_id, resume_text, skills, location, file_path, file_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, resume_text, extracted_skills, location, file_path, file_type))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error saving resume: {str(e)}")
            return None

    def get_bookmarks(self, user_id: int) -> List[Dict]:
        """Get bookmarked jobs for user"""
        try:
            with self.get_cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT j.* FROM jobs j
                    JOIN bookmarks b ON j.id = b.job_id
                    WHERE b.user_id = %s
                    ORDER BY b.created_at DESC
                """, (user_id,))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting bookmarks: {str(e)}")
            return []

    def __del__(self):
        """Cleanup pool on object destruction"""
        try:
            if hasattr(self, '_pool') and self._pool is not None:
                self._pool.closeall()
        except Exception as e:
            logger.error(f"Error closing connection pool: {str(e)}")
