import cv2
import pytesseract
import re

def merge_boxes(boxes):
    if not boxes: return []
    boxes.sort(key=lambda b: (b[1], b[0]))
    merged = [boxes[0]]
    for box in boxes[1:]:
        x, y, w, h = box
        lx, ly, lw, lh = merged[-1]
        if abs(y - ly) < 15 and x <= (lx + lw + 40):
            merged[-1] = [min(x, lx), min(y, ly), max(x+w, lx+lw) - min(x, lx), max(y+h, ly+lh) - min(y, ly)]
        else:
            merged.append(box)
    return merged

def get_sensitive_text_boxes(image_path):
    img = cv2.imread(image_path)
    if img is None: return []

    img_h, img_w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Whitelist allows English letters, numbers, and date separators
    custom_config = r'--psm 11 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/-'
    data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT, config=custom_config)

    raw_boxes = []

    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        x, y = data['left'][i], data['top'][i]
        w, h = data['width'][i], data['height'][i]
        
        # Kill micro-dust and ignore the Hindi footer
        if h < 10 or w < 10 or y > (img_h * 0.85): 
            continue 

        word_upper = word.upper()

        # 1. STRICT REGEX (Real PANs & Voter IDs)
        if re.search(r'[A-Z]{5}[0-9O]{4}[A-Z]{1}', word_upper) or re.search(r'[A-Z]{3}[0-9O]{7}', word_upper):
            raw_boxes.append([max(0, x-2), max(0, y-2), w+4, h+4])
            continue

        # 2. ALPHANUMERIC ENTROPY FILTER (The Synthetic PAN Fix)
        # Strip away any stray symbols and check the core length
        clean_alnum = re.sub(r'[^A-Z0-9]', '', word_upper)
        
        if len(clean_alnum) == 10:
            has_letter = any(c.isalpha() for c in clean_alnum)
            has_number = any(c.isdigit() for c in clean_alnum)
            
            # If it's exactly 10 chars and a mix of letters and numbers, it's a PAN.
            if has_letter and has_number:
                raw_boxes.append([max(0, x-2), max(0, y-2), w+4, h+4])
                continue

        # 3. UNIVERSAL DATES (Catches YYYY-MM-DD and DD-MM-YYYY)
        if re.search(r'\d{2,4}[/-]\d{2}[/-]\d{2,4}', word):
            raw_boxes.append([max(0, x-2), max(0, y-2), w+4, h+4])
            continue

        # 4. AADHAAR CHUNKS (Modulo-4 logic)
        clean_digits = re.sub(r'[^0-9]', '', word)
        if len(clean_digits) in [4, 8, 12] and (len(clean_digits) / max(1, len(word))) > 0.6:
            raw_boxes.append([max(0, x-2), max(0, y-2), w+4, h+4])

    return merge_boxes(raw_boxes)