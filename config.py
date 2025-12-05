# config.py - Configuration file for Animal Detection System

# Email Configuration
# For Gmail, you need to use an "App Password" instead of your regular password
# Steps to get Gmail App Password:
# 1. Go to your Google Account settings
# 2. Security → 2-Step Verification (enable it if not already)
# 3. Security → App passwords
# 4. Generate a new app password for "Mail"
# 5. Use that 16-character password below

EMAIL_CONFIG = {
    'enabled': True,  # Set to False to disable email alerts
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'your_gmail@gmail.com',  # Your Gmail address
    'sender_password': 'yourpassword',   # Your Gmail app password (16 characters)
    'recipient_email': 'receiver email@gmail.com'  # Email to receive alerts
}

# For other email providers:
# Yahoo Mail: smtp.mail.yahoo.com, port 587
# Outlook: smtp-mail.outlook.com, port 587
# Custom SMTP: Enter your SMTP server details

# Detection Configuration
DETECTION_CONFIG = {
    'confidence_threshold': 0.5,  # Minimum confidence for detection (0.0 to 1.0)
    'alert_cooldown': 60,  # Seconds between alerts for same animal
    'camera_index': 0,  # Camera device index (0 for default camera)
    'frame_width': 640,  # Processing frame width
    'frame_height': 480,  # Processing frame height
    'save_detection_images': True,  # Save images when animals detected
    'detections_folder': 'detections'  # Folder to save detection images
}

# Target animals to detect (YOLO class names)
TARGET_ANIMALS = [
    'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 
    'elephant', 'bear', 'zebra', 'giraffe'
]

# Sound Alert Configuration
SOUND_CONFIG = {
    'enabled': True,  # Set to False to disable sound alerts
    'beep_frequency': 1000,  # Hz
    'beep_duration': 500,  # milliseconds
    'beep_count': 3  # Number of beeps
}

# Database Configuration
DATABASE_CONFIG = {
    'user_id': 1  # Default user ID for detections
}
