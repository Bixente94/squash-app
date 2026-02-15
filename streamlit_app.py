import streamlit as st 
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

# --- CONFIG ET CONNEXION ---
st.set_page_config(page_title="Squash Manager", page_icon="🎾")

try:
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    SHEET_ID = "1VxmG8Pw0-zmnox6EwYWO74mL4Wk71MQTC9D4ajPhvNA"
    DRIVE_FOLDER_ID = "1BTNIJpsZz_ndUlHzd8ikaASoFN5-VUD3"
    spreadsheet = client.open_by_key(SHEET_ID)
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# --- FONCTIONS ---
def flash_screen(color):
    hex_color = "#2ecc71" if color == "green" else "#e74c3c"
    flash_html = f'<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;background-color:{hex_color};opacity:0.4;z-index:9999;pointer-events:none;animation:flash 0.6s ease-out forwards;"></div><style>@keyframes flash{{0%{{opacity:0.4;}}100%{{opacity:0;}}}}</style>'
    st.components.v1.html(flash_html, height=0)

def upload_to_drive(file, filename):
    if not file: return ""
    try:
        service = build('drive', 'v3', credentials=creds)
        meta = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype='image/jpeg')
        up = service.files().create(body=meta, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()
        f_id = up.get('id')
        # Transfert vers ton email
        perm = {'type': 'user', 'role': 'owner', 'emailAddress': 'bixente.barnetche@gmail.com'}
        try:
            service.permissions().create(fileId=f_id, body=perm, transferOwnership=True, supportsAllDrives=True).execute()
        except:
            service.permissions().create(fileId=f_id, body={'type': 'user', 'role': 'writer', 'emailAddress': 'bixente.barnetche@gmail.com'}, supportsAllDrives=True).execute()
        return up.get('webViewLink')
    except: return ""

def get_liste_joueurs():
    ws = spreadsheet.worksheet("COORDONNEES")
    data = ws.get_all_values()[2:] 
    return [f"{row[0]} {row[1]}" for row in data if row[0]]

# --- INTERFACE ---
st.title("🏆 Enregistrement Scores")

liste_joueurs = get_liste_joueurs()
c1, c2 = st.columns(2)
j1_sel = c1.selectbox("Joueur 1", liste_joueurs)
j2_sel = c2.selectbox("Joueur 2", liste_joueurs)

st.divider()

scores_j1, scores_j2 = [], []
sets_j1, sets_j2 = 0, 0

st.write("### 📝 Scores des Sets")
for i in range(1, 6):
    col1, col2, col3 = st.columns([1, 1, 1])
    s1 =
