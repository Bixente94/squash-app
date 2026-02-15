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

# 1. Sélection des Joueurs (plus besoin de choisir la journée !)
liste_joueurs = get_liste_joueurs()
col1, col2 = st.columns(2)
j1_select = col1.selectbox("Joueur 1", liste_joueurs)
j2_select = col2.selectbox("Joueur 2", liste_joueurs)

st.divider()

# (garder la partie saisie des scores et calcul des jeux_j1 / jeux_j2)

if (jeux_j1 == 3 or jeux_j2 == 3):
    vrai_vainqueur = j1_select if jeux_j1 == 3 else j2_select
    st.balloons()
    
    st.write("### 🔍 Vérification des scores")
    recap_data = {
        "Set": [f"Set {i+1}" for i in range(len(scores_j1))],
        j1_select: scores_j1,
        j2_select: scores_j2
    }
    st.table(recap_data)

    if st.button("Confirmer et envoyer les scores"):
        try:
            match_trouve = False
            # On cherche dans tous les onglets de J1 à J9
            for i in range(1, 10):
                nom_onglet = f"J{i}"
                ws = spreadsheet.worksheet(nom_onglet)
                all_cells = ws.get_all_values()
                
                for idx, row in enumerate(all_cells):
                    nom_j1 = j1_select.split(" ")[0].upper()
                    nom_j2 = j2_select.split(" ")[0].upper()
                    
                    if nom_j1 in row[1].upper() or nom_j2 in row[1].upper():
                        voisin_index = idx + 1 if idx + 1 < len(all_cells) else idx - 1
                        nom_voisin = all_cells[voisin_index][1].upper()
                        
                        if nom_j1 in nom_voisin or nom_j2 in nom_voisin:
                            # ON A TROUVÉ LE MATCH !
                            # --- Vérification si déjà rempli ---
                            # On regarde si la case du Set 1 (Colonne D / index 3) est vide ou égale à 0
                            if row[3] and row[3] != "0" and row[3] != "":
                                st.warning(f"⚠️ Ce match dans l'onglet {nom_onglet} semble déjà avoir un score ({row[3]}).")
                                if not st.checkbox("Écraser le score existant ?"):
                                    match_trouve = True
                                    break

                            # --- Remplissage ---
                            if nom_j1 in row[1].upper():
                                sc_ligne_actuelle, sc_ligne_voisine = scores_j1, scores_j2
                            else:
                                sc_ligne_actuelle, sc_ligne_voisine = scores_j2, scores_j1
                                
                            for g_idx in range(len(scores_j1)):
                                ws.update_cell(idx + 1, 4 + g_idx, sc_ligne_actuelle[g_idx])
                                ws.update_cell(voisin_index + 1, 4 + g_idx, sc_ligne_voisine[g_idx])
                            
                            st.success(f"✅ Match trouvé et enregistré dans l'onglet **{nom_onglet}** !")
                            match_trouve = True
                            break
                if match_trouve: break # Sortir de la boucle des onglets J1-J9

            if not match_trouve:
                st.error("Impossible de trouver ce match dans les journées J1 à J9.")
        except Exception as e:
            st.error(f"Erreur technique : {e}")

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
jeux_j1 = sets_j1
jeux_j2 = sum(1 for i in range(len(scores_j1)) if scores_j2[i] > scores_j1[i])

if (jeux_j1 == 3 or jeux_j2 == 3):
    vrai_vainqueur = j1_select if jeux_j1 == 3 else j2_select
    st.balloons()
    
    # --- TABLEAU RÉCAPITULATIF ---
    st.write("### 🔍 Vérification des scores")
    recap_data = {
        "Set": [f"Set {i+1}" for i in range(len(scores_j1))],
        j1_select: scores_j1,
        j2_select: scores_j2
    }
    st.table(recap_data)
    st.info(f"Résultat final : **{jeux_j1} - {jeux_j2}** pour **{vrai_vainqueur}**")
    # ------------------------------

    if st.button("Confirmer et envoyer les scores"):
        try:
            ws = spreadsheet.worksheet(journee)
            all_cells = ws.get_all_values()
            trouve = False
            
            for idx, row in enumerate(all_cells):
                nom_j1 = j1_select.split(" ")[0].upper()
                nom_j2 = j2_select.split(" ")[0].upper()
                
                if nom_j1 in row[1].upper() or nom_j2 in row[1].upper():
                    voisin_index = idx + 1 if idx + 1 < len(all_cells) else idx - 1
                    nom_voisin = all_cells[voisin_index][1].upper()
                    
                    if nom_j1 in nom_voisin or nom_j2 in nom_voisin:
                        if nom_j1 in row[1].upper():
                            sc_ligne_actuelle, sc_ligne_voisine = scores_j1, scores_j2
                        else:
                            sc_ligne_actuelle, sc_ligne_voisine = scores_j2, scores_j1
                            
                        for g_idx in range(len(scores_j1)):
                            ws.update_cell(idx + 1, 4 + g_idx, sc_ligne_actuelle[g_idx])
                            ws.update_cell(voisin_index + 1, 4 + g_idx, sc_ligne_voisine[g_idx])
                        
                        trouve = True
                        st.success("✅ Scores enregistrés ! Ton classement sera mis à jour automatiquement.")
                        break
            
            if not trouve:
                st.error("Match non trouvé dans cette journée. Vérifie les adversaires.")
        except Exception as e:
            st.error(f"Erreur technique : {e}")
else:
    st.info("Le bouton d'envoi apparaîtra une fois les 3 jeux gagnants saisis.")
