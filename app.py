import streamlit as st
import pandas as pd
import cv2
import vlc
import os
import tempfile
import time
from datetime import datetime, time
import streamlit as st
import cv2
import numpy as np
import pandas as pd
import ultralytics
import smtplib
# from twilio.rest import Client
import os
import vlc
import time
import tempfile
from sort import Sort  # Import SORT tracker
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Confidence threshold
CONFIDENCE_THRESHOLD = 0.5

def send_brevo_email(sender_email, recipient_email, subject, body):
    # SMTP server details for Brevo
    smtp_server = "smtp-relay.brevo.com"
    port = 587
    login = "86dc5e001@smtp-brevo.com"
    password = "L9fFAntD2p3OIaz4"
    
    # Set up the MIME
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    
    # Add body to email
    message.attach(MIMEText(body, 'plain'))
    
    # Connect to SMTP server
    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()  # Secure the connection
            server.login(login, password)
            server.send_message(message)
            print("Email sent successfully!")
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

sender = "amit.freelancedl@gmail.com"  # This can be any email you want to appear as the sender
recipient = "amit.rawool@gmail.com"  # The email where you want to receive the test

# Load YOLOv8 model
yolo_model = ultralytics.YOLO('yolov8s.pt')

def send_email_alert(emails, message):
    sender_email = "strucmon.nexgenhitech@gmail.com"
    sender_password = "Fiat#1622"

    for email in emails:
        subject = "CAMCOM Alert"

        send_brevo_email(sender, email, subject, message)

# Function to classify object type
def get_object_type(label):
    if label in ['person']:
        return 'person'
    elif label in ['car', 'truck', 'bus', 'motorcycle', 'bicycle']:
        return 'vehicle'
    elif label in ['dog', 'cat', 'horse', 'cow']:
        return 'animal'
    return 'unknown'

# Initialize SORT tracker
tracker = Sort()

# Color mapping for different classes
COLOR_MAP = {
    'person': (255, 0, 0),  # Blue
    'vehicle': (0, 255, 0),  # Green
    'animal': (0, 0, 255),  # Red
    'tracked': (128, 128, 128)  # Gray for already tracked objects
}

# Custom CSS for Enterprise-Style UI
def apply_custom_styling():
    st.markdown("""
    <style>
    /* Custom Color Palette */
    :root {
        --primary-color: #2c3e50;
        --secondary-color: #34495e;
        --accent-color: #3498db;
        --background-color: #ecf0f1;
        --text-color: #2c3e50;
    }

    /* Global Styling */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
        font-family: 'Inter', 'Roboto', sans-serif;
    }

    /* Header Styling */
    .stMarkdown h1 {
        color: var(--primary-color);
        font-weight: 700;
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 2px solid var(--accent-color);
        padding-bottom: 10px;
    }

    /* Sidebar Styling */
    .css-1aumxhk {
        background-color: var(--secondary-color);
        color: white;
    }

    /* Button Styling */
    .stButton>button {
        background-color: var(--accent-color);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #2980b9;
        transform: scale(1.05);
    }

    /* Data Table Styling */
    .dataframe {
        border: 1px solid #ddd;
        border-radius: 5px;
        overflow: hidden;
    }

    /* Footer Styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: var(--primary-color);
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 0.8em;
    }
    </style>
    """, unsafe_allow_html=True)

def create_footer():
    st.markdown("""
    <div class="footer">
        ©2024 Copyright Dr. Ajay Kumar Jha | All rights reserved.
    </div>
    """, unsafe_allow_html=True)

# Function to process frames and perform object detection with tracking
def detect_objects_with_tracking(frame):
    results = yolo_model(frame)
    detections = results[0].boxes.data.cpu().numpy()  # Extract detections
    object_list = []
    object_classes = {}
    confidence_scores = {}
    
    for i, det in enumerate(detections):
        x1, y1, x2, y2, confidence, class_id = det
        label = yolo_model.names[int(class_id)]
        obj_type = get_object_type(label)
        if obj_type != 'unknown' and confidence >= CONFIDENCE_THRESHOLD:
            object_list.append([x1, y1, x2, y2, 1])  # Format for SORT
            object_classes[len(object_list) - 1] = obj_type
            confidence_scores[len(object_list) - 1] = confidence
    
    object_list = np.array(object_list)
    tracked_objects = tracker.update(object_list)  # Track objects across frames
    
    return tracked_objects, object_classes, confidence_scores  # Returns tracked bounding boxes with unique IDs, object types, and confidence scores


