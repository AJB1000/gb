#!/usr/bin/env python3

import sqlite3
import re


def gedcom_to_sqlite(gedcom_path, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # # Création des tables (voir schéma ci-dessus)
    # cursor.executescript('''
    #     -- Table Individus
    #     CREATE TABLE individus (
    #         id TEXT PRIMARY KEY,
    #         nom TEXT,
    #         prenom TEXT,
    #         sexe TEXT,
    #         date_naissance TEXT,
    #         lieu_naissance TEXT,
    #         date_deces TEXT,
    #         lieu_deces TEXT,
    #         notes TEXT,
    #         liens_www TEXT, -- Stockés sous forme de chaîne "url1, url2"
    #         photos TEXT     -- Stockés sous forme de chaîne "img1.jpg, img2.jpg"
    #     );

    #     -- Table Unions
    #     CREATE TABLE unions (
    #         id TEXT PRIMARY KEY,
    #         id_pere TEXT,
    #         id_mere TEXT,
    #         date_mariage TEXT,
    #         lieu_mariage TEXT,
    #         divorce TEXT,   -- 'T' ou 'F'
    #         date_divorce TEXT
    #     );

    #     -- Table Enfants
    #     CREATE TABLE enfants (
    #         id_union TEXT,
    #         id_enfant TEXT
    #     );'''
    # )

    with open(gedcom_path, 'r', encoding='utf-8') as f:
        current_type = None  # 'INDI' or 'FAM'
        data = {}

        for line in f:
            line = line.strip()
            if not line: continue
            
            # Détection des nouveaux blocs
            # Format: 0 @I1@ INDI ou 0 @F1@ FAM
            match_start = re.match(r'0 @(\w+)@ (INDI|FAM)', line)
            
            if match_start:
                # Sauvegarder le bloc précédent avant d'en commencer un nouveau
                save_previous_block(cursor, current_type, data)
                
                # Reset pour le nouveau bloc
                current_id, current_type = match_start.groups()
                data = {'id': current_id, 'notes': [], 'urls': [], 'photos': []}
                continue

            if current_type == 'INDI':
                if '1 NAME' in line:
                    name_parts = re.search(r'1 NAME (.*) /(.*)/', line)
                    if name_parts:
                        data['prenom'], data['nom'] = name_parts.groups()
                elif '1 SEX' in line: data['sexe'] = line.split(' ')[2]
                elif '1 BIRT' in line: sub_tag = 'BIRT'
                elif '1 DEAT' in line: sub_tag = 'DEAT'
                elif '2 DATE' in line: data[f'date_{sub_tag}'] = line[7:]
                elif '2 PLAC' in line: data[f'lieu_{sub_tag}'] = line[7:]
                elif '1 NOTE' in line: data['notes'].append(line[7:])
                elif '1 WWW' in line: data['urls'].append(line[6:])
                elif '1 OBJE' in line: pass # Début bloc photo
                elif '2 FILE' in line: data['photos'].append(line[7:])

            elif current_type == 'FAM':
                # Utilisation d'un regex plus large [^@]+
                match_id = re.search(r'@([^@]+)@', line)
                
                if match_id:
                    extracted_id = match_id.group(1)
                    if '1 HUSB' in line: 
                        data['pere'] = extracted_id
                    elif '1 WIFE' in line: 
                        data['mere'] = extracted_id
                    elif '1 CHIL' in line: 
                        cursor.execute('INSERT INTO enfants (id_union, id_enfant) VALUES (?, ?)', 
                                     (data['id'], extracted_id))
                elif '1 MARR' in line: sub_tag = 'MARR'
                elif '1 DIV' in line: 
                    data['divorce'] = 'T'
                    sub_tag = 'DIV'
                elif '2 DATE' in line: data[f'date_{sub_tag}'] = line[7:]

    conn.commit()
    conn.close()

def save_previous_block(cursor, type, data):
    if not data: return
    if type == 'INDI':
        cursor.execute('''INSERT OR REPLACE INTO individus VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (data.get('id'), data.get('nom'), data.get('prenom'), data.get('sexe'),
             data.get('date_BIRT'), data.get('lieu_BIRT'), data.get('date_DEAT'), data.get('lieu_DEAT'),
             "\n".join(data['notes']), ",".join(data['urls']), ",".join(data['photos'])))
    elif type == 'FAM':
        cursor.execute('''INSERT OR REPLACE INTO unions VALUES (?,?,?,?,?,?,?)''',
            (data.get('id'), data.get('pere'), data.get('mere'), data.get('date_MARR'), 
             data.get('lieu_MARR'), data.get('divorce', 'F'), data.get('date_DIV')))

gedcom_to_sqlite('test.ged', 'genealogie.db')