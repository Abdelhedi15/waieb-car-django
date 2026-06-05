import psycopg2
conn = psycopg2.connect('postgresql://postgres:TTNEZNUOBAocivPNQaAiBSFMEHIMCnsy@gondola.proxy.rlwy.net:58090/railway')
cur = conn.cursor()
cur.execute("UPDATE vehicles_vehicle SET date_acquisition = '2021-01-01' WHERE immatriculation = '264TN2008'")
print('Skoda Octavia:', cur.rowcount)
cur.execute("UPDATE vehicles_vehicle SET date_acquisition = '2021-03-01' WHERE immatriculation = '266TN2210'")
print('Renault Talisman:', cur.rowcount)
conn.commit()
cur.execute("""
    SELECT marque, modele, immatriculation, date_acquisition,
           ROUND((CURRENT_DATE - date_acquisition) / 365.25, 1) AS duree_ans
    FROM vehicles_vehicle
    WHERE immatriculation IN ('264TN2008', '266TN2210')
""")
for r in cur.fetchall():
    print(f'  {r[0]} {r[1]} | {r[2]} | acquisition={r[3]} | {r[4]} ans en flotte')
conn.close()
