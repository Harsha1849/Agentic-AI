import cv2
import os
import pickle
import numpy as np
from cryptography.fernet import Fernet

# 1. PERSISTENT KEY MANAGEMENT
KEY_FILE = "data/master.key"
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as key_file:
        MASTER_KEY = key_file.read()
else:
    MASTER_KEY = Fernet.generate_key()
    os.makedirs("data", exist_ok=True)
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(MASTER_KEY)

cipher = Fernet(MASTER_KEY)

def secure_and_redact(image_path, face_boxes):
    """Cuts, encrypts (LOSSLESS), redacts via math, and SAVES the vault."""
    img = cv2.imread(image_path)
    if img is None: return None, []

    # THE FIX: Take a snapshot of the clean image
    pristine_img = img.copy()

    encrypted_vault = []
    for (x, y, w, h) in face_boxes:
        
        # EXTRACT FROM THE PRISTINE SNAPSHOT (Prevents overlapping black boxes)
        face_crop = pristine_img[y:y+h, x:x+w]
        
        # Compress losslessly and encrypt
        _, buffer = cv2.imencode('.png', face_crop)
        encrypted_data = cipher.encrypt(buffer.tobytes())
        
        encrypted_vault.append({'coords': [x, y, w, h], 'secret_data': encrypted_data})
        
        # DRAW BLACK BOXES ON THE WORKING IMAGE
        img[y:y+h, x:x+w] = (0, 0, 0)

    # OUTPUT AS PNG TO PREVENT EDGE BLEEDING
    output_path = "cloud_safe_image.png"
    cv2.imwrite(output_path, img)
    
    base_name = os.path.basename(image_path)
    vault_path = f"data/3_crypto_vault/vault_{base_name}.pkl"
    with open(vault_path, "wb") as v_file:
        pickle.dump(encrypted_vault, v_file)

    return output_path, encrypted_vault

def decrypt_and_restore(safe_image_path, original_filename):
    """Unlocks the vault and mathematically restores the pixels."""
    img = cv2.imread(safe_image_path)
    vault_path = f"data/3_crypto_vault/vault_{original_filename}.pkl"
    
    if not os.path.exists(vault_path):
        return None, "Vault file missing. Cannot restore."
        
    with open(vault_path, "rb") as v_file:
        encrypted_vault = pickle.load(v_file)
        
    for patch in encrypted_vault:
        x, y, w, h = patch['coords']
        
        decrypted_bytes = cipher.decrypt(patch['secret_data'])
        nparr = np.frombuffer(decrypted_bytes, np.uint8)
        restored_patch = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Paste exactly w by h pixels
        img[y:y+h, x:x+w] = restored_patch
        
    restored_path = f"data/4_restored_outputs/restored_{original_filename}"
    cv2.imwrite(restored_path, img)
    
    return restored_path, "Success"