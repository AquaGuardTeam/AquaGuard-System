import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.extensions import db
from app.models import User


allowed_roles = ('super_admin', 'admin', 'maintenance')

parser = argparse.ArgumentParser(description='Provision AquaGuard users from the trusted server terminal.')
subparsers = parser.add_subparsers(dest='action', required=True)

add_parser = subparsers.add_parser('add', help='Create an authorized staff account')
add_parser.add_argument('--username', required=True)
add_parser.add_argument('--role', choices=allowed_roles, required=True)

subparsers.add_parser('list', help='List account names and roles')
args = parser.parse_args()

app = create_app()
with app.app_context():
    if args.action == 'list':
        for account in User.query.order_by(User.username.asc()).all():
            print(f'{account.id}\t{account.username}\t{account.role}')
    else:
        username = args.username.strip()
        role = args.role
        if len(username) < 3:
            raise SystemExit('Username must contain at least 3 characters.')
        if User.query.filter_by(username=username).first():
            raise SystemExit('That username already exists.')
        if role == 'super_admin' and User.query.filter_by(role='super_admin').first():
            raise SystemExit('A super administrator already exists.')

        password = getpass.getpass('Temporary password: ')
        confirmation = getpass.getpass('Confirm password: ')
        if len(password) < 12:
            raise SystemExit('Password must contain at least 12 characters.')
        if password != confirmation:
            raise SystemExit('Password confirmation does not match.')

        account = User(username=username, role=role)
        account.set_password(password)
        db.session.add(account)
        db.session.commit()
        print(f'Created {role} account: {username}')
