-- =====================================================================
--  SmartWater IoT – base de données MySQL (cohérente avec le cahier des charges)
--  6 tables métier : roles, utilisateurs, reservoirs, capteurs, mesures, alertes
--  + configuration_email (serveur SMTP) et thingspeak (relais), secrets chiffrés
--  + tables techniques de Django (sessions, admin, migrations).
--
--  Canal ThingSpeak 3597819 déjà relié au capteur n° 1 (relais désactivé) :
--  collez les clés Write/Read dans Paramètres > ThingSpeak puis activez le relais.
--  Aucune clé n'est stockée dans ce fichier.
--
--  Méthode recommandée : créer une base vide `smartwater` puis lancer
--      python manage.py migrate
--      python manage.py init_donnees
--  Ce script est équivalent (import possible via phpMyAdmin). Il contient :
--      - les rôles par défaut (admin, utilisateur, technicien)
--      - un compte admin@smartwater.local / SmartWater2026!  (mot de passe HACHÉ)
--      - un réservoir de démonstration et son capteur
--  Niveau (%) = (hauteur_cm - distance_cm) / hauteur_cm * 100
-- =====================================================================
CREATE DATABASE IF NOT EXISTS `smartwater` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `smartwater`;
/*M!999999\- enable the sandbox mode */ 

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP TABLE IF EXISTS `alertes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `alertes` (
  `id_alerte` int(11) NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL,
  `message` varchar(255) NOT NULL,
  `lue` tinyint(1) NOT NULL,
  `date_alerte` datetime(6) NOT NULL,
  `id_reservoir` int(11) NOT NULL,
  PRIMARY KEY (`id_alerte`),
  KEY `alertes_id_reservoir_99581c7e_fk_reservoirs_id_reservoir` (`id_reservoir`),
  CONSTRAINT `alertes_id_reservoir_99581c7e_fk_reservoirs_id_reservoir` FOREIGN KEY (`id_reservoir`) REFERENCES `reservoirs` (`id_reservoir`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `alertes` WRITE;
/*!40000 ALTER TABLE `alertes` DISABLE KEYS */;
/*!40000 ALTER TABLE `alertes` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES
(1,'Can add log entry',1,'add_logentry'),
(2,'Can change log entry',1,'change_logentry'),
(3,'Can delete log entry',1,'delete_logentry'),
(4,'Can view log entry',1,'view_logentry'),
(5,'Can add permission',3,'add_permission'),
(6,'Can change permission',3,'change_permission'),
(7,'Can delete permission',3,'delete_permission'),
(8,'Can view permission',3,'view_permission'),
(9,'Can add group',2,'add_group'),
(10,'Can change group',2,'change_group'),
(11,'Can delete group',2,'delete_group'),
(12,'Can view group',2,'view_group'),
(13,'Can add content type',4,'add_contenttype'),
(14,'Can change content type',4,'change_contenttype'),
(15,'Can delete content type',4,'delete_contenttype'),
(16,'Can view content type',4,'view_contenttype'),
(17,'Can add session',5,'add_session'),
(18,'Can change session',5,'change_session'),
(19,'Can delete session',5,'delete_session'),
(20,'Can view session',5,'view_session'),
(21,'Can add rôle',6,'add_role'),
(22,'Can change rôle',6,'change_role'),
(23,'Can delete rôle',6,'delete_role'),
(24,'Can view rôle',6,'view_role'),
(25,'Can add utilisateur',7,'add_utilisateur'),
(26,'Can change utilisateur',7,'change_utilisateur'),
(27,'Can delete utilisateur',7,'delete_utilisateur'),
(28,'Can view utilisateur',7,'view_utilisateur'),
(29,'Can add réservoir',10,'add_reservoir'),
(30,'Can change réservoir',10,'change_reservoir'),
(31,'Can delete réservoir',10,'delete_reservoir'),
(32,'Can view réservoir',10,'view_reservoir'),
(33,'Can add capteur',8,'add_capteur'),
(34,'Can change capteur',8,'change_capteur'),
(35,'Can delete capteur',8,'delete_capteur'),
(36,'Can view capteur',8,'view_capteur'),
(37,'Can add mesure',9,'add_mesure'),
(38,'Can change mesure',9,'change_mesure'),
(39,'Can delete mesure',9,'delete_mesure'),
(40,'Can view mesure',9,'view_mesure'),
(41,'Can add alerte',11,'add_alerte'),
(42,'Can change alerte',11,'change_alerte'),
(43,'Can delete alerte',11,'delete_alerte'),
(44,'Can view alerte',11,'view_alerte'),
(45,'Can add configuration e-mail',12,'add_configurationemail'),
(46,'Can change configuration e-mail',12,'change_configurationemail'),
(47,'Can delete configuration e-mail',12,'delete_configurationemail'),
(48,'Can view configuration e-mail',12,'view_configurationemail'),
(49,'Can add liaison ThingSpeak',13,'add_liaisonthingspeak'),
(50,'Can change liaison ThingSpeak',13,'change_liaisonthingspeak'),
(51,'Can delete liaison ThingSpeak',13,'delete_liaisonthingspeak'),
(52,'Can view liaison ThingSpeak',13,'view_liaisonthingspeak');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `capteurs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `capteurs` (
  `id_capteur` int(11) NOT NULL AUTO_INCREMENT,
  `modele` varchar(50) NOT NULL,
  `hauteur_cm` double NOT NULL,
  `statut` varchar(20) NOT NULL,
  `cle_api` varchar(64) NOT NULL,
  `frequence_envoi_s` int(10) unsigned NOT NULL CHECK (`frequence_envoi_s` >= 0),
  `derniere_communication` datetime(6) DEFAULT NULL,
  `id_reservoir` int(11) NOT NULL,
  PRIMARY KEY (`id_capteur`),
  UNIQUE KEY `cle_api` (`cle_api`),
  KEY `capteurs_id_reservoir_a48782e1_fk_reservoirs_id_reservoir` (`id_reservoir`),
  CONSTRAINT `capteurs_id_reservoir_a48782e1_fk_reservoirs_id_reservoir` FOREIGN KEY (`id_reservoir`) REFERENCES `reservoirs` (`id_reservoir`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `capteurs` WRITE;
/*!40000 ALTER TABLE `capteurs` DISABLE KEYS */;
INSERT INTO `capteurs` VALUES
(1,'HC-SR04',100,'hors_ligne','demo-changez-cette-cle-0123456789abcdef',10,NULL,1);
/*!40000 ALTER TABLE `capteurs` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `configuration_email`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `configuration_email` (
  `id_configuration` int(11) NOT NULL AUTO_INCREMENT,
  `actif` tinyint(1) NOT NULL,
  `hote` varchar(150) NOT NULL,
  `port` int(10) unsigned NOT NULL CHECK (`port` >= 0),
  `securite` varchar(10) NOT NULL,
  `utilisateur` varchar(150) NOT NULL,
  `mot_de_passe` longtext NOT NULL,
  `expediteur` varchar(100) NOT NULL,
  `date_modification` datetime(6) NOT NULL,
  `modifie_par` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_configuration`),
  KEY `configuration_email_modifie_par_15855c46_fk_utilisate` (`modifie_par`),
  CONSTRAINT `configuration_email_modifie_par_15855c46_fk_utilisate` FOREIGN KEY (`modifie_par`) REFERENCES `utilisateurs` (`id_utilisateur`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `configuration_email` WRITE;
/*!40000 ALTER TABLE `configuration_email` DISABLE KEYS */;
/*!40000 ALTER TABLE `configuration_email` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_utilisateurs_id_utilisateur` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_utilisateurs_id_utilisateur` FOREIGN KEY (`user_id`) REFERENCES `utilisateurs` (`id_utilisateur`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES
(7,'accounts','utilisateur'),
(1,'admin','logentry'),
(11,'alertes','alerte'),
(2,'auth','group'),
(3,'auth','permission'),
(4,'contenttypes','contenttype'),
(12,'parametres','configurationemail'),
(13,'parametres','liaisonthingspeak'),
(8,'reservoirs','capteur'),
(9,'reservoirs','mesure'),
(10,'reservoirs','reservoir'),
(6,'roles','role'),
(5,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES
(1,'roles','0001_initial','2026-11-26 01:38:56.376911'),
(2,'accounts','0001_initial','2026-11-26 01:38:56.389240'),
(3,'accounts','0002_notifications_telephone','2026-11-26 01:38:56.398370'),
(4,'contenttypes','0001_initial','2026-11-26 01:38:56.408994'),
(5,'admin','0001_initial','2026-11-26 01:38:56.424574'),
(6,'admin','0002_logentry_remove_auto_add','2026-11-26 01:38:56.427622'),
(7,'admin','0003_logentry_add_action_flag_choices','2026-11-26 01:38:56.430215'),
(8,'reservoirs','0001_initial','2026-11-26 01:38:56.468833'),
(9,'alertes','0001_initial','2026-11-26 01:38:56.481254'),
(10,'contenttypes','0002_remove_content_type_name','2026-11-26 01:38:56.504988'),
(11,'auth','0001_initial','2026-11-26 01:38:56.562186'),
(12,'auth','0002_alter_permission_name_max_length','2026-11-26 01:38:56.574178'),
(13,'auth','0003_alter_user_email_max_length','2026-11-26 01:38:56.577270'),
(14,'auth','0004_alter_user_username_opts','2026-11-26 01:38:56.580566'),
(15,'auth','0005_alter_user_last_login_null','2026-11-26 01:38:56.584370'),
(16,'auth','0006_require_contenttypes_0002','2026-11-26 01:38:56.585119'),
(17,'auth','0007_alter_validators_add_error_messages','2026-11-26 01:38:56.587735'),
(18,'auth','0008_alter_user_username_max_length','2026-11-26 01:38:56.590698'),
(19,'auth','0009_alter_user_last_name_max_length','2026-11-26 01:38:56.594314'),
(20,'auth','0010_alter_group_name_max_length','2026-11-26 01:38:56.602776'),
(21,'auth','0011_update_proxy_permissions','2026-11-26 01:38:56.609613'),
(22,'auth','0012_alter_user_first_name_max_length','2026-11-26 01:38:56.612580'),
(23,'parametres','0001_configuration_email','2026-11-26 01:38:56.629772'),
(24,'parametres','0002_liaison_thingspeak','2026-11-26 01:38:56.646911'),
(25,'roles','0002_roles_par_defaut','2026-11-26 01:38:56.656532'),
(26,'sessions','0001_initial','2026-11-26 01:38:56.662350');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `mesures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `mesures` (
  `id_mesure` bigint(20) NOT NULL AUTO_INCREMENT,
  `distance_cm` double NOT NULL,
  `niveau_pct` double NOT NULL,
  `date_mesure` datetime(6) NOT NULL,
  `id_capteur` int(11) NOT NULL,
  PRIMARY KEY (`id_mesure`),
  KEY `mesures_date_mesure_08e85282` (`date_mesure`),
  KEY `idx_mesure_capteur_date` (`id_capteur`,`date_mesure`),
  CONSTRAINT `mesures_id_capteur_a3a21cf0_fk_capteurs_id_capteur` FOREIGN KEY (`id_capteur`) REFERENCES `capteurs` (`id_capteur`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `mesures` WRITE;
/*!40000 ALTER TABLE `mesures` DISABLE KEYS */;
/*!40000 ALTER TABLE `mesures` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `reservoirs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `reservoirs` (
  `id_reservoir` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `emplacement` varchar(150) DEFAULT NULL,
  `capacite_litres` int(10) unsigned NOT NULL CHECK (`capacite_litres` >= 0),
  `seuil_bas` double NOT NULL,
  `seuil_haut` double NOT NULL,
  `id_utilisateur` int(11) NOT NULL,
  PRIMARY KEY (`id_reservoir`),
  KEY `reservoirs_id_utilisateur_0d4bcb84_fk_utilisate` (`id_utilisateur`),
  CONSTRAINT `reservoirs_id_utilisateur_0d4bcb84_fk_utilisate` FOREIGN KEY (`id_utilisateur`) REFERENCES `utilisateurs` (`id_utilisateur`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `reservoirs` WRITE;
/*!40000 ALTER TABLE `reservoirs` DISABLE KEYS */;
INSERT INTO `reservoirs` VALUES
(1,'Réservoir Principal','Bâtiment A - cave',1000,20,85,1);
/*!40000 ALTER TABLE `reservoirs` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id_role` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(30) NOT NULL,
  `libelle` varchar(60) NOT NULL,
  `description` varchar(255) NOT NULL,
  `est_administrateur` tinyint(1) NOT NULL,
  `date_creation` datetime(6) NOT NULL,
  PRIMARY KEY (`id_role`),
  UNIQUE KEY `nom` (`nom`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES
(1,'admin','Administrateur','Accès complet au système',1,'2026-11-26 01:38:56.654401'),
(2,'utilisateur','Utilisateur','Consulte et gère ses propres réservoirs',0,'2026-11-26 01:38:56.655587'),
(3,'technicien','Technicien','Installe et entretient les capteurs de ses réservoirs',0,'2026-11-26 01:38:57.159569');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `thingspeak`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `thingspeak` (
  `id_liaison` int(11) NOT NULL AUTO_INCREMENT,
  `actif` tinyint(1) NOT NULL,
  `canal_id` int(10) unsigned NOT NULL CHECK (`canal_id` >= 0),
  `cle_ecriture` longtext NOT NULL,
  `cle_lecture` longtext NOT NULL,
  `intervalle_s` int(10) unsigned NOT NULL CHECK (`intervalle_s` >= 0),
  `dernier_envoi` datetime(6) DEFAULT NULL,
  `dernier_resultat` varchar(255) NOT NULL,
  `nb_envois` int(10) unsigned NOT NULL CHECK (`nb_envois` >= 0),
  `id_capteur` int(11) NOT NULL,
  PRIMARY KEY (`id_liaison`),
  UNIQUE KEY `id_capteur` (`id_capteur`),
  CONSTRAINT `thingspeak_id_capteur_01113089_fk_capteurs_id_capteur` FOREIGN KEY (`id_capteur`) REFERENCES `capteurs` (`id_capteur`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `thingspeak` WRITE;
/*!40000 ALTER TABLE `thingspeak` DISABLE KEYS */;
INSERT INTO `thingspeak` VALUES
(1,0,3597819,'','',20,NULL,'',0,1);
/*!40000 ALTER TABLE `thingspeak` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `utilisateurs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `utilisateurs` (
  `id_utilisateur` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `mot_de_passe` varchar(255) NOT NULL,
  `actif` tinyint(1) NOT NULL,
  `derniere_connexion` datetime(6) DEFAULT NULL,
  `date_creation` datetime(6) NOT NULL,
  `notif_email` tinyint(1) NOT NULL,
  `notif_push` tinyint(1) NOT NULL,
  `notif_son` tinyint(1) NOT NULL,
  `id_role` int(11) NOT NULL,
  `ntfy_topic` varchar(64) NOT NULL,
  PRIMARY KEY (`id_utilisateur`),
  UNIQUE KEY `email` (`email`),
  KEY `utilisateurs_id_role_7ea69c33_fk_roles_id_role` (`id_role`),
  CONSTRAINT `utilisateurs_id_role_7ea69c33_fk_roles_id_role` FOREIGN KEY (`id_role`) REFERENCES `roles` (`id_role`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `utilisateurs` WRITE;
/*!40000 ALTER TABLE `utilisateurs` DISABLE KEYS */;
INSERT INTO `utilisateurs` VALUES
(1,'Administrateur','admin@smartwater.local','pbkdf2_sha256$1500000$hwOuZSoII78b2nhxtpwFjT$aiH1SoItbqoXgb0MbckjWWKmvulmhRM4lI1Z7PD0S3I=',1,NULL,'2026-11-26 01:38:57.390748',1,0,0,1,'');
/*!40000 ALTER TABLE `utilisateurs` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

