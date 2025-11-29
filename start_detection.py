#!/usr/bin/env python3
"""
Animal Detection System Launcher
Easy-to-use launcher with menu options
"""

import os
import sys
import subprocess


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print application header."""
    print("=" * 70)
    print("🐾 ANIMAL DETECTION & REPELLENT SYSTEM")
    print("=" * 70)
    print()


def check_requirements():
    """Check if required packages are installed."""
    required_packages = {
        'ultralytics': 'YOLO',
        'cv2': 'OpenCV',
        'flask': 'Flask',
        'PIL': 'Pillow'
    }
    
    missing = []
    for package, name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing.append(name)
    
    return missing


def check_files():
    """Check if required files exist."""
    required_files = ['app.py', 'detection.py', 'database.py']
    missing = [f for f in required_files if not os.path.exists(f)]
    return missing


def test_camera():
    """Quick camera test."""
    print("📷 Testing camera...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Camera is working!")
            cap.release()
            return True
        else:
            print("❌ Camera not accessible")
            return False
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False


def run_detection():
    """Run standalone detection."""
    print("\n🚀 Starting Animal Detection System...")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 70)
    try:
        subprocess.run([sys.executable, 'detection.py'])
    except KeyboardInterrupt:
        print("\n✅ Detection stopped")


def run_web_app():
    """Run Flask web application."""
    print("\n🌐 Starting Web Application...")
    print("📱 Access at: http://127.0.0.1:5000")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 70)
    try:
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\n✅ Web app stopped")


def test_email():
    """Test email configuration."""
    print("\n📧 Testing Email Configuration...")
    print("-" * 70)
    try:
        subprocess.run([sys.executable, 'test_email.py'])
    except FileNotFoundError:
        print("❌ test_email.py not found")
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled")


def show_config():
    """Display current configuration."""
    print("\n⚙️  CURRENT CONFIGURATION")
    print("-" * 70)
    try:
        from config import EMAIL_CONFIG, DETECTION_CONFIG, TARGET_ANIMALS
        
        print("\n📧 Email Settings:")
        print(f"   Enabled: {EMAIL_CONFIG.get('enabled', False)}")
        print(f"   SMTP Server: {EMAIL_CONFIG.get('smtp_server', 'Not set')}")
        print(f"   Sender: {EMAIL_CONFIG.get('sender_email', 'Not set')}")
        print(f"   Recipient: {EMAIL_CONFIG.get('recipient_email', 'Not set')}")
        
        print("\n🎯 Detection Settings:")
        print(f"   Confidence Threshold: {DETECTION_CONFIG.get('confidence_threshold', 0.5)}")
        print(f"   Alert Cooldown: {DETECTION_CONFIG.get('alert_cooldown', 60)}s")
        print(f"   Camera Index: {DETECTION_CONFIG.get('camera_index', 0)}")
        print(f"   Save Images: {DETECTION_CONFIG.get('save_detection_images', True)}")
        
        print(f"\n🐾 Target Animals ({len(TARGET_ANIMALS)}):")
        for i in range(0, len(TARGET_ANIMALS), 5):
            animals = TARGET_ANIMALS[i:i+5]
            print(f"   {', '.join(animals)}")
        
    except ImportError:
        print("⚠️  config.py not found - using defaults")
    
    input("\n📄 Press Enter to continue...")


def install_requirements():
    """Install required packages."""
    print("\n📦 Installing Required Packages...")
    print("-" * 70)
    packages = [
        'ultralytics',
        'opencv-python',
        'flask',
        'pillow',
        'werkzeug'
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package],
                check=True
            )
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
    
    print("\n✅ Installation complete!")
    input("Press Enter to continue...")


def main_menu():
    """Display main menu and handle user input."""
    while True:
        clear_screen()
        print_header()
        
        # Check system status
        missing_packages = check_requirements()
        missing_files = check_files()
        
        if missing_packages:
            print("⚠️  Missing packages:", ', '.join(missing_packages))
            print("   Select option 9 to install\n")
        
        if missing_files:
            print("⚠️  Missing files:", ', '.join(missing_files))
            print("   Make sure all project files are in the current directory\n")
        
        # Menu options
        print("MAIN MENU")
        print("-" * 70)
        print("1. 🎥  Start Animal Detection (Camera)")
        print("2. 🌐  Start Web Application")
        print("3. 📧  Test Email Configuration")
        print("4. 📷  Test Camera")
        print("5. ⚙️   Show Configuration")
        print("6. 📖  View Setup Guide")
        print("9. 📦  Install/Update Requirements")
        print("0. 🚪  Exit")
        print("-" * 70)
        
        choice = input("\nSelect option (0-9): ").strip()
        
        if choice == '1':
            if missing_packages or missing_files:
                print("\n❌ Cannot start: Missing requirements")
                input("Press Enter to continue...")
            else:
                run_detection()
                input("\nPress Enter to continue...")
        
        elif choice == '2':
            if missing_packages or missing_files:
                print("\n❌ Cannot start: Missing requirements")
                input("Press Enter to continue...")
            else:
                run_web_app()
                input("\nPress Enter to continue...")
        
        elif choice == '3':
            test_email()
            input("\nPress Enter to continue...")
        
        elif choice == '4':
            test_camera()
            input("\nPress Enter to continue...")
        
        elif choice == '5':
            show_config()
        
        elif choice == '6':
            print("\n📖 Opening SETUP_GUIDE.md...")
            if os.path.exists('SETUP_GUIDE.md'):
                if sys.platform == 'win32':
                    os.startfile('SETUP_GUIDE.md')
                else:
                    subprocess.run(['open', 'SETUP_GUIDE.md'], check=False)
            else:
                print("❌ SETUP_GUIDE.md not found")
            input("\nPress Enter to continue...")
        
        elif choice == '9':
            install_requirements()
        
        elif choice == '0':
            print("\n👋 Thank you for using Animal Detection System!")
            print("=" * 70)
            sys.exit(0)
        
        else:
            print("\n❌ Invalid option. Please try again.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)