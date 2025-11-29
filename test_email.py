#!/usr/bin/env python3
"""
Email Configuration Test Script
Tests if your email settings are working correctly
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_email_config():
    """Test email configuration with detailed error handling."""
    
    print("=" * 60)
    print("📧 EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    # Try to import config
    try:
        from config import EMAIL_CONFIG
        print("✅ config.py found and imported")
    except ImportError:
        print("❌ config.py not found!")
        print("\n💡 Please create config.py with your email settings:")
        print("""
EMAIL_CONFIG = {
    'enabled': True,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'your_email@gmail.com',
    'sender_password': 'your_app_password',
    'recipient_email': 'recipient@gmail.com'
}
        """)
        return False
    
    # Check if email is enabled
    if not EMAIL_CONFIG.get('enabled', False):
        print("⚠️  Email alerts are disabled in config.py")
        print("   Set 'enabled': True to enable email alerts")
        return False
    
    # Validate configuration
    print("\n📋 Checking configuration...")
    required_fields = ['smtp_server', 'smtp_port', 'sender_email', 
                      'sender_password', 'recipient_email']
    
    missing_fields = []
    for field in required_fields:
        if not EMAIL_CONFIG.get(field):
            missing_fields.append(field)
            print(f"❌ Missing: {field}")
        else:
            # Mask password for display
            if field == 'sender_password':
                display_value = '*' * len(str(EMAIL_CONFIG[field]))
            else:
                display_value = EMAIL_CONFIG[field]
            print(f"✅ {field}: {display_value}")
    
    if missing_fields:
        print(f"\n❌ Missing required fields: {', '.join(missing_fields)}")
        return False
    
    print("\n📤 Attempting to send test email...")
    
    try:
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        msg['Subject'] = "🧪 Test Email - Animal Detection System"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background-color: #d1ecf1; border: 2px solid #0c5460; padding: 20px; border-radius: 5px;">
                <h2 style="color: #0c5460;">✅ Email Configuration Test Successful!</h2>
                <p>Your Animal Detection System is configured correctly and ready to send alerts.</p>
                <hr>
                <p><strong>Test Details:</strong></p>
                <ul>
                    <li><strong>Test Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>SMTP Server:</strong> {EMAIL_CONFIG['smtp_server']}</li>
                    <li><strong>Sender:</strong> {EMAIL_CONFIG['sender_email']}</li>
                    <li><strong>Recipient:</strong> {EMAIL_CONFIG['recipient_email']}</li>
                </ul>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is a test message from your Animal Detection System.
                    You should receive similar alerts when animals are detected.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server
        print(f"🔗 Connecting to {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}...")
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'], timeout=10) as server:
            print("✅ Connected to SMTP server")
            
            print("🔒 Starting TLS encryption...")
            server.starttls()
            print("✅ TLS encryption enabled")
            
            print("🔑 Authenticating...")
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            print("✅ Authentication successful")
            
            print("📨 Sending test email...")
            server.send_message(msg)
            print("✅ Test email sent successfully!")
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Email configuration is working correctly!")
        print("=" * 60)
        print(f"\n📬 Check your inbox at: {EMAIL_CONFIG['recipient_email']}")
        print("   (Check spam folder if you don't see it)")
        print("\n✅ Your system is ready to send animal detection alerts!")
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        print("\n" + "=" * 60)
        print("❌ AUTHENTICATION FAILED")
        print("=" * 60)
        print("\n🔍 Possible causes:")
        print("   1. Incorrect email or password")
        print("   2. Using regular password instead of App Password")
        print("   3. 2-Factor Authentication not enabled")
        print("\n💡 For Gmail:")
        print("   1. Enable 2FA: https://myaccount.google.com/security")
        print("   2. Generate App Password: https://myaccount.google.com/apppasswords")
        print("   3. Use the 16-character app password (not your regular password)")
        print(f"\n📝 Error details: {e}")
        return False
    
    except smtplib.SMTPConnectError as e:
        print("\n" + "=" * 60)
        print("❌ CONNECTION FAILED")
        print("=" * 60)
        print("\n🔍 Possible causes:")
        print("   1. Wrong SMTP server or port")
        print("   2. Firewall blocking connection")
        print("   3. Internet connection issues")
        print(f"\n📝 Error details: {e}")
        return False
    
    except smtplib.SMTPException as e:
        print("\n" + "=" * 60)
        print("❌ SMTP ERROR")
        print("=" * 60)
        print(f"\n📝 Error details: {e}")
        return False
    
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ UNEXPECTED ERROR")
        print("=" * 60)
        print(f"\n📝 Error details: {e}")
        return False


def print_smtp_info():
    """Print common SMTP server configurations."""
    print("\n" + "=" * 60)
    print("📖 COMMON SMTP SERVER CONFIGURATIONS")
    print("=" * 60)
    
    smtp_configs = {
        "Gmail": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "notes": "Requires App Password with 2FA enabled"
        },
        "Yahoo": {
            "smtp_server": "smtp.mail.yahoo.com",
            "smtp_port": 587,
            "notes": "Requires App Password"
        },
        "Outlook/Hotmail": {
            "smtp_server": "smtp-mail.outlook.com",
            "smtp_port": 587,
            "notes": "Use your regular password"
        },
        "Office 365": {
            "smtp_server": "smtp.office365.com",
            "smtp_port": 587,
            "notes": "Use your regular password"
        }
    }
    
    for provider, config in smtp_configs.items():
        print(f"\n{provider}:")
        print(f"  Server: {config['smtp_server']}")
        print(f"  Port: {config['smtp_port']}")
        print(f"  Notes: {config['notes']}")


if __name__ == "__main__":
    success = test_email_config()
    
    if not success:
        print_smtp_info()
        print("\n" + "=" * 60)
        print("Need help? Check SETUP_GUIDE.md for detailed instructions")
        print("=" * 60)