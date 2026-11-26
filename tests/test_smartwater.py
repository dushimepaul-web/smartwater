from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Utilisateur
from alertes.models import Alerte
from reservoirs.models import Capteur, Mesure, Reservoir
from reservoirs.services import enregistrer_mesure
from roles.models import Role

MDP = 'UnMotDePasse!2026'


class Base(TestCase):
    def setUp(self):
        self.admin = Utilisateur.objects.create_superuser('admin@test.bi', 'Admin', MDP, email_verifie=True)
        self.paul = Utilisateur.objects.create_user('paul@test.bi', 'Paul', MDP, email_verifie=True)
        self.autre = Utilisateur.objects.create_user('autre@test.bi', 'Autre', MDP, email_verifie=True)
        self.res = Reservoir.objects.create(utilisateur=self.paul, nom='Cuve Paul', capacite_litres=1000)
        self.capteur = Capteur.objects.create(reservoir=self.res, hauteur_cm=100)


class ModelesTests(Base):
    def test_formule_du_pdf(self):
        # (100 - 45.5) / 100 * 100 = 54.5 %
        self.assertEqual(self.capteur.calculer_niveau(45.5), 54.5)
        self.assertEqual(self.capteur.calculer_niveau(150), 0)
        self.assertEqual(self.capteur.calculer_niveau(-5), 100)

    def test_mot_de_passe_hache_et_roles(self):
        self.assertTrue(self.paul.password.startswith('pbkdf2_'))
        self.assertTrue(self.paul.check_password(MDP))
        self.assertEqual(self.paul.role.nom, Role.UTILISATEUR)
        self.assertTrue(self.admin.est_admin and self.admin.is_staff)
        self.assertFalse(self.paul.est_admin)

    def test_alertes_seulement_au_franchissement_du_seuil(self):
        enregistrer_mesure(self.capteur, 50)      # 50 % normal
        enregistrer_mesure(self.capteur, 85)      # 15 % -> bas
        enregistrer_mesure(self.capteur, 88)      # 12 % toujours bas : pas de nouvelle alerte
        enregistrer_mesure(self.capteur, 10)      # 90 % -> haut
        enregistrer_mesure(self.capteur, 40)      # 60 % -> retour normal
        types = list(Alerte.objects.order_by('id_alerte').values_list('type', flat=True))
        self.assertEqual(types, ['niveau_bas', 'niveau_haut', 'info'])
        self.capteur.refresh_from_db()
        self.assertTrue(self.capteur.en_ligne)
        self.assertEqual(self.capteur.statut, 'en_ligne')

    def test_hors_ligne_si_silence(self):
        self.capteur.derniere_communication = timezone.now() - timedelta(minutes=10)
        self.assertFalse(self.capteur.en_ligne)


