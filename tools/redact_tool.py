import cv2
import os

def apply_redaction(image_path, face_boxes, text_boxes, output_filename="sanitized_output.jpg"):
    """
    Takes an image and lists of coordinates, draws black boxes over them,
    and saves the newly sanitized image.
    """
    # 1. Load the original image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not open image at {image_path}")
        return False

    print("Executing redaction protocols...")

    # 2. Redact Faces (Draw Black Boxes)
    # Coordinates format from our vision tool: [x, y, w, h]
    for (x, y, w, h) in face_boxes:
        # cv2.rectangle(image, top_left, bottom_right, color(B,G,R), thickness)
        # Color (0,0,0) is pitch black. Thickness -1 means "fill the entire box".
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), -1)

    # 3. Redact Sensitive Text (Draw Black Boxes)
    # Coordinates format from our OCR/PII tools: [x, y, w, h]
    for (x, y, w, h) in text_boxes:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), -1)

    # 4. Save the secure, sanitized image
    # We save it as a brand new file so the original isn't accidentally destroyed during testing
    output_path = os.path.join(os.path.dirname(image_path), output_filename)
    cv2.imwrite(output_path, img)

    print(f"✅ Success! Sanitized image saved locally as: {output_filename}")
    return output_path

# --- TESTING BLOCK ---
if __name__ == "__main__":
    # Let's test this on the 'test_photo.jpg' you used for the face detection earlier!
    test_image = "test_photo.jpg" 
    
    # We will simulate the AI handing over coordinates
    # Let's draw a random box on the face (e.g., x=150, y=100) and some text
    dummy_faces = [[150, 100, 80, 80]] 
    dummy_text = [[50, 50, 200, 30]]   
    
    apply_redaction(test_image, dummy_faces, dummy_text)