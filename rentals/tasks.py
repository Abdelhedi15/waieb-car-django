# rentals/tasks.py
# ─────────────────────────────────────────────────────────────
# Tâches planifiées pour Waieb Car Rent
# Appel depuis Railway cron ou commande manage.py
# ─────────────────────────────────────────────────────────────

import threading
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def _send_email_mailjet(to_email, to_name, subject, body_html, body_text):
    """Envoie un email via Mailjet dans un thread séparé."""
    def _run():
        try:
            from mailjet_rest import Client as MJClient
            mj = MJClient(
                auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY),
                version='v3.1'
            )
            data = {
                'Messages': [{
                    'From': {
                        'Email': settings.MAILJET_FROM_EMAIL,
                        'Name':  settings.MAILJET_FROM_NAME,
                    },
                    'To': [{'Email': to_email, 'Name': to_name}],
                    'Subject': subject,
                    'HTMLPart': body_html,
                    'TextPart': body_text,
                }]
            }
            result = mj.send.create(data=data)
            print(f'[mailjet] {to_email} → status={result.status_code}')
        except Exception as e:
            print(f'[mailjet] ERREUR: {e}')
    threading.Thread(target=_run, daemon=True).start()


def _get_montant_restant(reservation):
    """Calcule le montant encore dû pour une réservation."""
    try:
        from payments.models import Paiement, Avance
        total_paiements = sum(
            float(p.montant)
            for p in Paiement.objects.filter(reservation=reservation)
        )
        total_avances = sum(
            float(a.montant_total)
            for a in Avance.objects.filter(reservation=reservation)
        )
        acompte    = float(reservation.acompte or 0)
        total_paye = total_paiements + total_avances + acompte
        return max(0, float(reservation.montant_total or 0) - total_paye)
    except Exception as e:
        print(f'[montant_restant] erreur: {e}')
        return max(0, float(reservation.montant_total or 0) - float(reservation.acompte or 0))