class PagesTests(Base):
    def test_pages_protegees(self):
        for nom in ['dashboard', 'reservoirs', 'historique', 'alertes', 'parametres', 'roles']:
            r = self.client.get(reverse(nom))
            self.assertEqual(r.status_code, 302, nom)
            self.assertIn(reverse('login'), r['Location'])

    def test_connexion_et_toutes_les_pages(self):
        r = self.client.post(reverse('login'), {'username': 'paul@test.bi', 'password': MDP})
        self.assertRedirects(r, reverse('dashboard'), fetch_redirect_response=False)
        enregistrer_mesure(self.capteur, 30)
        for nom in ['dashboard', 'reservoirs', 'historique', 'alertes', 'parametres']:
            r = self.client.get(reverse(nom))
            self.assertEqual(r.status_code, 200, nom)
        self.assertContains(self.client.get(reverse('dashboard')), 'Cuve Paul')
        # un utilisateur simple n'a pas accès aux rôles
        self.assertRedirects(self.client.get(reverse('roles')), reverse('dashboard'))
        r = self.client.get(reverse('historique_export'))
        self.assertEqual(r['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('70,0', r.content.decode('utf-8-sig'))

    def test_mauvais_mot_de_passe(self):
        r = self.client.post(reverse('login'), {'username': 'paul@test.bi', 'password': 'faux'})
        self.assertContains(r, 'incorrect')

    def test_inscription(self):
        r = self.client.post(reverse('register'), {'nom': 'Nouveau', 'email': 'New@Test.bi',
                                                   'password1': MDP, 'password2': MDP})
        self.assertRedirects(r, reverse('verifier_email'), fetch_redirect_response=False)
        u = Utilisateur.objects.get(email='new@test.bi')
        self.assertEqual(u.role.nom, 'utilisateur')
        r = self.client.post(reverse('register'), {'nom': 'X', 'email': 'paul@test.bi',
                                                   'password1': MDP, 'password2': 'autre'})

    def test_crud_reservoir(self):
        self.client.force_login(self.paul)
        r = self.client.post(reverse('reservoir_ajouter'), {
            'nom': 'Citerne', 'emplacement': 'Toit', 'capacite_litres': 500, 'hauteur_cm': 80,
            'seuil_bas': 20, 'seuil_haut': 85, 'modele': 'JSN-SR04T'})
        nouveau = Reservoir.objects.get(nom='Citerne')
        self.assertRedirects(r, reverse('reservoir_modifier', args=[nouveau.pk]))
        self.assertEqual(nouveau.utilisateur, self.paul)
        self.assertEqual(nouveau.capteurs.get().modele, 'JSN-SR04T')
        r = self.client.post(reverse('reservoir_modifier', args=[nouveau.pk]), {
            'nom': 'Citerne', 'capacite_litres': 500, 'hauteur_cm': 90, 'seuil_bas': 90, 'seuil_haut': 10,
            'modele': 'JSN-SR04T'})
        self.assertContains(r, 'supérieur au seuil bas')
        self.client.post(reverse('reservoir_supprimer', args=[nouveau.pk]))
        self.assertFalse(Reservoir.objects.filter(pk=nouveau.pk).exists())

    def test_isolation_entre_utilisateurs(self):
        self.client.force_login(self.autre)
        self.assertEqual(self.client.get(reverse('reservoir_modifier', args=[self.res.pk])).status_code, 404)
        self.client.post(reverse('reservoir_supprimer', args=[self.res.pk]))
        self.assertTrue(Reservoir.objects.filter(pk=self.res.pk).exists())

    def test_parametres(self):
        self.client.force_login(self.paul)
        self.client.post(reverse('parametres'), {'section': 'seuils', 'reservoir': self.res.pk,
                                                 'seuil_bas': 30, 'seuil_haut': 80})
        self.res.refresh_from_db()
        self.assertEqual((self.res.seuil_bas, self.res.seuil_haut), (30, 80))
        self.client.post(reverse('parametres'), {'section': 'notifications', 'notif_son': 'on'})
        self.paul.refresh_from_db()
        self.assertEqual((self.paul.notif_email, self.paul.notif_son), (False, True))
        self.client.post(reverse('parametres'), {'section': 'appareil', 'reservoir': self.res.pk,
                                                 'modele': 'HC-SR04', 'hauteur_cm': 120, 'frequence_envoi_s': 30})
        self.capteur.refresh_from_db()
        self.assertEqual((self.capteur.hauteur_cm, self.capteur.frequence_envoi_s), (120, 30))

    def test_alertes_lues(self):
        self.client.force_login(self.paul)
        a = Alerte.objects.create(reservoir=self.res, type='niveau_bas', message='bas')
        self.assertContains(self.client.get(reverse('alertes')), 'Critique')
        self.client.post(reverse('alerte_lue', args=[a.pk]))
        a.refresh_from_db()
        self.assertTrue(a.lue)


class RolesTests(Base):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_page_et_creation_role(self):
        self.assertContains(self.client.get(reverse('roles')), 'Paul')
        self.client.post(reverse('role_ajouter'), {'nom': 'technicien', 'libelle': 'Technicien', 'description': ''})
        tech = Role.objects.get(nom='technicien')
        self.client.post(reverse('utilisateur_modifier', args=[self.paul.pk]),
                         {'nom': 'Paul', 'email': 'paul@test.bi', 'role': tech.pk, 'is_active': 'on'})
        self.paul.refresh_from_db()
        self.assertEqual(self.paul.role, tech)
        # rôle utilisé : suppression refusée
        self.client.post(reverse('role_supprimer', args=[tech.pk]))
        self.assertTrue(Role.objects.filter(pk=tech.pk).exists())

    def test_roles_systeme_et_dernier_admin_proteges(self):
        admin_role = Role.objects.get(nom='admin')
        self.client.post(reverse('role_supprimer', args=[admin_role.pk]))
        self.assertTrue(Role.objects.filter(nom='admin').exists())
        simple = Role.objects.get(nom='utilisateur')
        self.client.post(reverse('utilisateur_modifier', args=[self.admin.pk]),
                         {'nom': 'Admin', 'email': 'admin@test.bi', 'role': simple.pk, 'is_active': 'on'})
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.est_admin)

    def test_admin_voit_tous_les_reservoirs(self):
        self.assertContains(self.client.get(reverse('reservoirs')), 'Cuve Paul')
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)


