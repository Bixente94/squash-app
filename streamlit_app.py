import streamlit as st 
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

# --- SETUP ---
st.set_page_config(page_title="Squash Manager", page_icon="🎾")

try:
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    SHEET_ID = "1VxmG8Pw0-zmnox6EwYWO74mL4Wk71MQTC9D4ajPhvNA"
    DRIVE_ID = "1BTNIJpsZz_ndUlHzd8ikaASoFN5-VUD3"
    ss = client.open_by_key(SHEET_ID)
except Exception as e:
    st.error(f"Erreur connexion : {e}"); st.stop()

# --- UTILS ---
def flash(color):
    c = "#2ecc71" if color == "green" else "#e74c3c"
    html = f'<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;background-color:{c};opacity:0.4;z-index:9999;pointer-events:none;animation:f 0.6s ease-out forwards;"></div><style>@keyframes f{{0%{{opacity:0.4;}}100%{{opacity:0;}}}}</style>'
    st.components.v1.html(html, height=0)

def up_drive(file, name):
    if not file: return ""
    try:
        svc = build('drive', 'v3', credentials=creds)
        # On définit les métadonnées : le fichier appartient au dossier parent
        meta = {
            'name': name, 
            'parents': [DRIVE_ID]
        }
        m = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype='image/jpeg')
        
        # Création du fichier SANS transfert de propriété
        res = svc.files().create(
            body=meta, 
            media_body=m, 
            fields='id, webViewLink',
            supportsAllDrives=True # Très important
        ).execute()
        
        fid = res.get('id')
        
        # On rend juste le lien lisible pour que tu puisses cliquer dessus dans le Sheets
        svc.permissions().create(
            fileId=fid, 
            body={'type': 'anyone', 'role': 'viewer'},
            supportsAllDrives=True
        ).execute()
        
        return res.get('webViewLink')
    except Exception as e:
        st.error(f"Erreur Drive détaillée : {e}")
        return ""

# --- APP ---
st.title("🏆 Scores Squash")
ws_c = ss.worksheet("COORDONNEES")
joueurs = [f"{r[0]} {r[1]}" for r in ws_c.get_all_values()[2:] if r[0]]

c1, c2 = st.columns(2)
j1 = c1.selectbox("Joueur 1", joueurs)
j2 = c2.selectbox("Joueur 2", joueurs)

st.divider()
sc1, sc2, s1_w, s2_w = [], [], 0, 0

st.write("### 📝 Saisie des Sets")
h1, h2, h3 = st.columns([2, 2, 1])
h1.caption(f"Score {j1.split(' ')[0]}")
h2.caption(f"Score {j2.split(' ')[0]}")
h3.caption("État")

for i in range(1, 6):
    l1, l2, l3 = st.columns([2, 2, 1])
    v1 = l1.number_input(f"Set {i}", 0, 30, 0, key=f"v1_{i}", label_visibility="collapsed")
    v2 = l2.number_input(f"Set {i} bis", 0, 30, 0, key=f"v2_{i}", label_visibility="collapsed")
    
    diff = abs(v1 - v2)
    valid_set = False
    if (v1 == 11 or v2 == 11) and diff >= 2: valid_set = True
    elif (v1 > 11 or v2 > 11) and diff == 2: valid_set = True
        
    if valid_set:
        l3.markdown("### ✅")
        sc1.append(v1); sc2.append(v2)
        if v1 > v2: s1_w += 1
        else: s2_w += 1
    elif v1 > 0 or v2 > 0: l3.markdown("### ⏳")

st.divider()
img = st.file_uploader("📸 Photo de la feuille de match (Optionnel)", type=['jpg', 'png', 'jpeg'])

if s1_w == 3 or s2_w == 3:
    st.write("#### 🔍 Récapitulatif")
    recap_dict = {"Set": [f"Set {k+1}" for k in range(len(sc1))], j1: sc1, j2: sc2}
    st.table(recap_dict)
    
    win = j1 if s1_w == 3 else j2
    st.success(f"🏆 Victoire de **{win}** par **{max(s1_w, s2_w)}** sets à **{min(s1_w, s2_w)}**")

    if st.button("🚀 ENVOYER LE SCORE FINAL"):
        try:
            with st.spinner('Envoi vers Google Sheets...'):
                link = up_drive(img, f"{datetime.now().strftime('%Y%m%d')}_{j1}_{j2}.jpg")
                found = False
                n1, n2 = j1.split(" ")[0].upper(), j2.split(" ")[0].upper()
                
                for j in range(1, 10):
                    ws = ss.worksheet(f"J{j}")
                    data = ws.get_all_values()
                    for idx, row in enumerate(data):
                        if n1 in row[1].upper() or n2 in row[1].upper():
                            v_idx = idx + 1 if (idx % 2 != 0) else idx - 1
                            if v_idx < 0 or v_idx >= len(data): continue
                            if n1 in data[v_idx][1].upper() or n2 in data[v_idx][1].upper():
                                if row[3].strip() not in ["", "0"]:
                                    flash("red"); st.error("❌ Déjà rempli !"); st.stop()
                                
                                found = True
                                sa, sv = (sc1, sc2) if n1 in row[1].upper() else (sc2, sc1)
                                
                                for k in range(len(sc1)):
                                    ws.update_cell(idx+1, 4+k, sa[k])
                                    ws.update_cell(v_idx+1, 4+k, sv[k])
                                
                                if link:
                                    ws.update_cell(idx + 1, 16, link)
                                    ws.update_cell(v_idx + 1, 16, link)
                                
                                flash("green"); st.success("✅ Match enregistré !"); break
                    if found: break
                if not found: st.error("Match non trouvé dans le calendrier.")
        except Exception as e: st.error(f"Erreur : {e}")
else:
    st.info("ℹ️ Complétez 3 sets gagnants pour débloquer l'envoi.")