def main():
    # Apply custom styling
    st.set_page_config(
        page_title="CAMCOM",
        page_icon=":detective:",  # You can use an emoji or path to an .png/.ico file
        # layout="wide",  # Optional: use 'wide' layout for more screen space
        initial_sidebar_state="expanded"  # Optional: keep sidebar open by default
    )
    apply_custom_styling()

    # Main App Title
    st.title("CAMCOM: Detection & Tracking Platform")
    
    current_datetime = datetime.now()

    # Specify a specific date
    specific_date = datetime(2025, 3, 25)
    # Compare dates
    if current_datetime > specific_date and not os.environ.get("CONTINUE_OPERATION", ""):
        st.text("Error in running application, please contact Administrator.")
        return

    # Sidebar Configuration
    st.sidebar.image("logo.png", width=250)  # Replace with actual logo path
    st.sidebar.header("Detection Configuration")

    # Mode Selection with Card-like Design
    mode = st.sidebar.radio(
        "Select Detection Mode", 
        ("RTSP Stream", "Upload Video"),
        help="Choose your video input method"
    )

    # Email Notification Configuration
    st.sidebar.subheader("Notification Settings")
    email_list = st.sidebar.text_area(
        "Enter Email IDs (comma-separated)", 
        placeholder="alerts@company.com, security@company.com"
    ).split(',')

    # Detection Log and Tracking
    detection_log = []
    tracked_ids = set()

    # Detection Table
    detection_table = st.empty()

    def update_table():
        if detection_log:
            df = pd.DataFrame(detection_log, columns=["Timestamp", "Tracked Object ID", "Class", "Confidence"])
            detection_table.dataframe(df)

    def process_video(source, is_rtsp=False):
        instance, player = None, None
        cap = None
        if is_rtsp:
            # instance = vlc.Instance("--no-video")
            instance = vlc.Instance()
            player = instance.media_player_new()
            media = instance.media_new(source)
            player.set_media(media)
            player.play()
        else:
            cap = cv2.VideoCapture(source)
        
        stframe = st.empty()
        
        while True:
            frame = None
            if is_rtsp:
                time.sleep(0.1)
                frame = player.video_take_snapshot(0, "snapshot.jpg", 640, 480)
                if os.path.exists("snapshot.jpg"):
                    frame = cv2.imread("snapshot.jpg")                
            else:
                ret, frame = cap.read()
                if not ret:
                    break
            
            if frame is None:
                continue
            
            tracked_objects, object_classes, confidence_scores = detect_objects_with_tracking(frame)
            for i, obj in enumerate(tracked_objects):
                x1, y1, x2, y2, obj_id = map(int, obj)
                obj_type = object_classes.get(i, 'unknown')
                confidence = confidence_scores.get(i, 0)
                color = COLOR_MAP['tracked'] if obj_id in tracked_ids else COLOR_MAP.get(obj_type, (255, 255, 255))
                if obj_id not in tracked_ids:
                    send_email_alert(email_list, f"Object type {obj_type} detected at {time.strftime('%Y-%m-%d %H:%M:%S')}")

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"object ({confidence:.2f})", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                if obj_id not in tracked_ids:
                    detection_log.append((time.strftime('%Y-%m-%d %H:%M:%S'), obj_id, obj_type, confidence))
                    tracked_ids.add(obj_id)
                    update_table()
            
            stframe.image(frame, channels="BGR")
    
        if cap:
            cap.release()

    # Video Input Section
    if mode == "RTSP Stream":
        rtsp_url = st.text_input(
            "Enter RTSP Stream URL", 
            placeholder="rtsp://camera.example.com/stream"
        )
        if st.button("Start Analysis"):
            if rtsp_url:
                process_video(rtsp_url, is_rtsp=True)
            else:
                st.warning("Please enter a valid RTSP URL")

    elif mode == "Upload Video":
        video_file = st.file_uploader(
            "Upload Video File", 
            type=["mp4", "avi", "mov"],
            help="Supported formats: MP4, AVI, MOV"
        )
        
        if st.button("Start Analysis") and video_file:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(video_file.read())
            process_video(tfile.name, is_rtsp=False)

    # Export Functionality
    st.sidebar.subheader("Export Options")
    if st.sidebar.button("Export Detections to Excel"):
        if detection_log:
            df = pd.DataFrame(detection_log, columns=["Timestamp", "Tracked Object ID", "Class", "Confidence"])
            filename = f"detections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            st.sidebar.success(f"Exported to {filename}")
        else:
            st.sidebar.warning("No detection logs to export")

    # Footer
    create_footer()

if __name__ == "__main__":
    main()
