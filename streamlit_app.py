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

# --- FONCTIONS DRIVE ---
def upload_to_drive(file, filename):
    service = build('drive', 'v3', credentials=creds)
    file_metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
    media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype='image/jpeg')
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True).execute()
    return uploaded_file.get('webViewLink')

# --- FONCTIONS SHEETS ---
def get_liste_joueurs():
    ws = spreadsheet.worksheet("COORDONNEES")
    data = ws.get_all_values()[2:] 
    return [f"{row[0]} {row[1]}" for row in data if row[0]]

def verifier_jeu(s1, s2):
    if s1 == 0 and s2 == 0: return False, "En attente"
    if s1 < 11 and s2 < 11: return False, "Score < 11"
    diff = abs(s1 - s2)
    if (s1 == 11 or s2 == 11) and diff >= 2: return True, "OK"
    if (s1 > 11 or s2 > 11) and diff == 2: return True, "OK"
    return False, "Écart de 2 requis"

# --- INTERFACE ---
st.set_page_config(page_title="Squash Manager", page_icon="🎾")
st.title("🏆 Enregistrement des Scores")

liste_joueurs = get_liste_joueurs()
col1, col2 = st.columns(2)
j1_select = col1.selectbox("Joueur 1", liste_joueurs)
j2_select = col2.selectbox("Joueur 2", liste_joueurs)

st.divider()

scores_j1, scores_j2, sets_j1 = [], [], 0

st.write("### Détails des Jeux")
for i in range(1, 6):
    c1, c2, c3 = st.columns([1, 1, 2])
    s1 = c1.number_input(f"Set {i} - {j1_select}", min_value=0, step=1, key=f"s1_{i}")
    s2 = c2.number_input(f"Set {i} - {j2_select}", min_value=0, step=1, key=f"s2_{i}")
    
    valide, msg = verifier_jeu(s1, s2)
    if valide:
        c3.success("Jeu valide")
        scores_j1.append(s1); scores_j2.append(s2)
        if s1 > s2: sets_j1 += 1
    elif s1 > 0 or s2 > 0:
        c3.error(msg)

st.divider()
uploaded_photo = st.file_uploader("📸 Photo de la feuille de match (Optionnel)", type=['jpg', 'jpeg', 'png'])
st.divider()

# CALCULS (CORRIGÉS)
jeux_j1 = sets_j1
jeux_j2 = sum(1 for i in range(len(scores_j1)) if scores_j2[i] > scores_j1[i])

if (jeux_j1 == 3 or jeux_j2 == 3):
    vrai_vainqueur = j1_select if jeux_j1 == 3 else j2_select
    st.write("### 🔍 Vérification des scores")
    recap = {"Set": [f"Set {i+1}" for i in range(len(scores_j1))], j1_select: scores_j1, j2_select: scores_j2}
    st.table(recap)
    st.info(f"Résultat final : **{jeux_j1} - {jeux_j2}** pour **{vrai_vainqueur}**")

    if st.button("Confirmer et envoyer les scores"):
        try:
            match_trouve = False
            with st.spinner('Envoi en cours...'):
                link_photo = upload_to_drive(uploaded_photo, f"{j1_select}_{j2_select}.jpg") if uploaded_photo else ""

                for i in range(1, 10):
                    ws = spreadsheet.worksheet(f"J{i}")
                    all_cells = ws.get_all_values()
                    for idx, row in enumerate(all_cells):
                        n1, n2 = j1_select.split(" ")[0].upper(), j2_select.split(" ")[0].upper()
                        if n1 in row[1].upper() or n2 in row[1].upper():
                            v_idx = idx + 1 if idx + 1 < len(all_cells) else idx - 1
                            if n1 in all_cells[v_idx][1].upper() or n2 in all_cells[v_idx][1].upper():
                                match_trouve = True
                                if row[3].strip() not in ["", "0"]:
                                    flash_screen("red")
                                    st.error("❌ Score déjà présent.")
                                    st.stop()
                                
                                s_actu, s_voisin = (scores_j1, scores_j2) if n1 in row[1].upper() else (scores_j2, scores_j1)
                                for g_idx in range(len(scores_j1)):
                                    ws.update_cell(idx + 1, 4 + g_idx, s_actu[g_idx])
                                    ws.update_cell(v_idx + 1, 4 + g_idx, s_voisin[g_idx])
                                if link_photo:
                                    ws.update_cell(idx + 1, 16, link_photo)
                                    ws.update_cell(v_idx + 1, 16, link_photo)
                                
                                flash_screen("green")
                                st.success(f"✅ Enregistré dans J{i} !")
                                break
                    if match_trouve: break
            if not match_trouve:
                flash_screen("red")
                st.error("Match non trouvé.")
        except Exception as e:
            flash_screen("red")
            st.error(f"Erreur : {e}")
else:
    st.info("Saisissez 3 sets gagnants pour envoyer.")
