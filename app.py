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


# def send_sms_alert(phones, message):
#     client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
#     for phone in phones:
#         if phone.strip():
#             try:
#                 client.messages.create(body=message, from_=TWILIO_PHONE_NUMBER, to=phone.strip())
#             except Exception as e:
#                 st.error(f"SMS sending failed: {e}")


# Initialize SORT tracker
tracker = Sort()

# Color mapping for different classes
COLOR_MAP = {
    'person': (255, 0, 0),  # Blue
    'vehicle': (0, 255, 0),  # Green
    'animal': (0, 0, 255),  # Red
    'tracked': (128, 128, 128)  # Gray for already tracked objects
}

# Confidence threshold
CONFIDENCE_THRESHOLD = 0.5

# Function to classify object type
def get_object_type(label):
    if label in ['person']:
        return 'person'
    elif label in ['car', 'truck', 'bus', 'motorcycle', 'bicycle']:
        return 'vehicle'
    elif label in ['dog', 'cat', 'horse', 'cow']:
        return 'animal'
    return 'unknown'

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

# UI Layout
st.title("Object Detection & Tracking from RTSP & Video Files")
mode = st.sidebar.radio("Choose Mode", ("RTSP Stream", "Upload Video"))

# Alert Storage
detection_log = []
tracked_ids = set()
email_list = st.sidebar.text_area("Enter up to 10 Email IDs (comma-separated)").split(',')
# phone_list = st.sidebar.text_area("Enter up to 10 Mobile Numbers (comma-separated)").split(',')

detection_table = st.empty()

def update_table():
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

if mode == "RTSP Stream":
    rtsp_url = st.text_input("Enter RTSP URL")
    if st.button("Analyze") and rtsp_url:
        process_video(rtsp_url, is_rtsp=True)
elif mode == "Upload Video":
    video_file = st.file_uploader("Upload Video File", type=["mp4", "avi", "mov"])
    if st.button("Analyze") and video_file:
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(video_file.read())
        process_video(tfile.name, is_rtsp=False)

# Export Button
if st.button("Export to Excel"):
    df = pd.DataFrame(detection_log, columns=["Timestamp", "Tracked Object ID", "Class", "Confidence"])
    df.to_excel("detections.xlsx", index=False)
    st.success("Exported Successfully!")
