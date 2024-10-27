import logging
from utils.database import Database
from psycopg2 import Error as PostgresError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def split_sql_commands(sql_file):
    """Split SQL file content into individual commands"""
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    # Split on semicolons while ignoring those within comments
    commands = []
    current_command = []
    in_comment = False
    
    for line in sql_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('--'):
            continue
            
        if line.startswith('/*'):
            in_comment = True
            continue
            
        if line.endswith('*/'):
            in_comment = False
            continue
            
        if not in_comment:
            current_command.append(line)
            if line.endswith(';'):
                commands.append('\n'.join(current_command))
                current_command = []
    
    return commands

def apply_schema_updates():
    """Apply database schema updates with error handling"""
    db = Database()
    sql_files = [
        'schema_updates_email.sql',
        'schema_updates_scraping.sql',
        'sample_job_sources.sql'
    ]
    
    try:
        for sql_file in sql_files:
            logger.info(f"Processing schema updates from {sql_file}")
            commands = split_sql_commands(sql_file)
            
            for command in commands:
                if not command.strip():
                    continue
                    
                try:
                    with db.conn.cursor() as cur:
                        cur.execute(command)
                        db.conn.commit()
                        logger.info(f"Successfully executed command: {command[:50]}...")
                except PostgresError as e:
                    if 'already exists' in str(e):
                        logger.info(f"Table already exists, skipping: {str(e)}")
                        continue
                    logger.error(f"Error executing command: {str(e)}")
                    db.conn.rollback()
                    
        logger.info("Schema updates completed successfully")
        
    except Exception as e:
        logger.error(f"Error during schema updates: {str(e)}")
        raise
    finally:
        db.conn.commit()

if __name__ == "__main__":
    apply_schema_updates()
