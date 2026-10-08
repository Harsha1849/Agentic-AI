import os
import sys
from crewai import Agent, Task, Crew, Process, LLM

# Add the 'tools' folder to Python's system path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

# --- THE FIX: Updated Imports ---
from tools.ocr_tool import get_sensitive_text_boxes
from tools.vision_tool import get_vision_boxes # <-- Updated to match the new vision_tool.py
from tools.crypto_tool import secure_and_redact

# 1. Connect to local LLM
local_llm = LLM(
    model="ollama/qwen2.5:1.5b",
    base_url="http://localhost:11434"
)

# 2. Define the Agent
auditor_agent = Agent(
    role='Senior Compliance Auditor',
    goal='Write professional audit reports based on redaction logs.',
    backstory='Strict auditor ensuring zero-trust privacy and clear documentation.',
    verbose=False, 
    llm=local_llm
)

# 3. The Omnivore Pipeline (Zero-Trust)
def run_redaction_pipeline(target_image_path):
    print("\n--- INITIATING ZERO-TRUST KYC PIPELINE ---")
    
    # STEP A: Scan for Visuals (Faces & QR Codes via Biometric Routing)
    visual_coords = get_vision_boxes(target_image_path) # <-- Updated function call
    print(f"Visual Biometrics/QR found: {len(visual_coords)}")
    
    # STEP B: Scan for Sensitive Text (OCR + Alphanumeric Entropy Fallback)
    text_coords = get_sensitive_text_boxes(target_image_path)
    print(f"Sensitive text blocks found: {len(text_coords)}")
    
    # STEP C: Combine all coordinates into one master list
    all_targets = visual_coords + text_coords
    
    if not all_targets:
        return "Audit Report: No human faces, QR codes, or sensitive text detected. File is clean."
        
    # STEP D: Send the combined list to the Crypto Vault
    safe_image_path, vault = secure_and_redact(target_image_path, all_targets)
    
    # STEP E: Local LLM Auditing
    task = Task(
        description=f'I just ran an automated zero-trust script on an image. I found {len(visual_coords)} visual targets (faces/QR) and {len(text_coords)} sensitive text blocks (PII). I generated {len(vault)} encrypted patches in the SQLite vault. Write a highly professional, 2-sentence audit report confirming the file is sanitized and safe for the cloud.',
        expected_output='A 2-sentence text report.',
        agent=auditor_agent
    )
    
    crew = Crew(
        agents=[auditor_agent],
        tasks=[task],
        process=Process.sequential
    )
    
    report = crew.kickoff()
    return report