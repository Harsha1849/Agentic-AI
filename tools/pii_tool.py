from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern

# Initialize the Microsoft Presidio engine
analyzer = AnalyzerEngine()

def get_pii_coordinates(extracted_data):
    """
    Takes the OCR data and flags the coordinates of sensitive information.
    extracted_data format: [{'text': 'word', 'box': [x, y, w, h]}, ...]
    """
    redaction_boxes = []
    
    # --- CUSTOM AADHAAR RECOGNIZER ---
    # We teach the AI what an Indian Aadhaar number looks like using Regex
    aadhaar_pattern = Pattern(
        name="aadhaar_regex", 
        regex=r"\b[2-9][0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b", 
        score=0.85
    )
    aadhaar_recognizer = PatternRecognizer(
        supported_entity="AADHAAR", 
        patterns=[aadhaar_pattern]
    )
    analyzer.registry.add_recognizer(aadhaar_recognizer)
    # ---------------------------------

    print("Analyzing text for sensitive data...")

    # Loop through every word the OCR found
    for item in extracted_data:
        word = item['text']
        box = item['box']
        
        # Ask Presidio to check the word against its database
        # We are looking for Emails, Phone Numbers, and our custom Aadhaar entity
        results = analyzer.analyze(
            text=word, 
            entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "AADHAAR"], 
            language='en'
        )
        
        # If Presidio finds a match, it returns a list of results
        if len(results) > 0:
            entity_type = results[0].entity_type
            print(f"🚨 PII Alert: Found '{word}' -> Type: {entity_type}")
            redaction_boxes.append(box)
            
    return redaction_boxes

# --- TESTING BLOCK ---
if __name__ == "__main__":
    # We will simulate the data coming from your OCR tool to test this instantly
    test_ocr_data = [
        {'text': 'Student', 'box': [10, 10, 50, 20]},
        {'text': 'Email:', 'box': [65, 10, 30, 20]},
        {'text': 'harshaa.bsc23@rvu.edu.in', 'box': [100, 10, 200, 20]},
        {'text': 'ID:', 'box': [10, 40, 20, 20]},
        {'text': '9845', 'box': [35, 40, 30, 20]}, 
        {'text': 'Aadhaar:', 'box': [10, 70, 60, 20]},
        {'text': '4928 1042 8492', 'box': [75, 70, 120, 20]}
    ]
    
    boxes_to_redact = get_pii_coordinates(test_ocr_data)
    
    print(f"\nTotal items that need redaction: {len(boxes_to_redact)}")
    print("Coordinates to send to the blackout tool:")
    print(boxes_to_redact)