class ApiTests(Base):
    def setUp(self):
        super().setUp()
        self.api = APIClient()

    def test_envoi_mesure_esp32(self):
        url = reverse('api-envoi-mesure')
        self.assertEqual(self.api.post(url, {'distance_cm': 40}, format='json').status_code, 401)
        r = self.api.post(url, {'distance_cm': 45.5}, format='json', HTTP_X_API_KEY=self.capteur.cle_api)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()['niveau_pct'], 54.5)
        r = self.api.post(url, {'distance_cm': 'abc'}, format='json', HTTP_X_API_KEY=self.capteur.cle_api)
        self.assertEqual(r.status_code, 400)
        r = self.api.post(url, {'distance_cm': 90, 'cle': self.capteur.cle_api}, format='json')
        self.assertEqual(r.json()['alerte'], "Niveau d'eau trop bas (10%) – Cuve Paul")

    def test_niveau_temps_reel_et_droits(self):
        enregistrer_mesure(self.capteur, 25)
        self.assertEqual(self.api.get(reverse('api-dashboard')).status_code, 403)
        self.api.force_authenticate(self.paul)
        r = self.api.get(reverse('api-reservoir-niveau', args=[self.res.pk])).json()
        self.assertEqual((r['niveau_pct'], r['volume_litres'], r['etat']), (75.0, 750, 'normal'))
        d = self.api.get(reverse('api-dashboard'), {'periode': '1h'}).json()
        self.assertEqual(d['global']['nb_en_ligne'], 1)
        self.assertEqual(len(d['serie']['points']), 1)
        self.assertEqual(len(self.api.get(reverse('api-mesure-list')).json()), 1)
        self.api.force_authenticate(self.autre)
        self.assertEqual(self.api.get(reverse('api-reservoir-niveau', args=[self.res.pk])).status_code, 404)

    def test_crud_reservoir_api(self):
        self.api.force_authenticate(self.paul)
        r = self.api.post(reverse('api-reservoir-list'), {'nom': 'API', 'capacite_litres': 200, 'hauteur_cm': 50},
                          format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(len(r.json()['capteurs']), 1)
        self.assertEqual(len(self.api.get(reverse('api-reservoir-list')).json()), 2)

    def test_alertes_api(self):
        a = Alerte.objects.create(reservoir=self.res, type='info', message='x')
        self.api.force_authenticate(self.paul)
        self.assertEqual(len(self.api.get(reverse('api-alerte-list'), {'non_lues': 1}).json()), 1)
        self.api.post(reverse('api-alerte-lue', args=[a.pk]))
        self.assertEqual(len(self.api.get(reverse('api-alerte-list'), {'non_lues': 1}).json()), 0)

    def test_serie_regroupee(self):
        now = timezone.now()
        Mesure.objects.bulk_create([Mesure(capteur=self.capteur, distance_cm=50, niveau_pct=50,
                                           date_mesure=now - timedelta(hours=h)) for h in range(1, 48)])
        self.api.force_authenticate(self.paul)
        s = self.api.get(reverse('api-reservoir-serie', args=[self.res.pk]), {'periode': '24h'}).json()
        self.assertEqual(len(s['points']), 23)
        self.assertTrue(all(p['niveau'] == 50 for p in s['points']))


class GestionUtilisateursTests(Base):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_creer_modifier_utilisateur(self):
        tech = Role.objects.create(nom='technicien', libelle='Technicien')
        r = self.client.post(reverse('utilisateur_ajouter'), {
            'nom': 'Marie', 'email': 'Marie@Test.bi', 'role': tech.pk, 'is_active': 'on', 'mot_de_passe': MDP})
        self.assertRedirects(r, reverse('roles'))
        marie = Utilisateur.objects.get(email='marie@test.bi')
        self.assertEqual(marie.role, tech)
        self.assertTrue(marie.check_password(MDP))
        # mot de passe trop simple refusé, e-mail déjà pris refusé
        r = self.client.post(reverse('utilisateur_ajouter'), {
            'nom': 'X', 'email': 'paul@test.bi', 'role': tech.pk, 'mot_de_passe': '123'})
        self.assertContains(r, 'existe déjà')
        self.assertContains(r, 'trop court')
        # modification sans mot de passe : l'ancien est conservé ; désactivation
        self.client.post(reverse('utilisateur_modifier', args=[marie.pk]), {
            'nom': 'Marie N.', 'email': 'marie@test.bi', 'role': tech.pk, 'mot_de_passe': ''})
        marie.refresh_from_db()
        self.assertEqual(marie.nom, 'Marie N.')
        self.assertFalse(marie.is_active)
        self.assertTrue(marie.check_password(MDP))
        # un compte désactivé ne peut plus se connecter
        self.client.logout()
        r = self.client.post(reverse('login'), {'username': 'marie@test.bi', 'password': MDP})
        self.assertEqual(r.status_code, 200)

    def test_supprimer_avec_transfert(self):
        r = self.client.get(reverse('utilisateur_supprimer', args=[self.paul.pk]))
        self.assertContains(r, '1 réservoir')
        self.client.post(reverse('utilisateur_supprimer', args=[self.paul.pk]), {'transferer': 'on'})
        self.assertFalse(Utilisateur.objects.filter(pk=self.paul.pk).exists())
        self.res.refresh_from_db()
        self.assertEqual(self.res.utilisateur, self.admin)

    def test_supprimer_sans_transfert(self):
        self.client.post(reverse('utilisateur_supprimer', args=[self.paul.pk]))
        self.assertFalse(Reservoir.objects.filter(pk=self.res.pk).exists())

    def test_protections(self):
        # pas de suppression de soi-même
        self.client.post(reverse('utilisateur_supprimer', args=[self.admin.pk]))
        self.assertTrue(Utilisateur.objects.filter(pk=self.admin.pk).exists())
        # le dernier admin ne peut pas être désactivé
        self.client.post(reverse('utilisateur_modifier', args=[self.admin.pk]), {
            'nom': 'Admin', 'email': 'admin@test.bi', 'role': self.admin.role_id})
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        # un utilisateur simple n'a pas accès
        self.client.force_login(self.paul)
        self.client.post(reverse('utilisateur_supprimer', args=[self.autre.pk]))
        self.assertTrue(Utilisateur.objects.filter(pk=self.autre.pk).exists())


class FilSynchrone:
    """Remplace threading.Thread dans les tests : exécute tout de suite."""
    def __init__(self, target, daemon=None):
        self.target = target

    def start(self):
        self.target()


class FausseReponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@mock.patch('alertes.notifications.threading.Thread', FilSynchrone)
class NotificationsTests(Base):
    def setUp(self):
        super().setUp()
        self.paul.notif_email = True
        self.paul.notif_push = True
        self.paul.ntfy_topic = 'smartwater-test-123'
        self.paul.save()

    def test_alerte_envoyee_par_email_et_ntfy(self):
        with mock.patch('alertes.notifications.urllib.request.urlopen', return_value=FausseReponse()) as envoi:
            with self.captureOnCommitCallbacks(execute=True):
                enregistrer_mesure(self.capteur, 50)
            with self.captureOnCommitCallbacks(execute=True):
                enregistrer_mesure(self.capteur, 90)   # 10 % -> critique
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['paul@test.bi'])
        self.assertIn('Critique', mail.outbox[0].subject)
        envoi.assert_called_once()
        req = envoi.call_args[0][0]
        self.assertEqual(req.full_url, 'https://ntfy.sh/')
        corps = __import__('json').loads(req.data)
        self.assertEqual((corps['topic'], corps['priority']), ('smartwater-test-123', 5))
        self.assertIn('Critique', corps['title'])
        self.assertIn('trop bas', corps['message'])

    def test_preferences_respectees(self):
        self.paul.notif_email = False
        self.paul.notif_push = False
        self.paul.save()
        with mock.patch('alertes.notifications.urllib.request.urlopen') as envoi:
            with self.captureOnCommitCallbacks(execute=True):
                enregistrer_mesure(self.capteur, 50)
            with self.captureOnCommitCallbacks(execute=True):
                enregistrer_mesure(self.capteur, 90)
        self.assertEqual(len(mail.outbox), 0)
        envoi.assert_not_called()

    def test_ntfy_en_panne_ne_bloque_pas(self):
        with mock.patch('alertes.notifications.urllib.request.urlopen', side_effect=OSError('réseau')):
            with self.captureOnCommitCallbacks(execute=True):
                enregistrer_mesure(self.capteur, 50)
            with self.captureOnCommitCallbacks(execute=True):
                m, alerte = enregistrer_mesure(self.capteur, 90)
        self.assertIsNotNone(alerte)
        self.assertEqual(len(mail.outbox), 1)

    def test_bouton_test_et_parametres(self):
        self.client.force_login(self.paul)
        r = self.client.post(reverse('parametres'), {'section': 'notifications', 'notif_push': 'on', 'ntfy_topic': 'a b'})
        self.assertContains(r, 'lettres, chiffres')
        r = self.client.post(reverse('parametres'), {'section': 'notifications', 'notif_push': 'on'})
        self.assertContains(r, 'Indiquez le sujet ntfy')
        with mock.patch('alertes.notifications.urllib.request.urlopen', return_value=FausseReponse()) as envoi:
            r = self.client.post(reverse('parametres'), {'section': 'test'}, follow=True)
        self.assertContains(r, 'Notification envoyée')
        self.assertEqual(len(mail.outbox), 1)
        envoi.assert_called_once()

    def test_echec_envoi_affiche(self):
        self.paul.notif_push = False
        self.paul.save()
        self.client.force_login(self.paul)
        with mock.patch('parametres.views.envoyer_email', side_effect=OSError('refusé')):
            r = self.client.post(reverse('parametres'), {'section': 'test'}, follow=True)
        self.assertContains(r, "Échec de l&#x27;envoi de l&#x27;e-mail")


