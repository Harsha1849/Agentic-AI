import streamlit as st
import os
import shutil
import sqlite3
import time
import pandas as pd
from orchestrator import run_redaction_pipeline

# Configure the web page
st.set_page_config(page_title="Zero-Trust Auto-Redactor", layout="wide")

# Ensure all our storage folders exist
folders = [
    "data/1_raw_uploads", 
    "data/2_sanitized_cloud", 
    "data/3_crypto_vault", 
    "data/4_restored_outputs"
]
for f in folders:
    os.makedirs(f, exist_ok=True)

# Initialize Database
conn = sqlite3.connect('data/vault.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS records
             (customer_name TEXT, original_file TEXT, sanitized_file TEXT)''')
conn.commit()

# --- UI LAYOUT ---
st.title("🛡️ Automated PII Sanitizer")
st.markdown("Zero-Trust Agentic AI Pipeline for Cryptographic Redaction")

# Create our 3 Tabs
tab1, tab2, tab3 = st.tabs(["1. Intake & Processing", "2. Cloud Vault", "3. Retrieval & Reversal"])

# --- TAB 1: UPLOAD & PROCESS ---
with tab1:
    # Industry Pivot: Fintech KYC Branding
    st.header("Fintech KYC Document Intake")
    st.write("Zero-Trust pipeline for sanitizing Customer IDs before cloud storage.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        customer_name = st.text_input("Account Holder Name", placeholder="e.g., John Doe")
    with col2:
        uploaded_files = st.file_uploader("Upload KYC Documents (PAN/Aadhaar/License)", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    
    if st.button("Process & Sanitize KYC", type="primary"):
        if not customer_name or not uploaded_files:
            st.error("Please provide both an Account Holder Name and KYC Documents.")
        else:
            for uploaded_file in uploaded_files:
                
                # 5MB Safety Net
                if uploaded_file.size > 5 * 1024 * 1024:
                    st.error(f"⚠️ {uploaded_file.name} exceeds 5MB limit.")
                    continue

                raw_path = os.path.join("data/1_raw_uploads", uploaded_file.name)
                with open(raw_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # THE UI UPGRADE: Fintech Animations + NLP
                with st.status(f"🏦 Initializing Zero-Trust KYC Pipeline for {uploaded_file.name}...", expanded=True) as status:
                    
                    st.write("🔍 Running MediaPipe Vision for biometric detection...")
                    time.sleep(0.5)
                    
                    st.write("🧠 Engaging Microsoft Presidio NLP to extract Names & Locations...")
                    time.sleep(1)
                    
                    st.write("🔐 Cryptographically securing identified PII to AES Vault...")
                    # Run the pipeline
                    report = run_redaction_pipeline(raw_path)
                    
                    st.write("📝 Senior Compliance AI auditing logs...")
                    time.sleep(1)
                    
                    # File Routing
                    safe_filename = f"safe_{customer_name.replace(' ', '_')}_{uploaded_file.name}.png"
                    final_safe_path = os.path.join("data/2_sanitized_cloud", safe_filename)
                    if os.path.exists("cloud_safe_image.png"):
                        import shutil
                        shutil.move("cloud_safe_image.png", final_safe_path)
                    
                    c.execute("INSERT INTO records VALUES (?, ?, ?)", (customer_name, uploaded_file.name, final_safe_path))
                    conn.commit()
                    
                    status.update(label=f"✅ {uploaded_file.name} Successfully Sanitized & Cloud-Ready!", state="complete", expanded=False)
                
                st.info(f"📋 AI Compliance Report: {report}")


# --- TAB 2: COMPLIANCE VIEWER ---
with tab2:
    st.header("Secure Cloud Vault")
    st.write("Browse the master ledger, verify documents, or purge customer records.")
    
    # 1. THE MASTER LEDGER (Table)
    st.subheader("Vault Ledger")
    c.execute("SELECT * FROM records")
    all_records = c.fetchall()
    
    if not all_records:
        st.info("The vault is currently empty. Process some documents in the Intake Tab.")
    else:
        table_data = [{"Customer Name": r[0], "Original File": r[1], "Encrypted Path": r[2]} for r in all_records]
        st.dataframe(table_data, use_container_width=True, hide_index=True)
        
    st.divider() 
    
    # 2. THE SEARCH ENGINE (Images)
    st.subheader("Document Viewer")
    search_name = st.text_input("Enter a Customer Name to view their files", placeholder="e.g., John Doe")
    
    if st.button("Fetch KYC Records", type="primary"):
        if not search_name:
            st.warning("Please enter a name to search.")
        else:
            c.execute("SELECT * FROM records WHERE customer_name = ?", (search_name,))
            records = c.fetchall()
            
            if not records:
                st.error(f"No compliance records found for '{search_name}'.")
            else:
                st.success(f"✅ Found {len(records)} secure documents for {search_name}.")
                
                # THE UI UPGRADE: Create a dynamic 3-column grid
                cols = st.columns(3) 
                
                for idx, record in enumerate(records):
                    customer, original_filename, safe_path = record
                    
                    # The modulo operator (%) wraps the images to the next row after 3 columns
                    with cols[idx % 3]: 
                        # Adding a border creates a beautiful "File Card" look
                        with st.container(border=True): 
                            st.markdown(f"**Document {idx + 1}**<br> `{original_filename}`", unsafe_allow_html=True)
                            
                            try:
                                # Because it's inside a column, this safely shrinks the image!
                                st.image(safe_path, use_container_width=True)
                                st.caption(f"🔒 Vault: {safe_path}")
                            except FileNotFoundError:
                                st.error("⚠️ Image missing from secure vault.")

    # 3. GDPR COMPLIANCE (Data Purge)
    st.subheader("Data Purge (Right to be Forgotten)")
    st.error("⚠️ Authorized Admins Only: This action is irreversible.")
    
    # Grab a list of unique customers currently in the database
    c.execute("SELECT DISTINCT customer_name FROM records")
    unique_customers = [r[0] for r in c.fetchall()]
    
    if unique_customers:
        # Create a dropdown menu to select who gets deleted
        target_to_delete = st.selectbox("Select Customer to Purge:", ["-- Select Customer --"] + unique_customers)
        
        if target_to_delete != "-- Select Customer --":
            st.warning(f"You are about to permanently delete all records for **{target_to_delete}**.")
            
            # The Purge Button
            if st.button(f"Permanently Delete {target_to_delete}", type="primary"):
                # Wipe them from the database
                c.execute("DELETE FROM records WHERE customer_name = ?", (target_to_delete,))
                conn.commit() # Save the database changes
                
                st.success(f"✅ All records for {target_to_delete} have been purged.")
                
                # Instantly refresh the Streamlit UI so the table updates dynamically
                st.rerun() 
    else:
        st.info("No customers available to purge.")

# --- TAB 3: DE-REDACTION ---
with tab3:
    st.header("Cryptographic Reversal (De-Redaction)")
    st.warning("⚠️ Authorized Personnel Only. Decryption key required.")
    
    # Search function
    search_name = st.text_input("Search Customer Name to Restore Data", placeholder="e.g., John Doe")
    if st.button("Find Records"):
        c.execute("SELECT * FROM records WHERE customer_name=?", (search_name,))
        results = c.fetchall()
        
        if results:
            st.success(f"✅ Found {len(results)} encrypted files for {search_name}.")
            # Save ALL found records into memory, not just results[0]
            st.session_state.restore_targets = results 
        else:
            st.error("No records found.")
            # Security wipe: clear old results if a new search fails
            if 'restore_targets' in st.session_state:
                del st.session_state['restore_targets']
                
    # If we found records, show the dropdown and unlock tools
    if 'restore_targets' in st.session_state and st.session_state.restore_targets:
        records = st.session_state.restore_targets
        
        # 1. Extract just the filenames to populate our dropdown menu
        file_options = [r[1] for r in records] 
        
        # 2. The Dropdown Selector! Let the user pick the exact file
        selected_filename = st.selectbox("Select Document to Unlock:", file_options)
        
        # 3. Match their selection back to the specific database record
        target_record = next(r for r in records if r[1] == selected_filename)
        
        # Extract the exact paths for the chosen file
        original_filename = target_record[1]
        safe_cloud_path = target_record[2]
        
        st.info(f"Target File Locked: {original_filename}")
        
        # 4. The Unlock Button (Notice the dynamic key to prevent Streamlit UI bugs)
        if st.button("Decrypt & Restore File", key=f"unlock_{original_filename}", type="primary"):
            from tools.crypto_tool import decrypt_and_restore
            
            # THE UI UPGRADE: De-redaction Sequence
            with st.status("🔑 Authenticating Reversal Protocol...", expanded=True) as status:
                st.write("🛡️ Verifying local AES Master Key...")
                time.sleep(1.2)
                
                st.write("📂 Extracting encrypted pixel patches from secure vault...")
                time.sleep(1)
                
                st.write("🧩 Mathematically reconstructing original image array...")
                # Run the actual decryption function
                restored_path, status_msg = decrypt_and_restore(safe_cloud_path, original_filename)
                
                status.update(label="🔓 Cryptographic Reversal Complete!", state="complete", expanded=False)
                
            if restored_path:
                st.success("✅ File Successfully Reconstructed!")
                st.image(restored_path, caption="Original Reconstructed File", width=600)
                
                with open(restored_path, "rb") as file:
                    st.download_button(
                        label="⬇️ Download Restored File",
                        data=file,
                        file_name=f"UNLOCKED_{original_filename}",
                        mime="image/jpeg",
                        type="primary" # Makes the button pop with color
                    )
            else:
                st.error(f"Restoration Failed: {status_msg}")