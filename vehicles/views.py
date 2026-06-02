from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .models import Vehicle
from .serializers import VehicleSerializer
import os


class VehicleListView(generics.ListCreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    parser_classes = [MultiPartParser, FormParser]


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    parser_classes = [MultiPartParser, FormParser]


class AvailableVehiclesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        date_debut = request.query_params.get('date_debut')
        date_fin   = request.query_params.get('date_fin')
        if not date_debut or not date_fin:
            return Response({'error': 'date_debut and date_fin required'}, status=400)

        from rentals.models import Reservation

        # ✅ FIX: véhicules qui ont une réservation ACTIVE dans la période demandée
        reserved_ids = Reservation.objects.filter(
            statut__in=['en_attente', 'confirmée'],
            date_debut__lte=date_fin,
            date_fin__gte=date_debut
        ).values_list('vehicle_id', flat=True)

        # ✅ FIX: inclure 'disponible' ET 'loue' (un véhicule loué peut être libre
        # pour une autre période si aucune résa active ne chevauche)
        # Exclure seulement: a_vendre, vendu, maintenance, hors_service
        available = Vehicle.objects.exclude(
            id__in=reserved_ids
        ).exclude(
            statut__in=['a_vendre', 'vendu', 'maintenance', 'hors_service']
        )

        return Response(VehicleSerializer(available, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_replacement_email(request):
    """
    POST /api/vehicles/send-replacement-email/
    Envoie un email Mailjet au client pour l'informer du remplacement de véhicule.
    """
    data = request.data

    api_key    = os.environ.get('MAILJET_API_KEY',    '')
    api_secret = os.environ.get('MAILJET_API_SECRET', '')

    if not api_key or not api_secret:
        return Response({'error': 'Mailjet non configuré (MAILJET_API_KEY manquant)'}, status=500)

    try:
        from mailjet_rest import Client
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1B3A6B; padding: 24px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 22px;">🚗 Waieb Car Rent</h1>
                <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0; font-size: 14px;">Notification de remplacement de véhicule</p>
            </div>

            <div style="background: white; padding: 28px; border: 1px solid #DDE3ED;">
                <p style="font-size: 15px; color: #1A2535;">Bonjour <strong>{data.get('client_prenom')} {data.get('client_nom')}</strong>,</p>

                <div style="background: #FEE2E2; border-radius: 10px; padding: 16px; margin: 16px 0; border-left: 4px solid #DC2626;">
                    <p style="color: #991B1B; font-weight: bold; margin: 0 0 8px;">⚠️ Incident sur votre véhicule réservé</p>
                    <p style="color: #7F1D1D; margin: 0; font-size: 14px;">
                        Un incident a été déclaré sur le véhicule <strong>{data.get('ancien_vehicule')}</strong>
                        prévu pour votre location du <strong>{data.get('date_debut')}</strong> au <strong>{data.get('date_fin')}</strong>.
                    </p>
                </div>

                <div style="background: #DCFCE7; border-radius: 10px; padding: 16px; margin: 16px 0; border-left: 4px solid #16A34A;">
                    <p style="color: #166534; font-weight: bold; margin: 0 0 8px;">✅ Véhicule de remplacement confirmé</p>
                    <p style="color: #14532D; margin: 0; font-size: 14px;">
                        Nous vous proposons le véhicule <strong>{data.get('nouveau_vehicule')}</strong>
                        pour les mêmes dates.
                    </p>
                    <p style="color: #14532D; margin: 8px 0 0; font-size: 15px;">
                        Nouveau total : <strong>{data.get('nouveau_total')} DT</strong>
                    </p>
                </div>

                <div style="background: #EFF4FB; border-radius: 10px; padding: 16px; margin: 16px 0;">
                    <p style="color: #1B3A6B; font-weight: bold; margin: 0 0 10px;">📋 Récapitulatif — Réservation #{data.get('reservation_id')}</p>
                    <table style="width: 100%; font-size: 13px; color: #374151; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #DDE3ED;">
                            <td style="padding: 8px 0; color: #6B7280;">Période</td>
                            <td style="font-weight: 600;">{data.get('date_debut')} → {data.get('date_fin')}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #DDE3ED;">
                            <td style="padding: 8px 0; color: #6B7280;">Ancien véhicule</td>
                            <td style="font-weight: 600; color: #DC2626;">{data.get('ancien_vehicule')}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #DDE3ED;">
                            <td style="padding: 8px 0; color: #6B7280;">Nouveau véhicule</td>
                            <td style="font-weight: 600; color: #16A34A;">{data.get('nouveau_vehicule')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6B7280;">Total</td>
                            <td style="font-weight: 800; color: #1B3A6B; font-size: 16px;">{data.get('nouveau_total')} DT</td>
                        </tr>
                    </table>
                </div>

                <p style="font-size: 14px; color: #374151; margin-top: 20px;">
                    Pour toute question, contactez-nous :
                    <a href="mailto:waiebcarrent2026@gmail.com" style="color: #1B3A6B; font-weight: 600;">waiebcarrent2026@gmail.com</a>
                </p>
            </div>

            <div style="background: #F8FAFC; padding: 16px; border-radius: 0 0 12px 12px; text-align: center; border: 1px solid #DDE3ED; border-top: none;">
                <p style="color: #94A3B8; font-size: 12px; margin: 0;">© 2026 Waieb Car Rent — Sfax, Tunisie</p>
            </div>
        </div>
        """

        message = {
            'Messages': [{
                'From': {'Email': 'waiebcarrent2026@gmail.com', 'Name': 'Waieb Car Rent'},
                'To':   [{'Email': data.get('client_email'), 'Name': f"{data.get('client_prenom')} {data.get('client_nom')}"}],
                'Subject': f"🚗 Remplacement de véhicule — Réservation #{data.get('reservation_id')}",
                'HTMLPart': html_body,
            }]
        }

        result = mailjet.send.create(data=message)
        if result.status_code == 200:
            return Response({'success': True, 'message': f"Email envoyé à {data.get('client_email')}"})
        else:
            return Response({'error': 'Erreur Mailjet', 'detail': result.json()}, status=500)

    except ImportError:
        return Response({'error': 'mailjet_rest non installé. pip install mailjet-rest'}, status=500)
    except Exception as e:
        return Response({'error': str(e)}, status=500)