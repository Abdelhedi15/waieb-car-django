import psycopg2

conn = psycopg2.connect('postgresql://postgres:TTNEZNUOBAocivPNQaAiBSFMEHIMCnsy@gondola.proxy.rlwy.net:58090/railway')
cur = conn.cursor()

# Reset ALL vehicles to NULL date_acquisition first
cur.execute("UPDATE vehicles_vehicle SET date_acquisition = NULL")
print(f"Reset all: {cur.rowcount} rows")

# Only set real dates for the 2 demo vehicles
cur.execute("UPDATE vehicles_vehicle SET date_acquisition = '2021-01-01' WHERE immatriculation = '264TN2008'")
print(f"Skoda Octavia: {cur.rowcount}")

cur.execute("UPDATE vehicles_vehicle SET date_acquisition = '2021-03-01' WHERE immatriculation = '266TN2210'")
print(f"Renault Talisman: {cur.rowcount}")

conn.commit()

# Verify
cur.execute("""
    SELECT immatriculation, marque, modele, date_acquisition,
           CASE WHEN date_acquisition IS NOT NULL 
                THEN ROUND((CURRENT_DATE - date_acquisition) / 365.25, 1)
                ELSE NULL END AS duree_ans
    FROM vehicles_vehicle
    WHERE date_acquisition IS NOT NULL
""")
print("\nVehicules avec date_acquisition:")
for r in cur.fetchall():
    print(f"  {r[1]} {r[2]} ({r[0]}) → {r[4]} ans")

cur.execute("SELECT COUNT(*) FROM vehicles_vehicle WHERE date_acquisition IS NULL")
print(f"\nVéhicules sans date_acquisition: {cur.fetchone()[0]}")

conn.close()
print("\n✅ Done!")