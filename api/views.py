from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse

from alertes.models import Alerte
from reservoirs.models import Capteur, Mesure, Reservoir
from reservoirs.services import enregistrer_mesure
from reservoirs.stats import etat_reservoir, periode_valide, resume_global, serie_niveaux

from .serializers import AlerteSerializer, EnvoiMesureSerializer, MesureSerializer, ReservoirSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def racine(request, format=None):
    """API REST SmartWater IoT – liste des points d'accès."""
    liste = reverse('api-reservoir-list', request=request)
    return Response({
        'envoi_mesure (ESP32 : POST, en-tête X-API-Key)': reverse('api-envoi-mesure', request=request),
        'tableau_de_bord (GET ?reservoir=<id>&periode=1h|24h|7j)': reverse('api-dashboard', request=request),
        'reservoirs (GET, POST, PUT, DELETE)': liste,
        'niveau_temps_reel (GET)': liste + '<id>/niveau/',
        'serie_graphique (GET ?periode=1h|24h|7j|30j)': liste + '<id>/serie/',
        'mesures (GET ?reservoir=<id>&limite=100)': reverse('api-mesure-list', request=request),
        'alertes (GET ?non_lues=1, POST <id>/lue/)': reverse('api-alerte-list', request=request),
        'moi (GET)': reverse('api-moi', request=request),
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def envoi_mesure(request):
    """Reçoit une mesure de l'ESP32.

    En-tête : `X-API-Key: <clé du capteur>` (ou champ `cle` dans le JSON).
    Corps JSON : `{"distance_cm": 45.5}`.
    """
    cle = request.headers.get('X-API-Key') or request.data.get('cle') or request.query_params.get('cle')
    capteur = Capteur.objects.select_related('reservoir').filter(cle_api=cle).first() if cle else None
    if not capteur:
        return Response({'erreur': "Clé d'API manquante ou invalide"}, status=status.HTTP_401_UNAUTHORIZED)
    s = EnvoiMesureSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    mesure, alerte = enregistrer_mesure(capteur, s.validated_data['distance_cm'])
    return Response({
        'ok': True,
        'id_mesure': mesure.id_mesure,
        'niveau_pct': mesure.niveau_pct,
        'alerte': alerte.message if alerte else None,
        # l'ESP32 adapte son rythme à la fréquence choisie dans Paramètres
        'frequence_envoi_s': capteur.frequence_envoi_s,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def dashboard(request):
    """Toutes les données du tableau de bord ; la page l'interroge toutes les 5 secondes."""
    reservoirs = Reservoir.objects.visibles_par(request.user)
    choisi = reservoirs.filter(pk=request.query_params.get('reservoir') or 0).first() or reservoirs.first()
    periode = periode_valide(request.query_params.get('periode'), '24h')
    return Response({
        'global': resume_global(request.user),
        'reservoir': etat_reservoir(choisi) if choisi else None,
        'serie': serie_niveaux(choisi, periode) if choisi else None,
    })


@api_view(['GET'])
def moi(request):
    u = request.user
    return Response({'id_utilisateur': u.pk, 'nom': u.nom, 'email': u.email,
                     'role': u.role.nom, 'est_admin': u.est_admin,
                     'notif_email': u.notif_email, 'notif_push': u.notif_push, 'notif_son': u.notif_son})


class ReservoirViewSet(viewsets.ModelViewSet):
    serializer_class = ReservoirSerializer

    def get_queryset(self):
        return Reservoir.objects.visibles_par(self.request.user).prefetch_related('capteurs')

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)

    @action(detail=True)
    def niveau(self, request, pk=None):
        """Niveau actuel en temps réel."""
        return Response(etat_reservoir(self.get_object()))

    @action(detail=True)
    def serie(self, request, pk=None):
        return Response(serie_niveaux(self.get_object(), request.query_params.get('periode', '24h')))


class MesureViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MesureSerializer

    def get_queryset(self):
        qs = (Mesure.objects.filter(capteur__reservoir__in=Reservoir.objects.visibles_par(self.request.user))
              .select_related('capteur').order_by('-date_mesure'))
        if self.request.query_params.get('reservoir'):
            qs = qs.filter(capteur__reservoir_id=self.request.query_params['reservoir'])
        return qs

    def list(self, request, *args, **kwargs):
        try:
            limite = min(1000, max(1, int(request.query_params.get('limite', 100))))
        except ValueError:
            limite = 100
        return Response(self.get_serializer(self.get_queryset()[:limite], many=True).data)


class AlerteViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AlerteSerializer

    def get_queryset(self):
        qs = Alerte.objects.visibles_par(self.request.user).select_related('reservoir')
        if self.request.query_params.get('non_lues'):
            qs = qs.filter(lue=False)
        return qs

    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_queryset()[:200], many=True).data)

    @action(detail=True, methods=['post'])
    def lue(self, request, pk=None):
        alerte = self.get_object()
        alerte.lue = True
        alerte.save(update_fields=['lue'])
        return Response(self.get_serializer(alerte).data)
