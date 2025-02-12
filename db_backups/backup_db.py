#backup_db.py
import os
import subprocess
from datetime import datetime
from ng_news_scraper.config.settings import SCRAPER_SETTINGS

def backup_database():
    """Create a compressed backup of the PostgreSQL database"""
    # Use existing backup directory
    backup_dir = '/Users/jeremiah/Projects/ng_news_scraper/db_backups'
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f"backup_{timestamp}.sql.gz")
    
    # Parse database URL
    db_url = SCRAPER_SETTINGS['DATABASE_URL']
    db_info = {}
    if '://' in db_url:
        auth_url = db_url.split('://', 1)[1]
        user_pass, host_db = auth_url.split('@', 1)
        db_info['user'], db_info['password'] = user_pass.split(':')
        host_port, db_info['dbname'] = host_db.split('/')
        db_info['host'], db_info['port'] = host_port.split(':') if ':' in host_port else (host_port, '5432')
    
    # Set environment variables
    env = os.environ.copy()
    env['PGPASSWORD'] = db_info['password']
    
    # Construct commands
    pg_dump_cmd = [
        'pg_dump',
        '-h', db_info['host'],
        '-p', db_info['port'],
        '-U', db_info['user'],
        '-F', 'p',  # Plain text format
        '-b',  # Include large objects
        db_info['dbname']
    ]
    
    try:
        # Execute backup with pipeline
        with open(backup_file, 'wb') as f:
            dump_process = subprocess.Popen(
                pg_dump_cmd, 
                stdout=subprocess.PIPE,
                env=env
            )
            gzip_process = subprocess.Popen(
                ['gzip'], 
                stdin=dump_process.stdout,
                stdout=f
            )
            
            dump_process.stdout.close()
            gzip_process.communicate()
            
            if gzip_process.returncode == 0:
                print(f"✅ Backup created: {backup_file}")
                # Keep only last 5 backups
                cleanup_old_backups(backup_dir, keep=5)
                return backup_file
            else:
                print("❌ Backup failed during compression")
                return None
                
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        if os.path.exists(backup_file):
            os.remove(backup_file)
        return None

def cleanup_old_backups(backup_dir, keep=5):
    """Keep only the n most recent backups"""
    backups = []
    for f in os.listdir(backup_dir):
        if f.startswith('backup_') and f.endswith('.sql.gz'):
            full_path = os.path.join(backup_dir, f)
            backups.append((os.path.getmtime(full_path), full_path))
    
    # Sort by modification time (newest first)
    backups.sort(reverse=True)
    
    # Remove old backups
    for _, file_path in backups[keep:]:
        try:
            os.remove(file_path)
            print(f"🗑️  Removed old backup: {os.path.basename(file_path)}")
        except OSError as e:
            print(f"⚠️  Could not remove {file_path}: {e}")

if __name__ == "__main__":
    backup_database()