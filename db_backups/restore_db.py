import os
import subprocess
import argparse
from ng_news_scraper.config.settings import SCRAPER_SETTINGS

def restore_database(backup_file):
    """Restore database from gzipped backup file"""
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    # Parse database URL
    db_url = SCRAPER_SETTINGS['DATABASE_URL']
    db_info = {}
    if '://' in db_url:
        auth_url = db_url.split('://', 1)[1]
        user_pass, host_db = auth_url.split('@', 1)
        db_info['user'], db_info['password'] = user_pass.split(':')
        host_port, db_info['dbname'] = host_db.split('/')
        db_info['host'], db_info['port'] = host_port.split(':') if ':' in host_port else (host_port, '5432')
    
    env = os.environ.copy()
    env['PGPASSWORD'] = db_info['password']
    
    try:
        gunzip_cmd = ['gunzip', '--stdout', backup_file]
        psql_cmd = [
            'psql',
            '-h', db_info['host'],
            '-p', db_info['port'],
            '-U', db_info['user'],
            '-d', db_info['dbname'],
            '-v', 'ON_ERROR_STOP=1'
        ]
        
        print(f"🔄 Restoring from: {backup_file}")
        gunzip_process = subprocess.Popen(gunzip_cmd, stdout=subprocess.PIPE, env=env)
        psql_process = subprocess.Popen(psql_cmd, stdin=gunzip_process.stdout, env=env)
        
        gunzip_process.stdout.close()
        psql_process.communicate()
        
        if psql_process.returncode == 0:
            print("✅ Database restored successfully")
            return True
        else:
            print("❌ Restore failed")
            return False
            
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Restore database from backup')
    parser.add_argument('backup_file', help='Path to gzipped backup file')
    args = parser.parse_args()
    restore_database(args.backup_file)