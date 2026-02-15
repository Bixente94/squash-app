import streamlit as st 
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

# --- CONNEXION GOOGLE SERVICES ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

SHEET_ID = "1VxmG8Pw0-zmnox6EwYWO74mL4Wk71MQTC9D4ajPhvNA"
DRIVE_FOLDER_ID = "1BTNIJpsZz_ndUlHzd8ikaASoFN5-VUD3"
spreadsheet = client.open_by_key(SHEET_ID)

# --- FONCTIONS VISUELLES ---
def flash_screen(color):
    hex_color = "#2ecc71" if color == "green" else "#e74c3c"
    flash_html = f"""
        <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: {hex_color};
            opacity: 0.5; z-index: 9999; pointer-events: none; animation: flash 0.6s ease-out forwards;"></div>
        <style> @keyframes flash {{ 0% {{ opacity: 0.5; }} 100% {{ opacity: 0; }} }} </style>
    """
    st.components.v1.html(flash_html, height=0)

# --- FONCTION DRIVE ---
def upload_to_drive(file, filename):
    if not file: return ""
    try:
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype='image/jpeg')
        up = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()
        f_id = up.get('id')
        # Permission
        service.permissions().create(fileId=f_id, body={'type': 'user', 'role': 'owner', 'emailAddress': 'bixente.barnetche@gmail.com'}, transferOwnership=True, supportsAllDrives=True).execute()
        return up.get('webViewLink')
    except:
        # Si owner échoue, on tente writer
        try:
            service.permissions().create(fileId=f_id, body={'type': 'user', 'role': 'writer', 'emailAddress': 'bixente.barnetche@gmail.com'}, supportsAllDrives=True).execute()
            return up.get('webViewLink')
        except: return up.get('webViewLink') if 'up' in locals() else ""

# --- FONCTIONS SHEETS ---
def get_liste_joueurs():
    ws = spreadsheet.worksheet("COORDONNEES")
    data = ws.get_all_values()[2:] 
    return [f"{row[0]} {row[1]}" for row in data if row[0]]

def verifier_jeu(s1, s2):
    if s1 == 0 and s2 == 0: return False, ""
