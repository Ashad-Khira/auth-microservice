# Authentication Microservice

This is a RESTful authentication microservice built with Flask, designed to handle user registration, email verification, OTP-based login, password reset, and account updates. It follows RESTful API principles and is intended to be scalable and secure for integration into larger systems.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Security Considerations](#security-considerations)
- [Scalability](#scalability)
- [Contributing](#contributing)
- [Postman Collection](#postman-collection)

## Features
- **User Registration**: Register users with first name, last name, email, phone number, and password, with email verification via a secure link.
- **Email Verification**: Sends a verification link to the user's email, which verifies their account upon clicking.
- **OTP-Based Login**: Authenticates users using a phone number and SMS OTP, issuing a JWT token.
- **Password Reset**: Allows users to reset their password via a secure email token.
- **Account Updates**: Enables authenticated users to update their profile details (protected by JWT).
- **Role-Based Authorization**: Supports roles (e.g., user, admin) for potential access control (optional implementation).
- **Secure Design**: Uses password hashing, signed tokens, and time-limited OTPs for security.

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ashad-khira/auth-microservice.git
   cd auth-microservice
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install flask flask-sqlalchemy flask-jwt-extended flask-mail twilio passlib itsdangerous
   ```

4. **Create the Database**:
   - The application uses SQLite by default (`users.db`). The database is created automatically when you run the application.

## Configuration
Configure the application by setting environment variables or updating the configuration in `auth_microservice.py`. Key settings include:

- **Flask Configuration**:
  - `JWT_SECRET_KEY`: Secret key for JWT tokens (e.g., `'your-jwt-secret-key'`).
  - `SECRET_KEY`: Secret key for token serialization (e.g., `'your-secret-key'`).
  - `SQLALCHEMY_DATABASE_URI`: Database URI (default: `'sqlite:///users.db'`).

- **Email Service** (e.g., Mailtrap for testing):
  - `MAIL_SERVER`: SMTP server (e.g., `'smtp.mailtrap.io'`).
  - `MAIL_PORT`: SMTP port (e.g., `587`).
  - `MAIL_USE_TLS`: Enable TLS (e.g., `True`).
  - `MAIL_USERNAME`: Email username.
  - `MAIL_PASSWORD`: Email password.

- **Twilio SMS Service**:
  - `account_sid`: Twilio account SID.
  - `auth_token`: Twilio auth token.
  - `twilio_number`: Twilio phone number.

Example `.env` file:
```bash
JWT_SECRET_KEY=your-jwt-secret-key
SECRET_KEY=your-secret-key
MAIL_SERVER=smtp.mailtrap.io
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-mailtrap-username
MAIL_PASSWORD=your-mailtrap-password
account_sid=your-twilio-account-sid
auth_token=your-twilio-auth-token
twilio_number=your-twilio-phone-number
```

Load environment variables using `python-dotenv`:
```bash
pip install python-dotenv
```
Then, import and load in `auth_microservice.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Usage
1. **Run the Application**:
   ```bash
   python auth_microservice.py
   ```
   The server starts on `http://localhost:5000` in debug mode.

2. **Interact with the API**:
   Use tools like [Postman](https://www.postman.com) or `curl` to send requests to the API endpoints.

3. **Example Workflow**:
   - Register a user (`POST /register`).
   - Verify email via the link sent to the user's email (`GET /verify-email?token=<token>`).
   - Request a login OTP (`POST /send-login-otp`).
   - Log in with the OTP (`POST /login`) to get a JWT token.
   - Update account details (`PUT /update-account`) using the JWT token.

## API Endpoints
| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/register` | POST | Register a new user and send a verification link | None |
| `/verify-email` | GET | Verify the user's email via a token | None |
| `/send-login-otp` | POST | Send an OTP to the user's phone | None |
| `/login` | POST | Authenticate with phone number and OTP, return JWT | None |
| `/request-reset` | POST | Request a password reset token via email | None |
| `/reset-password` | POST | Reset password using a token | None |
| `/update-account` | PUT | Update user account details | JWT Bearer Token |

### Example Requests
- **Register**:
  ```bash
  curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone_number": "+1234567890",
    "password": "secure123"
  }'
  ```

- **Verify Email**:
  ```bash
  curl http://localhost:5000/verify-email?token=<token-from-email>
  ```

- **Send Login OTP**:
  ```bash
  curl -X POST http://localhost:5000/send-login-otp -H "Content-Type: application/json" -d '{
    "phone_number": "+1234567890"
  }'
  ```

- **Login**:
  ```bash
  curl -X POST http://localhost:5000/login -H "Content-Type: application/json" -d '{
    "phone_number": "+1234567890",
    "otp": "123456"
  }'
  ```

- **Update Account**:
  ```bash
  curl -X PUT http://localhost:5000/update-account -H "Authorization: Bearer <jwt-token>" -H "Content-Type: application/json" -d '{
    "first_name": "Jane",
    "phone_number": "+0987654321"
  }'
  ```

## Testing
- **Unit Tests**: Write tests using [pytest](https://pytest.org) to cover API endpoints, database operations, and authentication flows.
- **Manual Testing**: Use [Postman](https://www.postman.com) or `curl` to test endpoints.
- **Email Testing**: Use [Mailtrap](https://mailtrap.io) to capture verification and reset emails.
- **SMS Testing**: Use [Twilio's sandbox](https://www.twilio.com/docs/sms) for SMS OTP testing.
- **Database Inspection**: Use [DB Browser for SQLite](https://sqlitebrowser.org) to verify user and OTP data.

Example test command:
```bash
pytest tests/
```

## Security Considerations
- **Password Hashing**: Uses PBKDF2-SHA256 for secure password storage.
- **Token Security**: JWT tokens and email verification tokens are signed and time-limited.
- **OTP Security**: SMS OTPs are valid for 10 minutes and deleted after use.
- **Input Validation**: All endpoints validate inputs to prevent injection attacks.
- **CSRF Protection**: Enabled for JWT tokens (includes `csrf` claim).
- **Recommendations**:
  - Use HTTPS in production to encrypt data in transit.
  - Rotate `JWT_SECRET_KEY` and `SECRET_KEY` periodically.
  - Implement rate limiting with [Flask-Limiter](https://flask-limiter.readthedocs.io) to prevent abuse.

## Scalability
- **Database**: SQLite is used for development. For production, use [PostgreSQL](https://www.postgresql.org) for better concurrency.
- **Caching**: Store OTPs in [Redis](https://redis.io) for faster access and automatic expiration.
- **Deployment**: Use [Gunicorn](https://gunicorn.org) with [Nginx](https://www.nginx.com) as a reverse proxy for load balancing.
- **Horizontal Scaling**: Deploy multiple instances behind a load balancer.
- **Database Migrations**: Use [Flask-Migrate](https://flask-migrate.readthedocs.io) for schema changes.

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## Postman Collection
Here is the Postman Collection to test this projects API Endpoints. See the [Postman Collection](postman-collection) file for details.