class ConfigurationEmailTests(Base):
    MDP_APP = 'abcd efgh ijkl mnop'

    def enregistrer(self, **extra):
        donnees = {'section': 'smtp', 'actif': 'on', 'hote': 'smtp.gmail.com', 'port': 587, 'securite': 'tls',
                   'utilisateur': 'boutique@gmail.com', 'expediteur': 'SmartWater IoT', 'mot_de_passe': self.MDP_APP}
        donnees.update(extra)
        return self.client.post(reverse('parametres'), donnees, follow=True)

    def test_reserve_aux_administrateurs(self):
        from parametres.models import ConfigurationEmail
        self.client.force_login(self.paul)
        self.assertNotContains(self.client.get(reverse('parametres')), 'E-mail (SMTP)')
        self.enregistrer()
        self.assertFalse(ConfigurationEmail.objects.exists())

    def test_enregistrement_chiffre(self):
        from parametres.email_backend import mode_envoi
        from parametres.models import ConfigurationEmail
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('parametres')), 'Non configuré')
        r = self.enregistrer()
        self.assertContains(r, 'Configuration e-mail enregistrée')
        conf = ConfigurationEmail.actuelle()
        self.assertNotIn('abcd', conf.mot_de_passe_chiffre)            # chiffré dans la base
        self.assertEqual(conf.lire_mot_de_passe(), 'abcdefghijklmnop')  # espaces retirés
        self.assertNotContains(r, 'abcdefghijklmnop')                   # jamais réaffiché
        self.assertEqual(mode_envoi()[0], 'base')
        self.enregistrer(mot_de_passe='')                               # vide : l'ancien est conservé
        conf.refresh_from_db()
        self.assertEqual(conf.lire_mot_de_passe(), 'abcdefghijklmnop')
        self.assertContains(self.enregistrer(mot_de_passe='court'), '16 lettres')

    def test_backend_utilise_la_configuration(self):
        from parametres.email_backend import EmailBackend
        from parametres.models import ConfigurationEmail
        conf = ConfigurationEmail(utilisateur='boutique@gmail.com')
        conf.definir_mot_de_passe('abcdefghijklmnop')
        conf.save()
        msg = mail.EmailMessage('Sujet', 'Corps', None, ['x@test.bi'])
        vus = {}

        def faux_envoi(backend, messages):
            vus.update(host=backend.host, port=backend.port, user=backend.username, pwd=backend.password,
                       tls=backend.use_tls, de=messages[0].from_email)
            return 1
        with mock.patch('django.core.mail.backends.smtp.EmailBackend.send_messages', faux_envoi):
            self.assertEqual(EmailBackend(alias='default').send_messages([msg]), 1)
        self.assertEqual(vus, {'host': 'smtp.gmail.com', 'port': 587, 'user': 'boutique@gmail.com',
                               'pwd': 'abcdefghijklmnop', 'tls': True, 'de': 'SmartWater IoT <boutique@gmail.com>'})
        conf.actif = False
        conf.save()
        with mock.patch('django.core.mail.backends.console.EmailBackend.send_messages', return_value=1) as console:
            EmailBackend(alias='default').send_messages([msg])
        console.assert_called_once()

    def test_bouton_test_explique_les_erreurs(self):
        self.client.force_login(self.admin)
        self.enregistrer()
        erreur = OSError("(535, b'5.7.8 Username and Password not accepted')")
        with mock.patch('parametres.views.envoyer_email', side_effect=erreur):
            r = self.client.post(reverse('parametres'), {'section': 'test_smtp', 'destinataire': 'a@b.bi'}, follow=True)
        self.assertContains(r, 'mot de passe d&#x27;application')
        with mock.patch('parametres.views.envoyer_email') as envoi:
            r = self.client.post(reverse('parametres'), {'section': 'test_smtp', 'destinataire': 'a@b.bi'}, follow=True)
        envoi.assert_called_once()
        self.assertContains(r, 'E-mail de test envoyé à a@b.bi')


