import psycopg2
conn = psycopg2.connect('postgresql://postgres:TTNEZNUOBAocivPNQaAiBSFMEHIMCnsy@gondola.proxy.rlwy.net:58090/railway')
cur = conn.cursor()
cur.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('vehicles', '0004_alter_vehicle_statut', NOW()) ON CONFLICT DO NOTHING")
conn.commit()
print('Migration faked!')
cur.execute("SELECT name FROM django_migrations WHERE app='vehicles' ORDER BY applied")
for r in cur.fetchall(): print(' ', r[0])
conn.close()
