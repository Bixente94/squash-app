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
    st.error(f"Erreur de connexion aux services Google : {e}")
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
        file_metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype='image/jpeg')
        up = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()
        f_id = up.get('id')
        # Transfert de propriété vers ton email
        try:
            service.permissions().create(fileId=f_id, body={'type': 'user', 'role': 'owner', 'emailAddress': 'bixente.barnetche@gmail.com'}, transferOwnership=True, supportsAllDrives=True).execute()
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
j1_select = c1.selectbox("Joueur 1", liste_joueurs)
j2_select = c2.selectbox("Joueur 2", liste_joueurs)

st.divider()

scores_j1, scores_j2 = [], []
sets_j1, sets_j2 = 0, 0

st.write("### 📝 Scores des Sets")
for i in range(1, 6):
    col1, col2, col3 = st.columns([1, 1, 1])
    s1 = col1.number_input(f"Set {i} - J1", min_value=0, step=1, key=f"s1_{i}")
    s2 = col2.number_input(f"Set {i} - J2", min_value=0, step=1, key=f"s2_{i}")
    
    if (s1 >= 11 or s2 >= 11) and abs(s1 - s2) >= 2:
        col3.success("✅ Valide")
        scores_j1.append(s1)
        scores_j2.append(s2)
        if s1 > s2: sets_j1 += 1
        else: sets_j2 += 1
    elif s1 > 0 or s2 > 0:
        col3.warning("En cours...")

st.divider()
uploaded_photo = st.file_uploader("📸 Photo de la feuille (Optionnel)", type=['jpg', 'png', 'jpeg'])
st.divider()

# --- VALIDATION ET ENVOI ---
if sets_j1 == 3 or sets_j2 == 3:
    st.balloons() # Juste pour le plaisir visuel avant l'envoi
    st.success(f"Résultat final : {sets_j1} - {sets_j2}")
    
    if st.button("🚀 ENVOYER AU SHEETS"):
        try:
            with st.spinner('Enregistrement en cours...'):
                photo_link = upload_to_drive(uploaded_photo, f"{j1_select}_{j2_select}.jpg")
                match_trouve = False
                
                for j in range(1, 10):
                    ws = spreadsheet.worksheet(f"J{j}")
                    data = ws.get_all_values()
                    for idx, row in enumerate(data):
                        n1, n2 = j1_select.split(" ")[0].upper(), j2_select.split(" ")[0].upper()
                        if n1 in row[1].upper() or n2 in row[1].upper():
                            v_idx = idx + 1 if idx + 1
