import psycopg2

conn = psycopg2.connect('postgresql://postgres:TTNEZNUOBAocivPNQaAiBSFMEHIMCnsy@gondola.proxy.rlwy.net:58090/railway')
cur = conn.cursor()

# 1. Ajouter la colonne
cur.execute('ALTER TABLE vehicles_vehicle ADD COLUMN IF NOT EXISTS date_acquisition DATE')
conn.commit()
print('✅ Colonne date_acquisition ajoutée')

# 2. Utiliser created_at comme date_acquisition pour tous les véhicules existants
# (fallback raisonnable — date d'ajout dans le système = date d'entrée en flotte)
cur.execute("""
    UPDATE vehicles_vehicle
    SET date_acquisition = created_at::date
    WHERE date_acquisition IS NULL
""")
print(f'✅ {cur.rowcount} véhicules mis à jour avec date_acquisition = created_at')
conn.commit()

# 3. Vérifier
cur.execute("""
    SELECT id, marque, modele, immatriculation, date_acquisition,
           ROUND((CURRENT_DATE - date_acquisition) / 365.25, 2) AS duree_ans
    FROM vehicles_vehicle
    ORDER BY date_acquisition
    LIMIT 10
""")
print('\nAperçu (10 premiers):')
for r in cur.fetchall():
    flag = '🔴' if r[5] and r[5] >= 3.5 else '✅'
    print(f'  {flag} {r[1]} {r[2]} | acquisition: {r[4]} | {r[5]} ans en flotte')

# 4. Combien dépassent 3.5 ans?
cur.execute("""
    SELECT COUNT(*) FROM vehicles_vehicle
    WHERE date_acquisition IS NOT NULL
    AND (CURRENT_DATE - date_acquisition) / 365.25 >= 3.5
""")
nb = cur.fetchone()[0]
print(f'\n🔴 Véhicules dépassant 3.5 ans en flotte: {nb}')

conn.close()