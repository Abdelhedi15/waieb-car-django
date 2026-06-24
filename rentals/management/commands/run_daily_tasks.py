# rentals/management/commands/run_daily_tasks.py
# ─────────────────────────────────────────────────────────────
# Crée cette arborescence :
# rentals/
#   management/
#     __init__.py       ← fichier vide
#     commands/
#       __init__.py     ← fichier vide
#       run_daily_tasks.py  ← CE FICHIER
# ─────────────────────────────────────────────────────────────

from django.core.management.base import BaseCommand
from rentals.tasks import alerte_j1_paiements, sync_statuts_vehicules


class Command(BaseCommand):
    help = 'Tâches quotidiennes : alerte J-1 paiements + sync statuts véhicules'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('🚀 Démarrage des tâches quotidiennes Waieb Car Rent')
        self.stdout.write('=' * 60)

        # ── Tâche 1 : Alerte J-1 ────────────────────────────────
        self.stdout.write('\n📧 Tâche 1 : Alertes J-1 paiements...')
        try:
            result1 = alerte_j1_paiements()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Alertes J-1 : {result1["emails_envoyes"]} email(s) envoyé(s)'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur alertes J-1 : {e}'))

        # ── Tâche 2 : Sync statuts ───────────────────────────────
        self.stdout.write('\n🚗 Tâche 2 : Synchronisation statuts véhicules...')
        try:
            result2 = sync_statuts_vehicules()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Sync : {result2["vehicules_liberes"]} véhicule(s) mis à jour'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur sync véhicules : {e}'))

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('✅ Tâches terminées')
        self.stdout.write('=' * 60)