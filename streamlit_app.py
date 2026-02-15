import streamlit as st 
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONNEXION GOOGLE SHEETS ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
# On utilise les secrets de Streamlit pour la sécurité
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# Ouvre ton fichier (met le nom EXACT de ton Google Sheet ici)
NOM_DU_FICHIER = "Championnat interne Poule 1 Phase 2" 
spreadsheet = client.open_by_key("1VxmG8Pw0-zmnox6EwYWO74mL4Wk71MQTC9D4ajPhvNA")
# --- FONCTIONS UTILES ---
def get_liste_joueurs():
    ws = spreadsheet.worksheet("COORDONNEES")
    # On récupère Nom (Col A) et Prénom (Col B) à partir de la ligne 3
    data = ws.get_all_values()[2:] 
    return [f"{row[0]} {row[1]}" for row in data if row[0]]

def verifier_jeu(s1, s2):
    if s1 == 0 and s2 == 0: return False, "En attente"
    if s1 < 11 and s2 < 11: return False, "Score < 11"
    diff = abs(s1 - s2)
    if (s1 == 11 or s2 == 11) and diff >= 2: return True, "OK"
    if (s1 > 11 or s2 > 11) and diff == 2: return True, "OK"
    return False, "Écart de 2 requis"

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Squash Manager", page_icon="🎾")
st.title("🏆 Enregistrement des Scores")

# 1. Sélection Journée et Joueurs
liste_joueurs = get_liste_joueurs()
journee = st.selectbox("Sélectionnez la journée", [f"J{i}" for i in range(1, 10)])

col1, col2 = st.columns(2)
j1_select = col1.selectbox("Joueur 1 (Vainqueur)", liste_joueurs)
j2_select = col2.selectbox("Joueur 2 (Perdant)", liste_joueurs)

st.divider()

# 2. Saisie des scores
scores_j1 = []
scores_j2 = []
sets_j1 = 0

st.write("### Détails des Jeux")
for i in range(1, 6):
    c1, c2, c3 = st.columns([1, 1, 2])
    s1 = c1.number_input(f"J{i} - {j1_select}", min_value=0, step=1, key=f"s1_{i}")
    s2 = c2.number_input(f"J{i} - {j2_select}", min_value=0, step=1, key=f"s2_{i}")
    
    valide, msg = verifier_jeu(s1, s2)
    if valide:
        c3.success("Jeu valide")
        scores_j1.append(s1)
        scores_j2.append(s2)
        if s1 > s2: sets_j1 += 1
    elif s1 > 0 or s2 > 0:
        c3.error(msg)

# 3. Validation et Envoi
if sets_j1 == 3:
    st.balloons()
    if st.button("Confirmer et envoyer au Google Sheet"):
        try:
            ws = spreadsheet.worksheet(journee)
            all_cells = ws.get_all_values()
            trouve = False
            
            # On cherche le bloc des joueurs dans l'onglet Journée
            for idx, row in enumerate(all_cells):
                # On cherche le NOM (souvent en majuscules dans tes feuilles J1, J2)
                nom_j1_fiche = j1_select.split(" ")[0].upper()
                nom_j2_fiche = j2_select.split(" ")[0].upper()
                
                if nom_j1_fiche in row[1] or nom_j2_fiche in row[1]:
                    # On vérifie la ligne d'en dessous pour confirmer le match
                    if nom_j1_fiche in all_cells[idx+1][1] or nom_j2_fiche in all_cells[idx+1][1]:
                        
                        # Déterminer quelle ligne appartient à qui
                        row_top = idx + 1
                        row_bottom = idx + 2
                        idx_v = row_top if nom_j1_fiche in row[1] else row_bottom
                        idx_p = row_bottom if idx_v == row_top else row_top
                        
                        # Remplissage des colonnes D, E, F, G, H (colonnes 4 à 8)
                        for game_idx in range(len(scores_j1)):
                            ws.update_cell(idx_v, 4 + game_idx, scores_j1[game_idx])
                            ws.update_cell(idx_p, 4 + game_idx, scores_j2[game_idx])
                        
                        trouve = True
                        st.success(f"✅ Match {j1_select} vs {j2_select} enregistré avec succès dans {journee} !")
                        break
            
            if not trouve:
                st.error("Match non trouvé dans cette journée. Vérifiez les noms.")
        except Exception as e:
            st.error(f"Erreur : {e}")
else:
    st.info("Le bouton d'envoi apparaîtra une fois les 3 jeux gagnants saisis.")
