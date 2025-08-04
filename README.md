# NFL Predicting Game

A Flask-based web application for predicting NFL game outcomes and competing in leagues with friends.

## Features

- User authentication and registration
- NFL game prediction system
- League creation and management
- Real-time scoring based on ESPN API data
- Responsive Bootstrap UI

## Security Improvements Made

### 🔒 Critical Security Fixes
- **CSRF Protection**: Added CSRF tokens to all forms
- **Input Validation**: Comprehensive validation for all user inputs
- **SQL Injection Prevention**: Enhanced parameterized queries with error handling
- **Session Security**: Secure session configuration with timeouts
- **Production Configuration**: Removed debug mode and proper host binding

### 🛡️ Additional Security Measures
- **Password Requirements**: Minimum 8 characters with complexity requirements
- **Username Validation**: Alphanumeric + underscore only, 3-50 characters
- **League Code Validation**: Alphanumeric only, 3-20 characters
- **Score Validation**: Numeric values between 0-999
- **Error Handling**: Comprehensive error handling and logging
- **Flash Messages**: User-friendly error and success messages

## Installation

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd NFL-Predicting-Game
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-super-secret-key-here
   MYSQL_HOST=localhost
   MYSQL_USER=your_mysql_user
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DB=nfl_predictions
   FLASK_ENV=development
   FLASK_DEBUG=False
   ```

4. **Set up the database**
   ```sql
   CREATE DATABASE nfl_predictions;
   USE nfl_predictions;
   ```
   Then run the SQL script:
   ```bash
   mysql -u your_user -p nfl_predictions < create_tables.sql
   ```

5. **Run the application**
   ```bash
   # Development
   python app.py
   
   # Or using the provided script
   runflask.cmd
   ```

## Configuration

### Development vs Production

The application supports different configurations:

- **Development**: Debug mode enabled, less strict security
- **Production**: Debug disabled, enhanced security settings

Set the environment variable `FLASK_ENV` to control the configuration:
- `development` - Development settings
- `production` - Production settings

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Yes | None |
| `MYSQL_HOST` | MySQL server host | No | localhost |
| `MYSQL_USER` | MySQL username | Yes | None |
| `MYSQL_PASSWORD` | MySQL password | Yes | None |
| `MYSQL_DB` | MySQL database name | No | nfl_predictions |
| `FLASK_ENV` | Environment (development/production) | No | development |
| `FLASK_DEBUG` | Enable debug mode | No | False |

## Security Best Practices

### For Production Deployment

1. **Use HTTPS**: Always use HTTPS in production
2. **Strong Secret Key**: Generate a strong, random secret key
3. **Database Security**: Use dedicated database user with minimal privileges
4. **Environment Variables**: Never commit `.env` files to version control
5. **Regular Updates**: Keep dependencies updated
6. **Logging**: Monitor application logs for security issues
7. **Backup**: Regular database backups

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

### Input Validation

All user inputs are validated:
- Usernames: 3-50 characters, alphanumeric + underscore
- League codes: 3-20 characters, alphanumeric only
- League names: 2-100 characters
- Scores: 0-999 integers

## API Dependencies

The application uses the ESPN API for NFL game data:
- Endpoint: `https://site.web.api.espn.com/apis/v2/scoreboard/header?sport=football&league=nfl`
- Rate limiting: Implemented with timeout handling
- Error handling: Graceful fallback for API failures

## Database Schema

The application uses the following tables:
- `brycegayan_users` - User accounts
- `brycegayan_leagues` - League information
- `brycegayan_users_leagues` - User-league relationships
- `brycegayan_predictions` - Submitted predictions
- `brycegayan_savedpredictions` - Draft predictions
- `brycegayan_info` - Application metadata

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the repository.
