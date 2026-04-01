#!/usr/bin/env python3

import sqlite3

def sqlite_to_gedcom(db_path, output_path):
    conn = sqlite3.connect(db_path)
    # Permet d'accéder aux colonnes par nom : row['nom']
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    with open(output_path, 'w', encoding='utf-8') as f:
        # 1. Header (Indispensable pour Topola)
        f.write("0 HEAD\n1 CHAR UTF-8\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n")

        # 2. Export des Individus
        cursor.execute("SELECT * FROM individus")
        individus = cursor.fetchall()
        print(f"Export de {len(individus)} individus...")

        for row in individus:
            idx = row['id']
            f.write(f"0 @{idx}@ INDI\n")
            if row['prenom'] or row['nom']:
                f.write(f"1 NAME {row['prenom']} /{row['nom']}/\n")
            if row['sexe']: 
                f.write(f"1 SEX {row['sexe']}\n")
            
            # Événements Naissance
            if row['date_naissance'] or row['lieu_naissance']:
                f.write("1 BIRT\n")
                if row['date_naissance']: f.write(f"2 DATE {row['date_naissance']}\n")
                if row['lieu_naissance']: f.write(f"2 PLAC {row['lieu_naissance']}\n")
            
            # Événements Décès
            if row['date_deces'] or row['lieu_deces']:
                f.write("1 DEAT\n")
                if row['date_deces']: f.write(f"2 DATE {row['date_deces']}\n")
                if row['lieu_deces']: f.write(f"2 PLAC {row['lieu_deces']}\n")

            # --- LIENS FAMILIAUX (L'ANCRE DE TOPOLA) ---
            # Lien vers la famille où il est ENFANT
            cursor.execute("SELECT id_union FROM enfants WHERE id_enfant=?", (idx,))
            for (famc_id,) in cursor.fetchall():
                f.write(f"1 FAMC @{famc_id}@\n")

            # Lien vers les familles où il est CONJOINT/PARENT
            cursor.execute("SELECT id FROM unions WHERE id_pere=? OR id_mere=?", (idx, idx))
            for (fams_id,) in cursor.fetchall():
                f.write(f"1 FAMS @{fams_id}@\n")

            # Médias et Notes
            if row['notes']:
                for n in row['notes'].split('\n'): f.write(f"1 NOTE {n}\n")
            if row['liens_www']:
                for url in row['liens_www'].split(','): f.write(f"1 WWW {url.strip()}\n")
            if row['photos']:
                for img in row['photos'].split(','):
                    f.write(f"1 OBJE\n2 FILE {img.strip()}\n2 FORM jpg\n")

        # 3. Export des Unions (Familles)
        cursor.execute("SELECT * FROM unions")
        unions = cursor.fetchall()
        print(f"Export de {len(unions)} unions...")

        for row in unions:
            u_id = row['id']
            f.write(f"0 @{u_id}@ FAM\n")
            if row['id_pere']: f.write(f"1 HUSB @{row['id_pere']}@\n")
            if row['id_mere']: f.write(f"1 WIFE @{row['id_mere']}@\n")
            
            # Liste des enfants de cette famille
            cursor.execute("SELECT id_enfant FROM enfants WHERE id_union=?", (u_id,))
            for (child_id,) in cursor.fetchall():
                f.write(f"1 CHIL @{child_id}@\n")
            
            # Événements Mariage
            if row['date_mariage'] or row['lieu_mariage']:
                f.write("1 MARR\n")
                if row['date_mariage']: f.write(f"2 DATE {row['date_mariage']}\n")
                if row['lieu_mariage']: f.write(f"2 PLAC {row['lieu_mariage']}\n")
            
            # Divorce
            if row['divorce'] == 'T':
                f.write("1 DIV\n")
                if row['date_divorce']: f.write(f"2 DATE {row['date_divorce']}\n")

        f.write("0 TRLR")

    conn.close()
    print("Fichier reconstruit avec succès.")

sqlite_to_gedcom('genealogie.db', 'test_reconstruit.ged')