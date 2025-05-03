from flask import Flask, request, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_mail import Mail, Message
from twilio.rest import Client
from passlib.hash import pbkdf2_sha256
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random, os

# Loading .env File
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Use SQLite for simplicity
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')  # Replace with secure key
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')  # Replace with your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')  # Replace with your email
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')  # Replace with your email
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # Replace with your email password
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')  # Replace with secure key

# Twilio configuration
account_sid = os.environ.get('account_sid')  # Replace with Twilio SID
auth_token = os.environ.get('auth_token')  # Replace with Twilio auth token
twilio_number = os.environ.get('twilio_number')  # Replace with Twilio phone number

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
mail = Mail(app)


# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    user_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_email_verified = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')


# OTP model (used only for login OTP)
class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp_type = db.Column(db.String(20), nullable=False)  # 'login'
    code = db.Column(db.String(6), nullable=False)
    expiry = db.Column(db.DateTime, nullable=False)


# Helper functions
def generate_otp():
    return str(random.randint(100000, 999999))[:6]


def send_email(to, subject, body):
    msg = Message(subject, recipients=[to], body=body)
    mail.send(msg)


def send_sms(to, body):
    client = Client(account_sid, auth_token)
    client.messages.create(to=f"+91{to}", from_=twilio_number, body=body)


# API Endpoints
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not all(key in data for key in ('first_name', 'last_name', 'email', 'phone_number', 'password')):
        return jsonify({'message': 'Missing fields'}), 400
    if User.query.filter_by(email=data['email']).first() or User.query.filter_by(
            phone_number=data['phone_number']).first():
        return jsonify({'message': 'Email or phone number already exists'}), 400
    password_hash = pbkdf2_sha256.hash(data['password'])
    user_name = f"{str(data['first_name']).lower()}_{str(data['last_name']).lower()}"
    user = User(first_name=data['first_name'], last_name=data['last_name'], email=data['email'],
                phone_number=data['phone_number'], password_hash=password_hash, user_name=user_name)
    db.session.add(user)
    db.session.commit()
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = serializer.dumps(user.email, salt='email-verification-salt')
    verification_url = url_for('verify_email', token=token, _external=True)
    send_email(user.email, 'Verify your email', f'Please click this link to verify your email: {verification_url}')
    return jsonify({
                       'message': f'You are successfully registered as: {user_name}. Please check your email to verify your account.'}), 201


@app.route('/verify-email', methods=['GET'])
def verify_email():
    token = request.args.get('token')
    if not token:
        return jsonify({'message': 'Missing token'}), 400
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-verification-salt', max_age=86400)  # 24 hours
    except:
        return jsonify({'message': 'Invalid or expired token'}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    if user.is_email_verified:
        return jsonify({'message': 'Email already verified'}), 200
    user.is_email_verified = True
    db.session.commit()
    return jsonify({'message': 'Email verified successfully'}), 200


@app.route('/send-login-otp', methods=['POST'])
def send_login_otp():
    data = request.get_json()
    if 'phone_number' not in data:
        return jsonify({'message': 'Missing phone_number'}), 400
    user = User.query.filter_by(phone_number=data['phone_number']).first()
    if not user or not user.is_email_verified:
        return jsonify({'message': 'User not found or email not verified'}), 404
    otp_code = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=10)
    OTP.query.filter_by(user_id=user.id, otp_type='login').delete()
    otp = OTP(user_id=user.id, otp_type='login', code=otp_code, expiry=expiry)
    db.session.add(otp)
    db.session.commit()
    send_sms(user.phone_number, f'Your login OTP is {otp_code}')
    return jsonify({'message': 'OTP sent to your phone'}), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not all(key in data for key in ('phone_number', 'otp')):
        return jsonify({'message': 'Missing fields'}), 400
    user = User.query.filter_by(phone_number=data['phone_number']).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    otp = OTP.query.filter_by(user_id=user.id, otp_type='login').first()
    if not otp or otp.code != data['otp'] or datetime.utcnow() > otp.expiry:
        return jsonify({'message': 'Invalid or expired OTP'}), 400
    access_token = create_access_token(identity=user.user_name)
    db.session.delete(otp)
    db.session.commit()
    return jsonify({'access_token': access_token}), 200


@app.route('/request-reset', methods=['POST'])
def request_reset():
    data = request.get_json()
    if 'email' not in data:
        return jsonify({'message': 'Missing email'}), 400
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    reset_token = serializer.dumps(user.email, salt='password-reset-salt')
    send_email(user.email, 'Password Reset', f'Your reset token is {reset_token}')
    return jsonify({'message': 'Reset token sent to your email'}), 200


@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    if not all(key in data for key in ('token', 'new_password')):
        return jsonify({'message': 'Missing fields'}), 400
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(data['token'], salt='password-reset-salt', max_age=3600)
    except:
        return jsonify({'message': 'Invalid or expired token'}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    user.password_hash = pbkdf2_sha256.hash(data['new_password'])
    db.session.commit()
    return jsonify({'message': 'Password reset successfully'}), 200


@app.route('/update-account', methods=['PUT'])
@jwt_required()
def update_account():
    current_user_name = get_jwt_identity()
    user = User.query.filter_by(user_name=current_user_name).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    data = request.get_json()
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'phone_number' in data:
        if User.query.filter_by(phone_number=data['phone_number']).first() and User.query.filter_by(
                phone_number=data['phone_number']).first().id != user.id:
            return jsonify({'message': 'Phone number already taken'}), 400
        user.phone_number = data['phone_number']
    if 'password' in data:
        user.password_hash = pbkdf2_sha256.hash(data['password'])
    db.session.commit()
    return jsonify({'message': 'Account updated successfully'}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run()
