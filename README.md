# Online Voting Management System (OVM)

A secure Django-based online voting platform with AI-powered identity verification and blockchain vote storage.

## Features

### 🔐 Security & Authentication
- **AI-Based Face Verification**: Uses OpenCV for face detection and recognition
- **Liveness Detection**: Prevents spoofing with blink and movement detection
- **Duplicate Prevention**: Cross-database face matching to prevent multiple registrations
- **Blockchain Vote Storage**: Immutable vote records with SHA-256 hashing

### 🗳️ Voting System
- **Remote Voting**: Vote from anywhere for your registered constituency
- **One Person, One Vote**: Enforced through blockchain and database constraints
- **Anonymous Voting**: Candidate choices are hashed on blockchain
- **Vote Verification**: Voters receive blockchain receipt for verification

### 🎯 Key Components

#### 1. Voter Management
- Aadhaar-based registration
- Biometric face data storage
- Constituency mapping
- Verification status tracking

#### 2. Election Management
- Multiple election types (General, State, Local)
- Election status management (Upcoming, Live, Completed)
- Candidate registration per constituency
- Real-time vote counting

#### 3. AI Verification Module
- **Face Detector**: OpenCV Haar Cascades for face detection
- **Liveness Detector**: Anti-spoofing with blink and movement detection
- **Face Matcher**: Feature extraction and comparison
- **Verification Service**: Orchestrates the verification workflow

#### 4. Blockchain Integration
- Custom blockchain implementation with proof-of-work
- Vote recording with voter and candidate hashing
- Blockchain integrity verification
- Election results aggregation

## Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup Steps

1. **Clone the repository** (if applicable)
   ```bash
   cd c:\Users\Ankit\Videos\Project\ovm
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Populate sample data**
   ```bash
   python manage.py populate_data
   ```

6. **Create superuser** (for admin access)
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Usage

### For Voters

1. **Login**
   - Go to the homepage
   - Enter your Aadhaar number
   - Complete face verification (if enabled)
   - Click "Verify Identity"

2. **Vote**
   - View active elections on your dashboard
   - Click "Cast Vote" for an election
   - Select your candidate
   - Confirm your vote
   - Receive blockchain receipt

3. **Verify Vote**
   - Use the blockchain hash from your receipt
   - Verify on the blockchain explorer (admin panel)

### For Administrators

1. **Access Admin Panel**
   - Go to http://127.0.0.1:8000/admin/
   - Login with superuser credentials

2. **Manage Elections**
   - Create new elections
   - Set start and end dates
   - Change election status to "Live"

3. **Register Candidates**
   - Add candidates to elections
   - Assign to constituencies
   - Upload photos and party symbols

4. **Monitor Voting**
   - View real-time vote counts
   - Check verification logs
   - Validate blockchain integrity

## Sample Data

The system comes with pre-populated data:

### States
- Maharashtra (MH)
- Karnataka (KA)
- Tamil Nadu (TN)
- Gujarat (GJ)
- Delhi (DL)

### Sample Voters
- **Aadhaar**: 123456789012 (Mumbai North)
- **Aadhaar**: 123456789013 (Bangalore North)

### Active Election
- **2026 General Election** (Live)
- Multiple candidates per constituency

## Project Structure

```
ovm/
├── ovm/                    # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── voting/                 # Main voting app
│   ├── models.py          # Database models
│   ├── views.py           # Views and API endpoints
│   ├── urls.py            # URL patterns
│   └── admin.py           # Admin configuration
├── ai_verification/        # AI verification module
│   ├── face_detector.py   # Face detection
│   ├── liveness_detector.py  # Liveness detection
│   ├── face_matcher.py    # Face matching
│   └── verification_service.py  # Main service
├── blockchain/             # Blockchain module
│   └── blockchain_service.py  # Blockchain implementation
├── templates/              # HTML templates
│   ├── index.html         # Landing page
│   ├── dashboard.html     # Voter dashboard
│   ├── vote.html          # Voting interface
│   ├── admin.html         # Admin login
│   └── camera.html        # Face capture
├── static/                 # Static files (CSS, JS)
├── media/                  # User uploads
└── manage.py              # Django management
```

## API Endpoints

### Voter APIs
- `POST /api/verify-login/` - Login with Aadhaar
- `POST /api/cast-vote/` - Cast a vote

### Response Format
```json
{
    "success": true,
    "message": "Operation successful",
    "data": {}
}
```

## Database Models

### Core Models
1. **State** - Indian states
2. **Constituency** - Electoral constituencies
3. **Voter** - Voter information with biometric data
4. **Election** - Election events
5. **Candidate** - Candidates in elections
6. **Vote** - Vote records with blockchain hash
7. **VoterVerification** - Verification attempt logs

## Security Features

### Data Protection
- Face encodings stored as binary (encrypted)
- Passwords hashed with Django's PBKDF2
- Session-based authentication
- CSRF protection on all forms

### Blockchain Security
- SHA-256 hashing
- Proof-of-work mining
- Chain integrity validation
- Immutable vote records

### Anti-Fraud Measures
- Duplicate face detection
- One vote per election constraint
- IP address logging
- Verification attempt tracking

## Testing

### Manual Testing
1. Login with sample Aadhaar: `123456789012`
2. View active elections
3. Cast a vote
4. Verify blockchain receipt

### Admin Testing
1. Login to admin panel
2. View vote records
3. Check blockchain integrity
4. Monitor verification logs

## Troubleshooting

### Common Issues

1. **Face detection not working**
   - Ensure OpenCV is installed correctly
   - Check camera permissions
   - Verify image quality

2. **Blockchain errors**
   - Check blockchain service is initialized
   - Verify data integrity

3. **Migration errors**
   - Delete `db.sqlite3` and `migrations/` folders
   - Run `makemigrations` and `migrate` again

## Future Enhancements

### Planned Features
1. **Real Aadhaar Integration** - Connect to UIDAI API
2. **Production Blockchain** - Migrate to Ethereum/Polygon
3. **Advanced AI** - Deep learning models for better accuracy
4. **Mobile App** - React Native mobile application
5. **Multi-language Support** - Support for Indian languages
6. **SMS/Email Notifications** - Vote confirmations
7. **Results Dashboard** - Public results visualization

### Production Considerations
1. **Database** - Migrate to PostgreSQL
2. **Web Server** - Use Gunicorn + Nginx
3. **HTTPS** - SSL certificate for security
4. **Scalability** - Load balancing and caching
5. **Compliance** - Election Commission approval
6. **Audit** - Security audit and penetration testing

## Legal Disclaimer

⚠️ **Important**: This is a **prototype/demonstration system** for educational purposes.

Real election systems require:
- Government authorization
- Election Commission of India approval
- Legal framework compliance
- Certified security audits
- Data protection compliance
- Official Aadhaar API access

## Technology Stack

- **Backend**: Django 5.2.9
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI/ML**: OpenCV, NumPy
- **Blockchain**: Custom implementation (SHA-256, PoW)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Session-based

## Contributing

This is a demonstration project. For production use:
1. Conduct security audit
2. Implement proper authentication
3. Add comprehensive testing
4. Follow election laws and regulations

## License

Educational/Demonstration purposes only.

## Contact

For questions or issues, please refer to the project documentation.

---

**Built with ❤️ for secure and transparent elections**

