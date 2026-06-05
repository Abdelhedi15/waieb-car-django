import psycopg2
conn = psycopg2.connect('postgresql://postgres:TTNEZNUOBAocivPNQaAiBSFMEHIMCnsy@gondola.proxy.rlwy.net:58090/railway')
cur = conn.cursor()
cur.execute("UPDATE vehicles_vehicle SET statut = 'a_vendre' WHERE immatriculation = '264TN2008'")
print('Updated:', cur.rowcount, 'rows')
conn.commit()
cur.execute("SELECT immatriculation, statut FROM vehicles_vehicle WHERE immatriculation = '264TN2008'")
print(cur.fetchone())
conn.close()
