from ultralytics import YOLO
import cv2
import signal
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
import os
from database import add_detection, add_alert
import threading
import time
import subprocess

# Sound effect mapping for animals
ANIMAL_SOUNDS = {
    'cat': 'sound/cat.mp3',
    'cow': 'sound/cow.mp3',
    'lion': 'sound/lion.mp3'
}


def load_sound_file(animal_type):
    """Load a sound file for the given animal type. Returns file path if exists, None otherwise."""
    sound_file = ANIMAL_SOUNDS.get(animal_type.lower())
    if sound_file and os.path.exists(sound_file):
        return sound_file
    return None


# Import configuration
try:
    from config import EMAIL_CONFIG, DETECTION_CONFIG, TARGET_ANIMALS, SOUND_CONFIG, DATABASE_CONFIG
except ImportError:
    print("⚠️  config.py not found. Using default configuration.")
    EMAIL_CONFIG = {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'jaisuryafirerockers@gmail.com',
        'sender_password': 'dpzsquoolmljfsbx',
        'recipient_email': 'jaisurya230904@gmail.com'
    }
    DETECTION_CONFIG = {
        'confidence_threshold': 0.5,
        'alert_cooldown': 60,
        'camera_index': 0,
        'frame_width': 640,
        'frame_height': 480,
        'save_detection_images': True,
        'detections_folder': 'detections'
    }
    TARGET_ANIMALS = ['bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear']
    SOUND_CONFIG = {'enabled': True, 'beep_frequency': 1000, 'beep_duration': 500, 'beep_count': 3}
    DATABASE_CONFIG = {'user_id': 1}

# Allow overriding sender email from the environment (passed by Flask when starting the subprocess)
env_sender = os.environ.get('DETECTION_SENDER_EMAIL')
if env_sender:
    # Keep SMTP login credentials from EMAIL_CONFIG, but set the From header to the user's email
    EMAIL_CONFIG['override_sender'] = env_sender

# Allow overriding recipient email from environment (passed by Flask when starting the subprocess)
env_recipient = os.environ.get('DETECTION_RECIPIENT_EMAIL')
if env_recipient:
    EMAIL_CONFIG['recipient_email'] = env_recipient

# Global variables
should_exit = False
last_alert_time = {}


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global should_exit
    should_exit = True
    print("\n⏹️  Detection stopped by user.")
    sys.exit(0)


