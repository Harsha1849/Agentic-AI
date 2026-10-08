import cv2
import numpy as np
import mediapipe as mp
from pyzbar.pyzbar import decode

# Use model_selection=1 (better for faces slightly further away or lower res)
mp_face_detection = mp.solutions.face_detection
face_detector = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.3)

def get_vision_boxes(image_path):
    img = cv2.imread(image_path)
    if img is None: return []
    
    img_h, img_w = img.shape[:2]
    vision_boxes = []
    document_mode = "UNKNOWN"

    # --- Pre-processing: Contrast Enhancement (CLAHE) ---
    # This cuts through the texture and glare on physical cards
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced_gray = clahe.apply(gray)

    # --- 1. BIOMETRIC ROUTING (MediaPipe Face Detection) ---
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_detector.process(img_rgb)
    
    if results.detections:
        for detection in results.detections:
            bboxC = detection.location_data.relative_bounding_box
            x = int(bboxC.xmin * img_w)
            y = int(bboxC.ymin * img_h)
            w = int(bboxC.width * img_w)
            h = int(bboxC.height * img_h)
            
            vision_boxes.append([max(0, x-10), max(0, y-20), w+20, h+30])
            
            face_center_x = x + (w / 2)
            normalized_rho = face_center_x / img_w
            
            if normalized_rho <= 0.45:
                document_mode = "AADHAAR"
            else:
                document_mode = "PAN"

    # --- 2. ENHANCED QR DETECTION (Pyzbar on Sharpened Image) ---
    decoded_objects = decode(enhanced_gray)
    qr_found = False
    for obj in decoded_objects:
        x, y, w, h = obj.rect
        vision_boxes.append([max(0, x-15), max(0, y-15), w+30, h+30])
        qr_found = True

    # --- 3. DUAL ZONAL MORPHOLOGY (Decoupled from Face Detection) ---
    if not qr_found:
        slices_to_test = []
        
        # If we don't know the mode, we test BOTH sides to be safe.
        if document_mode == "AADHAAR" or document_mode == "UNKNOWN":
            slice_x_start = int(0.60 * img_w)
            slices_to_test.append((enhanced_gray[:, slice_x_start:], slice_x_start)) # Right side
            
        if document_mode == "PAN" or document_mode == "UNKNOWN":
            slice_x_end = int(0.40 * img_w)
            slices_to_test.append((enhanced_gray[:, :slice_x_end], 0)) # Left side

        for target_slice, offset_x in slices_to_test:
            kernel_bh = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
            blackhat = cv2.morphologyEx(target_slice, cv2.MORPH_BLACKHAT, kernel_bh)
            
            _, thresh = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            # Anti-Bridging Erosion
            kernel_erode = np.ones((3, 3), np.uint8)
            eroded = cv2.erode(thresh, kernel_erode, iterations=1)
            
            # Re-dilate
            kernel_dilate = np.ones((15, 15), np.uint8)
            dilated = cv2.dilate(eroded, kernel_dilate, iterations=2)
            
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Lowered threshold to 0.5% of total image size to catch small PAN QRs
                if area > (img_w * img_h * 0.005): 
                    x_slice, y, w, h = cv2.boundingRect(cnt)
                    
                    aspect_ratio = w / float(h)
                    # QRs are square. Allow margin for skew (0.6 to 1.4)
                    if 0.6 <= aspect_ratio <= 1.4:
                        actual_x = x_slice + offset_x
                        vision_boxes.append([max(0, actual_x-15), max(0, y-15), w+30, h+30])

    # --- 4. FALLBACK FACE DETECTION (OpenCV Cascade) ---
    # If MediaPipe failed completely, we use classic Haar Cascades as a safety net
    if document_mode == "UNKNOWN":
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(enhanced_gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
        for (x, y, w, h) in faces:
            vision_boxes.append([max(0, x-10), max(0, y-20), w+20, h+30])

    return vision_boxes