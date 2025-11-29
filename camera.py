import subprocess
import os

# Global variable to track detection process
detection_process = None


def start_detection_background(sender_email: str = None, recipient_email: str = None):
    """Start the YOLO detection process in the background.

    If `sender_email` is provided, it will be passed to the detection subprocess
    via the `DETECTION_SENDER_EMAIL` environment variable so the detection
    process can use it as the email sender for alerts.
    """
    global detection_process
    try:
        env = os.environ.copy()
        if sender_email:
            env['DETECTION_SENDER_EMAIL'] = sender_email
        if recipient_email:
            env['DETECTION_RECIPIENT_EMAIL'] = recipient_email

        # Start detection.py as a subprocess
        detection_process = subprocess.Popen(
            ['python', 'detection.py'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
    except Exception as e:
        print(f"Error starting detection process: {e}")


def stop_detection_background():
    """Stop the YOLO detection process."""
    global detection_process
    if detection_process:
        try:
            detection_process.terminate()
            detection_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            # Force kill if terminate doesn't work
            detection_process.kill()
            detection_process.wait()
        except Exception as e:
            print(f"Error stopping detection process: {e}")
            try:
                detection_process.kill()
            except:
                pass
        finally:
            detection_process = None
