#!/usr/bin/env python3

import sqlite3

def sqlite_to_gedcom(db_path, output_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(output_path, 'w', encoding='utf-8') as f:
        # 1. Header minimal
        f.write("0 HEAD\n1 CHAR UTF-8\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n")

        # 2. Export des Individus
        cursor.execute("SELECT * FROM individus")
        for row in cursor.fetchall():
            idx, nom, prenom, sexe, d_naiss, l_naiss, d_dec, l_dec, notes, urls, photos = row
            f.write(f"0 @{idx}@ INDI\n")
            if nom or prenom:
                f.write(f"1 NAME {prenom} /{nom}/\n")
            if sexe: f.write(f"1 SEX {sexe}\n")
            if d_naiss or l_naiss:
                f.write("1 BIRT\n")
                if d_naiss: f.write(f"2 DATE {d_naiss}\n")
                if l_naiss: f.write(f"2 PLAC {l_naiss}\n")
            if d_dec or l_dec:
                f.write("1 DEAT\n")
                if d_dec: f.write(f"2 DATE {d_dec}\n")
                if l_dec: f.write(f"2 PLAC {l_dec}\n")

            # --- AJOUT DES LIENS FAMILIAUX DANS INDI ---
            # 1. Est-il un enfant de quelqu'un ? (FAMC)
            cursor.execute("SELECT id_union FROM enfants WHERE id_enfant=?", (idx,))
            famc = cursor.fetchone()
            if famc:
                f.write(f"1 FAMC @{famc[0]}@\n")

            # 2. Est-il parent dans une ou plusieurs familles ? (FAMS)
            cursor.execute("SELECT id FROM unions WHERE id_pere=? OR id_mere=?", (idx, idx))
            for (fams_id,) in cursor.fetchall():
                f.write(f"1 FAMS @{fams_id}@\n")
            
            # Gestion des champs multiples (virgules -> tags multiples)
            if notes:
                for n in notes.split('\n'): f.write(f"1 NOTE {n}\n")
            if urls:
                for url in urls.split(','): f.write(f"1 WWW {url}\n")
            if photos:
                for img in photos.split(','):
                    f.write(f"1 OBJE\n2 FILE {img}\n2 FORM jpg\n")

        # 3. Export des Unions
        cursor.execute("SELECT * FROM unions")
        for row in cursor.fetchall():
            u_id, pere, mere, d_marr, l_marr, div, d_div = row
            f.write(f"0 @{u_id}@ FAM\n")
            if pere: f.write(f"1 HUSB @{pere}@\n")
            if mere: f.write(f"1 WIFE @{mere}@\n")
            
            # Récupération des enfants rattachés
            cursor.execute("SELECT id_enfant FROM enfants WHERE id_union=?", (u_id,))
            for (child_id,) in cursor.fetchall():
                f.write(f"1 CHIL @{child_id}@\n")
            
            if d_marr or l_marr:
                f.write("1 MARR\n")
                if d_marr: f.write(f"2 DATE {d_marr}\n")
                if l_marr: f.write(f"2 PLAC {l_marr}\n")
            
            if div == 'T':
                f.write("1 DIV\n")
                if d_div: f.write(f"2 DATE {d_div}\n")

        f.write("0 TRLR")

    conn.close()
    print(f"Fichier recréé : {output_path}")

sqlite_to_gedcom('genealogie.db', 'test_reconstruit.ged')