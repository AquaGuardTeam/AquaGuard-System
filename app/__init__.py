from flask import Flask
from flask_login import LoginManager
from flask_wtf import CSRFProtect
import click
from dotenv import load_dotenv

load_dotenv()

from app.config import Config
from app.extensions import db

csrf = CSRFProtect()

login_manager = LoginManager()
login_manager.login_view = 'web.login'


def create_app(config_object=Config):
    app = Flask(__name__, static_folder='../public/static')
    app.config.from_object(config_object)
    config_object.validate()

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    from app.models import User
    from app.api.routes import api
    from app.web.routes import web

    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(web)

    with app.app_context():
        db.create_all()
        from app.models import User, Device
        from werkzeug.security import generate_password_hash

        known_admin = User.query.filter_by(username='admin').first()
        if known_admin and known_admin.check_password('aquaguard'):
            db.session.delete(known_admin)
            db.session.commit()

        if not User.query.first():
            username = app.config.get('SUPER_ADMIN_USERNAME')
            password = app.config.get('SUPER_ADMIN_PASSWORD')
            if username and password and len(username) >= 3 and len(password) >= 12:
                super_admin = User(username=username, role='super_admin')
                super_admin.set_password(password)
                db.session.add(super_admin)
                db.session.commit()

        if app.config.get('DEVICE_API_TOKEN'):
            device = Device.query.first()
            if not device:
                device = Device(name='SBH-Fountain-01', location='Saint Benedict Hall',
                                api_token_hash=generate_password_hash(app.config['DEVICE_API_TOKEN']))
                db.session.add(device)
            else:
                device.api_token_hash = generate_password_hash(app.config['DEVICE_API_TOKEN'])
            db.session.commit()

    @app.cli.command('create-user')
    @click.option('--username', prompt=True)
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option('--role', type=click.Choice(['super_admin', 'admin', 'maintenance']), prompt=True)
    def create_user_command(username, password, role):
        """Provision a user through the trusted server terminal."""
        from app.models import User
        if User.query.filter_by(username=username).first():
            raise click.ClickException('That username already exists.')
        if len(username) < 3:
            raise click.ClickException('Username must contain at least 3 characters.')
        if len(password) < 12:
            raise click.ClickException('Password must contain at least 12 characters.')
        if role == 'super_admin' and User.query.filter_by(role='super_admin').first():
            raise click.ClickException('A super administrator already exists.')
        account = User(username=username, role=role)
        account.set_password(password)
        db.session.add(account)
        db.session.commit()
        click.echo(f'Created {role} account: {username}')

    @app.cli.command('list-users')
    def list_users_command():
        """List provisioned accounts without password information."""
        from app.models import User
        for account in User.query.order_by(User.username.asc()).all():
            click.echo(f'{account.id}\t{account.username}\t{account.role}')

    @app.after_request
    def prevent_html_caching(response):
        if response.mimetype == 'text/html':
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
        return response

    @app.context_processor
    def utility_processor():
        return {'app_name': 'AquaGuard'}

    return app
