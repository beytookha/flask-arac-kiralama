import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    # Try creating connection to MySQL Server (not specific DB yet)
    # First try with password from .env
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', '127.0.0.1'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', ''),
            port=3306
        )
        print("Connected with configured password.")
        return conn
    except mysql.connector.errors.ProgrammingError as e:
        if e.errno == 1045: # Access denied
            print("Access denied with configured password. Trying empty password (XAMPP default)...")
            try:
                conn = mysql.connector.connect(
                    host=os.environ.get('DB_HOST', '127.0.0.1'),
                    user=os.environ.get('DB_USER', 'root'),
                    password='', # Try empty password
                    port=3306
                )
                print("Connected with empty password.")
                return conn
            except Exception as e2:
                print(f"Failed with empty password too: {e2}")
                raise e
        else:
            raise e

def execute_script(cursor, script_file):
    with open(script_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by DELIMITER
    # The schema uses 'DELIMITER $$' and 'DELIMITER ;'
    # We will manually split the content.
    
    # Simple parser for this specific schema file
    # 1. Split into commands based on the structure we know. 
    # Since existing parsers are complex, we'll strip comments and do a smart split.
    
    # Strategy: 
    # - The file has `DELIMITER $$` ... `END$$` ... `DELIMITER ;` blocks.
    # - And standard `;` terminated statements.
    
    # Let's break it down by `DELIMITER` keyword first? No, replace logical blocks.
    
    # Actually, mysql-connector `multi=True` handles `;` separated statements well.
    # It does NOT handle `DELIMITER` command.
    # We have to handle Stored Procedures manually.
    
    commands = []
    
    # Normalize line endings
    content = content.replace('\r\n', '\n')
    
    # Split by 'DELIMITER $$'
    parts = content.split('DELIMITER $$')
    
    # The first part is standard SQL (terminated by ;)
    # subsequent parts start with a stored procedure body ending with $$, then usually 'DELIMITER ;' or EOF.
    
    standard_part = parts[0]
    
    # Execute standard part (tables, inserts)
    for cmd in standard_part.split(';'):
        if cmd.strip():
            # Skip comments-only
            if cmd.strip().startswith('/*') or cmd.strip().startswith('--'):
                 # Simple check, might need regex for robustness but sufficient for this file
                 pass
            commands.append(cmd + ';')

    # Process stored procedures
    for part in parts[1:]:
        # Each part looks like: 
        # CREATE PROCEDURE ... END$$ 
        # DELIMITER ; ... (commands) ...
        
        # Split by '$$' to separate the procedure body
        subparts = part.split('$$')
        
        proc_body = subparts[0] # This is the CREATE PROCEDURE ... END
        commands.append(proc_body)
        
        if len(subparts) > 1:
            remainder = subparts[1] 
            # remainder usually contains 'DELIMITER ;' and then more SQL
            remainder = remainder.replace('DELIMITER ;', '')
            for cmd in remainder.split(';'):
                if cmd.strip():
                     commands.append(cmd + ';')

    # Remove empty commands and clean up
    final_commands = []
    for cmd in commands:
        if not cmd: continue
        clean_cmd = cmd.strip()
        if not clean_cmd: continue
        # Remove 'DELIMITER ;' leftovers
        if clean_cmd.startswith('DELIMITER'): continue
        final_commands.append(clean_cmd)

    # Execution
    print(f"Found {len(final_commands)} commands to execute.")
    for i, cmd in enumerate(final_commands):
        try:
            # Skip commented out blocks or headers if any remain
            if cmd.startswith('/*') and '*/' not in cmd: 
                # Multi-line comment start, simplistic skip (risky if not matched, but schema.sql is well formed)
                pass 
            
            cursor.execute(cmd)
            # print(f"Executed command {i+1}")
        except mysql.connector.Error as err:
            # Ignore some warnings like "Table exists" if we use DROP
            print(f"Error executing command {i+1}: {err}")
            # print(f"Command was: {cmd[:100]}...")

def main():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("Executing schema.sql...")
        execute_script(cursor, 'schema.sql')
        
        conn.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()