def send_email_alert(animal_type, confidence, image_path=None):
    """Send email alert when animal is detected."""
    if not EMAIL_CONFIG.get('enabled', False):
        return False
    
    if not EMAIL_CONFIG.get('sender_email') or not EMAIL_CONFIG.get('sender_password'):
        print("⚠️  Email not configured. Skipping email alert.")
        return False
    
    try:
        msg = MIMEMultipart()
        # Use override sender (logged-in user's email) for the From header if provided,
        # but authenticate with configured SMTP sender credentials.
        from_header = EMAIL_CONFIG.get('override_sender') or EMAIL_CONFIG.get('sender_email')
        msg['From'] = from_header
        # Also set Reply-To so replies go to the logged-in user when override is used
        if EMAIL_CONFIG.get('override_sender'):
            msg['Reply-To'] = EMAIL_CONFIG.get('override_sender')
        msg['To'] = EMAIL_CONFIG['recipient_email']
        msg['Subject'] = f"🚨 ALERT: {animal_type.upper()} Detected!"
        
        # Email body with HTML formatting
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: #f8d7da; border: 2px solid #d9534f; padding: 20px; border-radius: 5px;">
                <h2 style="color: #d9534f; margin-top: 0;">🚨 Animal Detection Alert</h2>
                <table style="width: 100%; margin-top: 15px;">
                    <tr>
                        <td style="padding: 8px;"><strong>Animal Type:</strong></td>
                        <td style="padding: 8px;">{animal_type.capitalize()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;"><strong>Confidence:</strong></td>
                        <td style="padding: 8px;">{confidence:.2%}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;"><strong>Detection Time:</strong></td>
                        <td style="padding: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;"><strong>Location:</strong></td>
                        <td style="padding: 8px;">Farm Perimeter Camera</td>
                    </tr>
                </table>
            </div>
            <div style="margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                <p style="margin: 0; color: #666; font-size: 14px;">
                    <strong>Action Required:</strong> Please check your farm perimeter.
                    Sound alert has been activated to deter the animal.
                </p>
            </div>
            <hr style="margin-top: 20px; border: none; border-top: 1px solid #ddd;">
            <p style="color: #999; font-size: 12px; margin-top: 20px;">
                This is an automated alert from your Animal Repellent Detection System.
                <br>Powered by YOLO Object Detection
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach detection image if available
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, 'rb') as f:
                    img_data = f.read()
                    image = MIMEImage(img_data, name=os.path.basename(image_path))
                    msg.attach(image)
            except Exception as e:
                print(f"⚠️  Could not attach image: {e}")
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        print(f"✉️  Email alert sent successfully for {animal_type}")
        return True
    
    except smtplib.SMTPAuthenticationError:
        print("❌ Email authentication failed. Please check your email and app password.")
        return False
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def play_sound_alert(animal_type=None):
    """Play sound alert. If animal_type is provided, try to play the corresponding sound file.
    Otherwise fall back to beep."""
    if not SOUND_CONFIG.get('enabled', True):
        return
    
    # Try to play animal-specific sound if provided
    if animal_type:
        sound_file = load_sound_file(animal_type)
        if sound_file:
            try:
                # Try to play sound using Windows Media Player or ffplay
                try:
                    # Windows: use Windows Media Player
                    subprocess.Popen(['powershell', '-Command', f'(New-Object Media.SoundPlayer "{sound_file}").PlaySync()'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"🔊 Playing sound alert for {animal_type}: {sound_file}")
                    return
                except Exception:
                    # Try ffplay if available
                    try:
                        subprocess.run(['ffplay', '-nodisp', '-autoexit', sound_file],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                        print(f"🔊 Playing sound alert for {animal_type}: {sound_file}")
                        return
                    except Exception:
                        print(f"⚠️  Could not play {sound_file}, falling back to beep")
            except Exception as e:
                print(f"⚠️  Error playing sound: {e}")
    
    # Fall back to beep
    try:
        import winsound
        for _ in range(SOUND_CONFIG.get('beep_count', 3)):
            winsound.Beep(
                SOUND_CONFIG.get('beep_frequency', 1000), 
                SOUND_CONFIG.get('beep_duration', 500)
            )
            time.sleep(0.2)
        print("🔊 Sound alert played (beep)")
    except ImportError:
        # winsound is Windows-only
        print("⚠️  Sound alert not available on this platform")
    except Exception as e:
        print(f"⚠️  Sound alert error: {e}")


def should_send_alert(animal_type):
    """Check if enough time has passed since last alert."""
    current_time = time.time()
    cooldown = DETECTION_CONFIG.get('alert_cooldown', 60)
    
    if animal_type not in last_alert_time:
        last_alert_time[animal_type] = current_time
        return True
    
    if current_time - last_alert_time[animal_type] >= cooldown:
        last_alert_time[animal_type] = current_time
        return True
    
    return False


def save_detection_image(frame, animal_type):
    """Save detected frame as image."""
    if not DETECTION_CONFIG.get('save_detection_images', True):
        return None
    
    try:
        folder = DETECTION_CONFIG.get('detections_folder', 'detections')
        os.makedirs(folder, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"detection_{animal_type}_{timestamp}.jpg"
        filepath = os.path.join(folder, filename)
        
        cv2.imwrite(filepath, frame)
        print(f"💾 Detection image saved: {filename}")
        return filepath
    except Exception as e:
        print(f"⚠️  Failed to save detection image: {e}")
        return None


def main():
    """Main detection loop."""
    global should_exit
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Load YOLO model
    print("=" * 60)
    print("🐾 ANIMAL DETECTION SYSTEM")
    print("=" * 60)
    print("🔄 Loading YOLO model...")
    try:
        model = YOLO("yolov8n.pt")
        print("✅ YOLO model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load YOLO model: {e}")
        print("💡 Make sure yolov8n.pt is in the current directory")
        sys.exit(1)
    
    # Open camera
    camera_index = DETECTION_CONFIG.get('camera_index', 0)
    print(f"📷 Opening camera (index: {camera_index})...")
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ Could not open camera {camera_index}")
        print("💡 Try changing camera_index in config.py")
        sys.exit(1)
    
    print("✅ Camera opened successfully")
    print("=" * 60)
    print(f"🎯 Monitoring for: {', '.join(TARGET_ANIMALS)}")
    print(f"⚙️  Confidence threshold: {DETECTION_CONFIG.get('confidence_threshold', 0.5)}")
    print(f"📧 Email alerts: {'Enabled' if EMAIL_CONFIG.get('enabled') else 'Disabled'}")
    print(f"🔊 Sound alerts: {'Enabled' if SOUND_CONFIG.get('enabled') else 'Disabled'}")
    print(f"⏱️  Alert cooldown: {DETECTION_CONFIG.get('alert_cooldown', 60)}s")
    print("=" * 60)
    print("⏹️  Press Ctrl+C or 'q' to stop detection\n")
    
    # Detection variables
    frame_count = 0
    detection_count = 0
    user_id = DATABASE_CONFIG.get('user_id', 1)
    confidence_threshold = DETECTION_CONFIG.get('confidence_threshold', 0.5)
    frame_width = DETECTION_CONFIG.get('frame_width', 640)
    frame_height = DETECTION_CONFIG.get('frame_height', 480)
    
    try:
        while not should_exit:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame from camera")
                break
            
            frame_count += 1
            display_frame = frame.copy()
            process_frame = cv2.resize(frame, (frame_width, frame_height))
            
            # Run YOLO detection
            results = model(process_frame, verbose=False)
            
            # Process detections
            detected_animals = set()
            
            for r in results:
                for box in r.boxes:
                    try:
                        cls = int(box.cls[0])
                        label = model.names[cls].lower()
                        confidence = float(box.conf[0])
                        
                        # Check if target animal with sufficient confidence
                        if label in TARGET_ANIMALS and confidence > confidence_threshold:
                            detected_animals.add(label)
                            
                            # Scale coordinates back to original frame
                            x1, y1, x2, y2 = box.xyxy[0]
                            scale_x = frame.shape[1] / process_frame.shape[1]
                            scale_y = frame.shape[0] / process_frame.shape[0]
                            
                            x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
                            x2, y2 = int(x2 * scale_x), int(y2 * scale_y)
                            
                            # Draw bounding box
                            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                            
                            # Add label
                            text = f"{label.upper()} {confidence:.2f}"
                            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                            cv2.rectangle(display_frame, (x1, y1 - text_size[1] - 10),
                                        (x1 + text_size[0], y1), (0, 0, 255), -1)
                            cv2.putText(display_frame, text, (x1, y1 - 5),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                            
                            # Trigger alerts if cooldown period passed
                            if should_send_alert(label):
                                detection_count += 1
                                print(f"\n🚨 ALERT #{detection_count}: {label.upper()} detected!")
                                print(f"   Confidence: {confidence:.2%}")
                                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                                
                                # Save image
                                image_path = save_detection_image(frame, label)
                                
                                # Play sound (non-blocking)
                                threading.Thread(target=play_sound_alert, args=(label,), daemon=True).start()
                                
                                # Send email (non-blocking)
                                threading.Thread(
                                    target=send_email_alert,
                                    args=(label, confidence, image_path),
                                    daemon=True
                                ).start()
                                
                                # Save to database
                                try:
                                    add_detection(user_id, label.capitalize(), "Camera Feed")
                                    add_alert(user_id, 
                                            f"{label.capitalize()} detected - Alert activated",
                                            "danger")
                                except Exception as e:
                                    print(f"⚠️  Database error: {e}")
                    
                    except Exception as e:
                        print(f"⚠️  Error processing detection: {e}")
                        continue
            
            # Add status overlay
            status_text = f"Frame: {frame_count} | Alerts: {detection_count}"
            cv2.putText(display_frame, status_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if detected_animals:
                alert_text = f"DETECTED: {', '.join([a.upper() for a in detected_animals])}"
                cv2.putText(display_frame, alert_text, (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display frame
            cv2.imshow("Animal Detection System - Press 'q' to quit", display_frame)
            
            # Status update every 30 frames
            if frame_count % 30 == 0:
                print(f"📊 Frames: {frame_count} | Alerts: {detection_count}")
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\n⏹️  Detection interrupted")
    except Exception as e:
        print(f"\n❌ Error during detection: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\n" + "=" * 60)
        print("📊 FINAL STATISTICS")
        print("=" * 60)
        print(f"   Total frames processed: {frame_count}")
        print(f"   Total alerts sent: {detection_count}")
        print("=" * 60)
        print("✅ Detection system stopped successfully")


if __name__ == "__main__":
    main()