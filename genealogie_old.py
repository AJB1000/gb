#!/usr/bin/env python3

import csv
from datetime import datetime

# === CONFIGURATION GITHUB (A REMPLIR) ===
GITHUB_USER = "AJB1000"
GITHUB_REPO = "gb"
# L'URL de base pour les images "raw" sur GitHub Pages (branche main par défaut)
BASE_PHOTO_URL = f"https://raw.githubusercontent.com/AJB1000/gb/main/photos/"

def format_gedcom_date(date_str):
    if not date_str or "/" not in str(date_str): return date_str
    months_en = {1:"JAN", 2:"FEB", 3:"MAR", 4:"APR", 5:"MAY", 6:"JUN",
                 7:"JUL", 8:"AUG", 9:"SEP", 10:"OCT", 11:"NOV", 12:"DEC"}
    try:
        d = datetime.strptime(date_str.strip(), "%d/%m/%Y")
        return f"{d.day} {months_en[d.month]} {d.year}"
    except: return date_str

def create_gedcom(csv_file, gedcom_file):
    with open(csv_file, mode='r', encoding='utf-8') as f:
        data = list(csv.DictReader(f))

    with open(gedcom_file, mode='w', encoding='utf-8') as f:
        f.write("0 HEAD\n1 CHAR UTF-8\n1 GEDC\nVERS 5.5.1\n")
        
        # 1. INDIVIDUS (Avec ajout des photos)
        for row in data:
            indi_id = row['ID'].strip()
            if not indi_id: continue
            
            f.write(f"0 @I{indi_id}@ INDI\n")
            f.write(f"1 NAME {row.get('Prenom','')} /{row.get('Nom','')}/\n")
            f.write(f"1 SEX {row.get('Sexe','U')}\n")
            
            # Naissance
            if row.get('Date_Nais') or row.get('Lieu_Nais'):
                f.write("1 BIRT\n")
                if row.get('Date_Nais'):
                    f.write(f"2 DATE {format_gedcom_date(row['Date_Nais'])}\n")
                if row.get('Lieu_Nais'):
                    f.write(f"2 PLAC {row['Lieu_Nais'].strip()}\n")

            # Mariage (Note: dans GEDCOM, les lieux de mariage vont dans la balise FAM, 
            # le script s'en occupe plus bas dans la section FAMILLES)

            # Photo (Chemin absolu comme vous avez testé)
            photo = row.get('Photo_URL')
            if photo and photo.strip():
                f.write("1 OBJE\n")
                f.write(f"2 FILE {photo.strip()}\n")
                f.write("2 FORM jpg\n")

        # 2. FAMILLES (Code inchangé)
        families = {}
        for row in data:
            p, m = row.get('ID_Pere'), row.get('ID_Mere')
            if p and m:
                fid = tuple(sorted([p, m]))
                if fid not in families: families[fid] = {'husb': p, 'wife': m, 'children': [], 'marr_d': None, 'marr_p': None}
                families[fid]['children'].append(row['ID'])
            conj = row.get('ID_Conjoint')
            if conj:
                fid = tuple(sorted([row['ID'], conj]))
                if fid not in families:
                    h, w = (row['ID'], conj) if row['Sexe'] == 'M' else (conj, row['ID'])
                    families[fid] = {'husb': h, 'wife': w, 'children': [], 
                                     'marr_d': row.get('Date_Mariage'), 'marr_p': row.get('Lieu_Mariage')}

        for idx, (ids, info) in enumerate(families.items()):
            f.write(f"0 @F{idx}@ FAM\n")
            f.write(f"1 HUSB @I{info['husb']}@\n")
            f.write(f"1 WIFE @I{info['wife']}@\n")
            if info['marr_d'] or info['marr_p']:
                f.write("1 MARR\n")
                if info['marr_d']: f.write(f"2 DATE {format_gedcom_date(info['marr_d'])}\n")
                if info['marr_p']: f.write(f"2 PLAC {info['marr_p']}\n")
            for child in info['children']:
                f.write(f"1 CHIL @I{child}@\n")
        f.write("0 TRLR\n")

create_gedcom('famille.csv', 'mon_arbre.ged')
print("GEDCOM généré avec succès (avec photos GitHub) !")


