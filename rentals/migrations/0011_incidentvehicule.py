from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rentals', '0010_reservation_checklist_retour_and_more'),
        ('vehicles', '__first__'),  # assure que vehicles est appliqué avant
    ]

    operations = [
        migrations.CreateModel(
            name='IncidentVehicule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_incident', models.CharField(
                    choices=[
                        ('impact',   'Impact / Bosse'),
                        ('rayure',   'Éraflure / Rayure'),
                        ('accident', 'Accident'),
                        ('autre',    'Autre dommage'),
                    ],
                    default='impact', max_length=20
                )),
                ('gravite', models.CharField(
                    choices=[
                        ('mineur', 'Mineur'),
                        ('modere', 'Modéré'),
                        ('grave',  'Grave'),
                    ],
                    default='mineur', max_length=10
                )),
                ('zone',            models.CharField(blank=True, max_length=100)),
                ('description',     models.TextField()),
                ('date_incident',   models.DateField()),
                ('signale_par',     models.CharField(blank=True, max_length=100)),
                ('cout_reparation', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('repare',          models.BooleanField(default=False)),
                ('date_reparation', models.DateField(blank=True, null=True)),
                ('photos_notes',    models.TextField(blank=True)),
                ('created_at',      models.DateTimeField(auto_now_add=True)),
                ('vehicle', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='incidents',
                    to='vehicles.vehicle'   # ✅ app vehicles, pas rentals
                )),
                ('reservation', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='incidents',
                    to='rentals.reservation'   # ✅ app rentals
                )),
            ],
            options={
                'verbose_name': 'Incident Véhicule',
                'verbose_name_plural': 'Incidents Véhicules',
                'ordering': ['-date_incident', '-created_at'],
            },
        ),
    ]