# ---------------------------------------------------------------- ThingSpeak
import json as _json
import threading as _threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


class FauxThingSpeak(BaseHTTPRequestHandler):
    """Imite l'API ThingSpeak documentée : POST /update -> n° d'entrée ou 0 ; GET /channels/<id>/feeds.json."""
    CLE, CANAL = 'ABCDEFGH12345678', 4242
    entrees, dernier = [], [0.0]

    def log_message(self, *a):
        pass

    def do_POST(self):
        import time
        donnees = parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode())
        ok = donnees.get('api_key', [''])[0] == self.CLE and time.time() - self.dernier[0] >= 15
        if ok:
            self.dernier[0] = time.time()
            self.entrees.append({'entry_id': len(self.entrees) + 1, 'created_at': timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                                 **{k: v[0] for k, v in donnees.items() if k.startswith('field')}})
        self.send_response(200)
        self.end_headers()
        self.wfile.write(str(len(self.entrees) if ok else 0).encode())

    def do_GET(self):
        u = urlparse(self.path)
        if u.path != f'/channels/{self.CANAL}/feeds.json':
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(_json.dumps({'channel': {'id': self.CANAL}, 'feeds': self.entrees}).encode())


class ThingSpeakTests(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.serveur = HTTPServer(('127.0.0.1', 0), FauxThingSpeak)
        _threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()
        cls.api = f'http://127.0.0.1:{cls.serveur.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        FauxThingSpeak.entrees.clear()
        FauxThingSpeak.dernier[0] = 0.0
        self.reglages = self.settings(THINGSPEAK_API=self.api)
        self.reglages.enable()
        self.client.force_login(self.paul)

    def tearDown(self):
        self.reglages.disable()
        super().tearDown()

    def configurer(self, **extra):
        donnees = {'section': 'thingspeak', 'reservoir': self.res.pk, 'actif': 'on', 'canal_id': 4242,
                   'intervalle_s': 20, 'cle_ecriture': 'abcdefgh12345678'}
        donnees.update(extra)
        return self.client.post(reverse('parametres'), donnees, follow=True)

    def test_configuration_cles_chiffrees(self):
        from parametres.models import LiaisonThingSpeak
        self.assertContains(self.client.get(reverse('parametres')), 'ThingSpeak')
        self.assertContains(self.configurer(intervalle_s=5), '15 secondes minimum')
        self.assertContains(self.configurer(cle_ecriture='trop-court'), '16 lettres et chiffres')
        self.assertContains(self.configurer(), 'Liaison ThingSpeak enregistrée')
        li = LiaisonThingSpeak.objects.get()
        self.assertEqual(li.cle_ecriture, 'ABCDEFGH12345678')
        self.assertNotIn('ABCDEFGH', li.cle_ecriture_chiffree)
        # un autre utilisateur ne voit pas ce capteur
        self.client.force_login(self.autre)
        self.assertNotContains(self.client.get(reverse('parametres')), 'Canal 4242')

    def test_relais_automatique_et_limite_15s(self):
        from parametres.models import LiaisonThingSpeak
        from parametres.thingspeak import relayer_mesure
        self.configurer()
        m1, _ = enregistrer_mesure(self.capteur, 45.5)
        self.assertTrue(relayer_mesure(m1, en_arriere_plan=False))
        self.assertEqual(FauxThingSpeak.entrees[0]['field1'], '54.5')
        self.assertEqual(FauxThingSpeak.entrees[0]['field3'], '545')
        m2, _ = enregistrer_mesure(self.capteur, 40)
        self.assertFalse(relayer_mesure(m2, en_arriere_plan=False))   # moins de 20 s : pas d'envoi
        li = LiaisonThingSpeak.objects.get()
        self.assertEqual((li.nb_envois, li.dernier_resultat), (1, 'OK – entrée n° 1'))

    def test_relais_declenche_par_la_reception(self):
        self.configurer()
        with mock.patch('alertes.notifications.threading.Thread', FilSynchrone), \
             mock.patch('parametres.thingspeak.threading.Thread', FilSynchrone):
            with self.captureOnCommitCallbacks(execute=True):
                r = APIClient().post(reverse('api-envoi-mesure'), {'distance_cm': 30}, format='json',
                                     HTTP_X_API_KEY=self.capteur.cle_api)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(FauxThingSpeak.entrees[0]['field1'], '70.0')

    def test_bouton_tester_et_mauvaise_cle(self):
        enregistrer_mesure(self.capteur, 50)
        self.configurer(actif='')
        r = self.client.post(reverse('parametres'), {'section': 'ts_test', 'reservoir': self.res.pk}, follow=True)
        self.assertContains(r, 'Connexion réussie')
        self.configurer(cle_ecriture='ZZZZZZZZ00000000', actif='')
        FauxThingSpeak.dernier[0] = 0.0
        r = self.client.post(reverse('parametres'), {'section': 'ts_test', 'reservoir': self.res.pk}, follow=True)
        self.assertContains(r, 'Échec de l’envoi vers ThingSpeak')

    def test_recuperer_mesures_manquantes(self):
        self.configurer(actif='')
        maintenant = timezone.now()
        enregistrer_mesure(self.capteur, 50)   # déjà en base : la copie ThingSpeak doit être ignorée
        FauxThingSpeak.entrees.extend([
            {'entry_id': 1, 'created_at': maintenant.strftime('%Y-%m-%dT%H:%M:%SZ'), 'field1': '50.0', 'field2': '50.0'},
            {'entry_id': 2, 'created_at': (maintenant - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ'), 'field1': '80.0', 'field2': '20.0'},
            {'entry_id': 3, 'created_at': (maintenant - timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M:%SZ'), 'field1': '61.5'},
            {'entry_id': 4, 'created_at': (maintenant - timedelta(hours=4)).strftime('%Y-%m-%dT%H:%M:%SZ')},
        ])
        r = self.client.post(reverse('parametres'), {'section': 'ts_import', 'reservoir': self.res.pk, 'heures': 24}, follow=True)
        self.assertContains(r, '2 mesure(s) récupérée(s)')
        niveaux = sorted(Mesure.objects.filter(capteur=self.capteur).values_list('niveau_pct', flat=True))
        self.assertEqual(niveaux, [50.0, 61.5, 80.0])
        # deuxième import : rien de nouveau
        r = self.client.post(reverse('parametres'), {'section': 'ts_import', 'reservoir': self.res.pk, 'heures': 24}, follow=True)
        self.assertContains(r, '0 mesure(s) récupérée(s)')

    def test_commande_importer(self):
        from io import StringIO

        from django.core.management import call_command
        self.configurer(actif='')
        FauxThingSpeak.entrees.append({'entry_id': 1, 'created_at': timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                                       'field1': '33.0', 'field2': '67.0'})
        sortie = StringIO()
        call_command('importer_thingspeak', stdout=sortie)
        self.assertIn('1 importée(s)', sortie.getvalue())
