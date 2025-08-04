# NFL Game Prediction Platform

A full-stack web application for predicting NFL game outcomes and competing in fantasy-style leagues with friends. Built with modern web technologies and security best practices.

## 🎯 Project Overview

This application demonstrates full-stack development skills with a focus on:
- **Backend Development**: Flask web framework with MySQL database
- **Frontend Development**: Responsive Bootstrap UI with Jinja2 templating
- **Security Implementation**: CSRF protection, input validation, secure authentication
- **API Integration**: Real-time NFL data from ESPN API
- **Database Design**: Relational database with proper normalization
- **DevOps**: Environment configuration and deployment readiness

## 🚀 Key Features

### Core Functionality
- **User Authentication System**: Secure registration/login with password hashing
- **NFL Game Predictions**: Submit weekly game score predictions
- **League Management**: Create and join private prediction leagues
- **Real-time Scoring**: Automatic scoring based on actual game results
- **Leaderboards**: Dynamic standings and rankings within leagues

### Technical Features
- **Responsive Design**: Mobile-first Bootstrap interface
- **Real-time Data**: ESPN API integration for live game data
- **Session Management**: Secure user sessions with timeouts
- **Error Handling**: Comprehensive error handling and user feedback
- **Input Validation**: Server-side validation for all user inputs

## 🛠️ Technology Stack

### Backend
- **Python 3.8+** - Core programming language
- **Flask 2.3.3** - Web framework
- **Flask-MySQLdb** - Database ORM
- **Flask-WTF** - Form handling and CSRF protection
- **Werkzeug** - Security utilities (password hashing)

### Frontend
- **Bootstrap 5** - Responsive CSS framework
- **Jinja2** - Template engine
- **JavaScript** - Client-side interactions
- **CSS3** - Custom styling

### Database
- **MySQL 5.7+** - Relational database
- **Custom Schema** - 6 normalized tables

### External APIs
- **ESPN API** - NFL game data and scores

### Development Tools
- **python-dotenv** - Environment variable management
- **requests** - HTTP client for API calls

## 🔒 Security Features

### Authentication & Authorization
- Password hashing with Werkzeug
- Session-based authentication
- Login required decorators
- Secure session configuration

### Input Validation & Sanitization
- Comprehensive server-side validation
- SQL injection prevention with parameterized queries
- XSS protection through proper escaping
- CSRF token protection on all forms

### Security Headers & Configuration
- Secure cookie settings
- HTTP-only session cookies
- SameSite cookie policy
- Production-ready security configurations

## 📊 Database Architecture

The application uses a well-normalized database schema:

```sql
brycegayan_users          -- User accounts and authentication
brycegayan_leagues        -- League information and settings
brycegayan_users_leagues  -- Many-to-many user-league relationships
brycegayan_predictions    -- Submitted game predictions
brycegayan_savedpredictions -- Draft predictions (save for later)
brycegayan_info          -- Application metadata and configuration
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/NFL-Predicting-Game.git
   cd NFL-Predicting-Game
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
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

5. **Database Setup**
   ```sql
   CREATE DATABASE nfl_predictions;
   USE nfl_predictions;
   ```
   ```bash
   mysql -u your_user -p nfl_predictions < create_tables.sql
   ```

6. **Run the application**
   ```bash
   python app.py
   ```
   
   Or use the provided script:
   ```bash
   runflask.cmd
   ```

## 🏗️ Project Structure

```
NFL-Predicting-Game/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── create_tables.sql     # Database schema
├── requirements.txt      # Python dependencies
├── runflask.cmd         # Windows startup script
├── static/              # Static assets
│   ├── style.css        # Custom CSS
│   └── *.json           # Sample data files
└── templates/           # Jinja2 templates
    ├── base.html.j2     # Base template
    ├── index.html.j2    # Homepage
    ├── login.html.j2    # Login page
    ├── signup.html.j2   # Registration page
    ├── predictions.html.j2 # Prediction interface
    └── league.html.j2   # League management
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key | Yes | None |
| `MYSQL_HOST` | MySQL server host | No | localhost |
| `MYSQL_USER` | MySQL username | Yes | None |
| `MYSQL_PASSWORD` | MySQL password | Yes | None |
| `MYSQL_DB` | Database name | No | nfl_predictions |
| `FLASK_ENV` | Environment mode | No | development |
| `FLASK_DEBUG` | Debug mode | No | False |

### Development vs Production

The application supports different configurations:
- **Development**: Debug mode, relaxed security for testing
- **Production**: Enhanced security, error logging, performance optimizations

## 🧪 Testing & Quality Assurance

### Code Quality
- Comprehensive error handling with try-catch blocks
- Input validation for all user inputs
- Proper logging for debugging and monitoring
- Clean, documented code with meaningful function names

### Security Testing
- CSRF protection on all forms
- SQL injection prevention
- XSS protection through proper escaping
- Secure session management

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

- **GitHub**: [@BryceG2088](https://github.com/BryceG2088)
- **LinkedIn**: [Bryce Gayan](www.linkedin.com/in/bryce-gayan-4532aa243)

## 🙏 Acknowledgments

- ESPN API for providing NFL game data
- Bootstrap team for the responsive UI framework
- Flask community for the excellent web framework
- NFL for the exciting game data that makes this project possible

---

**Note**: This project is designed as a portfolio piece to demonstrate full-stack development skills, security best practices, and modern web application architecture. It showcases proficiency in Python, Flask, MySQL, frontend development, and API integration.
