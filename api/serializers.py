from rest_framework import serializers

from alertes.models import Alerte
from reservoirs.models import Capteur, Mesure, Reservoir


class CapteurSerializer(serializers.ModelSerializer):
    en_ligne = serializers.BooleanField(read_only=True)
    topic_mqtt = serializers.CharField(read_only=True)

    class Meta:
        model = Capteur
        fields = ['id_capteur', 'modele', 'hauteur_cm', 'statut', 'en_ligne', 'frequence_envoi_s',
                  'derniere_communication', 'topic_mqtt']
        read_only_fields = ['statut', 'derniere_communication']


class ReservoirSerializer(serializers.ModelSerializer):
    capteurs = CapteurSerializer(many=True, read_only=True)
    niveau_actuel = serializers.SerializerMethodField()
    hauteur_cm = serializers.FloatField(write_only=True, required=False, min_value=1,
                                        help_text='Crée le capteur associé (création uniquement)')

    class Meta:
        model = Reservoir
        fields = ['id_reservoir', 'nom', 'emplacement', 'capacite_litres', 'seuil_bas', 'seuil_haut',
                  'utilisateur', 'niveau_actuel', 'capteurs', 'hauteur_cm']
        read_only_fields = ['utilisateur']

    def get_niveau_actuel(self, obj):
        m = obj.derniere_mesure()
        return m.niveau_pct if m else None

    def validate(self, data):
        bas = data.get('seuil_bas', getattr(self.instance, 'seuil_bas', 20))
        haut = data.get('seuil_haut', getattr(self.instance, 'seuil_haut', 85))
        if not (0 <= bas < haut <= 100):
            raise serializers.ValidationError('Il faut 0 ≤ seuil_bas < seuil_haut ≤ 100.')
        if not self.instance and 'hauteur_cm' not in data:
            raise serializers.ValidationError({'hauteur_cm': 'Obligatoire pour créer le capteur.'})
        return data

    def create(self, data):
        hauteur = data.pop('hauteur_cm')
        reservoir = super().create(data)
        Capteur.objects.create(reservoir=reservoir, hauteur_cm=hauteur)
        return reservoir

    def update(self, instance, data):
        data.pop('hauteur_cm', None)
        return super().update(instance, data)


class MesureSerializer(serializers.ModelSerializer):
    id_capteur = serializers.IntegerField(source='capteur_id', read_only=True)
    id_reservoir = serializers.IntegerField(source='capteur.reservoir_id', read_only=True)

    class Meta:
        model = Mesure
        fields = ['id_mesure', 'id_capteur', 'id_reservoir', 'distance_cm', 'niveau_pct', 'date_mesure']


class EnvoiMesureSerializer(serializers.Serializer):
    """Ce que l'ESP32 envoie."""
    distance_cm = serializers.FloatField(min_value=0, max_value=2000)


class AlerteSerializer(serializers.ModelSerializer):
    id_reservoir = serializers.IntegerField(source='reservoir_id', read_only=True)
    reservoir_nom = serializers.CharField(source='reservoir.nom', read_only=True)
    gravite = serializers.CharField(read_only=True)

    class Meta:
        model = Alerte
        fields = ['id_alerte', 'id_reservoir', 'reservoir_nom', 'type', 'gravite', 'message', 'lue', 'date_alerte']
        read_only_fields = ['type', 'message', 'date_alerte']
