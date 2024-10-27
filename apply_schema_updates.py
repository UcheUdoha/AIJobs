from utils.database import Database

def apply_schema_updates():
    db = Database()
    with open('schema_updates_email.sql', 'r') as f:
        sql_commands = f.read()
    
    with db.conn.cursor() as cur:
        cur.execute(sql_commands)
    db.conn.commit()

if __name__ == "__main__":
    apply_schema_updates()
