"""
Script à lancer UNE SEULE FOIS pour initialiser les points
des clients qui ont déjà des réservations confirmées.

Lance: python manage.py shell < init_points.py
"""
from rentals.models import Client, Reservation

updated = 0
for client in Client.objects.all():
    nb_confirmees = Reservation.objects.filter(
        client=client,
        statut__in=['confirmée', 'confirmee', 'terminée', 'terminee']
    ).count()
    
    if nb_confirmees > 0 and client.points_gagnes == 0:
        client.points_gagnes = nb_confirmees * 100
        client.save(update_fields=['points_gagnes'])
        print(f'✅ {client.prenom} {client.nom} → {client.points_gagnes} pts ({nb_confirmees} résa)')
        updated += 1

print(f'\n✅ {updated} clients mis à jour.')