# ══════════════════════════════════════════════════════════════
# TÂCHE 1 — Alerte J-1 : email si montant restant > 0
# ══════════════════════════════════════════════════════════════
def alerte_j1_paiements():
    """
    À appeler chaque jour (ex: 08h00).
    Envoie un email de rappel aux clients dont la réservation
    se termine DEMAIN et qui ont encore un montant impayé.
    """
    from rentals.models import Reservation

    today    = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    reservations_j1 = Reservation.objects.filter(
        statut__in=['confirmee', 'confirmée', 'en_attente'],
        date_fin=tomorrow,
    ).select_related('client', 'vehicle')

    if not reservations_j1.exists():
        print(f'[J-1 Alert] Aucune réservation concernée pour {tomorrow}')
        return {'emails_envoyes': 0}

    emails_envoyes = 0

    for reservation in reservations_j1:
        try:
            montant_restant = _get_montant_restant(reservation)
            if montant_restant <= 0:
                continue  # déjà soldée, pas d'email

            client = reservation.client
            email = client.email
            if not email:
                try:
                    email = client.user.email
                except Exception:
                    pass
            if not email:
                print(f'[J-1 Alert] Pas d\'email pour client #{client.id}')
                continue

            nom_client = f'{client.prenom} {client.nom}'
            vehicule   = reservation.vehicle

            # ── Email HTML ───────────────────────────────────────
            body_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px;
                        margin: 0 auto; padding: 20px;">
                <div style="background: #1B3A6B; padding: 20px;
                            border-radius: 8px 8px 0 0; text-align: center;">
                    <h1 style="color: #E8A020; margin: 0; font-size: 24px;">
                        ⚠️ Rappel de paiement
                    </h1>
                    <p style="color: #CADCFC; margin: 5px 0;">
                        Waieb Car Rent
                    </p>
                </div>

                <div style="background: #F8FAFF; padding: 25px;
                            border: 1px solid #DDE3ED;">
                    <p style="font-size: 16px; color: #1A2535;">
                        Bonjour <strong>{nom_client}</strong>,
                    </p>
                    <p style="color: #1A2535;">
                        Votre location du véhicule
                        <strong>{vehicule.marque} {vehicule.modele}</strong>
                        se termine <strong>demain le {tomorrow}</strong>.
                    </p>

                    <div style="background: #FEF9EE; border: 2px solid #E8A020;
                                border-radius: 8px; padding: 20px;
                                margin: 20px 0; text-align: center;">
                        <p style="margin: 0; color: #1A2535; font-size: 14px;">
                            💳 Montant restant à régler
                        </p>
                        <p style="margin: 8px 0 0 0; font-size: 32px;
                                  font-weight: bold; color: #E8A020;">
                            {montant_restant:.2f} DT
                        </p>
                    </div>

                    <p style="color: #1A2535;">
                        Merci de régulariser ce montant lors de la
                        restitution du véhicule.
                    </p>

                    <div style="background: #EFF4FB; border-radius: 8px;
                                padding: 15px; margin-top: 15px;">
                        <p style="margin: 0; font-size: 14px; color: #64748B;">
                            📋 Réservation : <strong>#{reservation.id}</strong><br>
                            🚗 Véhicule : <strong>{vehicule.marque} {vehicule.modele}
                            ({vehicule.immatriculation})</strong><br>
                            📅 Période : <strong>{reservation.date_debut}
                            → {reservation.date_fin}</strong>
                        </p>
                    </div>
                </div>

                <div style="background: #1B3A6B; padding: 15px;
                            border-radius: 0 0 8px 8px; text-align: center;">
                    <p style="color: #AABDDB; margin: 0; font-size: 12px;">
                        Waieb Car Rent — MTD Group Sfax<br>
                        contact@mtd-group.biz — (+216) 74 490 291
                    </p>
                </div>
            </div>
            """

            # ── Email texte brut ─────────────────────────────────
            body_text = (
                f"Bonjour {nom_client},\n\n"
                f"Votre location du vehicule {vehicule.marque} {vehicule.modele} "
                f"se termine DEMAIN le {tomorrow}.\n\n"
                f"Montant restant a regler : {montant_restant:.2f} DT\n\n"
                f"Reservation #{reservation.id}\n"
                f"Periode : {reservation.date_debut} -> {reservation.date_fin}\n\n"
                f"Merci de regler ce montant lors de la restitution.\n\n"
                f"Cordialement,\nWaieb Car Rent"
            )

            _send_email_mailjet(
                email, nom_client,
                f'⚠️ Rappel paiement — Votre location se termine demain',
                body_html,
                body_text,
            )

            emails_envoyes += 1
            print(
                f'[J-1 Alert] ✅ Email → {email} | '
                f'Réservation #{reservation.id} | '
                f'Restant: {montant_restant:.2f} DT'
            )

        except Exception as e:
            print(f'[J-1 Alert] ❌ Erreur réservation #{reservation.id}: {e}')

    print(f'[J-1 Alert] Terminé: {emails_envoyes}/{reservations_j1.count()} emails envoyés')
    return {'emails_envoyes': emails_envoyes, 'date': str(tomorrow)}


# ══════════════════════════════════════════════════════════════
# TÂCHE 2 — Sync statuts véhicules (facultatif, appel quotidien)
# ══════════════════════════════════════════════════════════════
def sync_statuts_vehicules():
    """
    Remet en 'disponible' les véhicules marqués 'loue'
    sans réservation active aujourd'hui.
    """
    from vehicles.models import Vehicle
    from rentals.models import Reservation

    today = timezone.now().date()
    liberes = []

    for vehicle in Vehicle.objects.filter(statut='loue'):
        active = Reservation.objects.filter(
            vehicle_id=vehicle.id,
            statut__in=['confirmee', 'confirmée'],
            date_debut__lte=today,
            date_fin__gte=today,
        ).exists()

        if not active:
            vehicle.statut = 'disponible'
            vehicle.save()
            liberes.append(f'{vehicle.marque} {vehicle.modele} ({vehicle.immatriculation})')
            print(f'[Sync] {vehicle.marque} {vehicle.modele} → disponible')

    print(f'[Sync] {len(liberes)} véhicule(s) libéré(s)')
    return {'vehicules_liberes': len(liberes), 'details': liberes}