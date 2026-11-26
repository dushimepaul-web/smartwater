-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1:3306
-- Généré le : jeu. 26 nov. 2026 à 00:05
-- Version du serveur : 9.1.0
-- Version de PHP : 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `smartwater`
--

-- --------------------------------------------------------

--
-- Structure de la table `alertes`
--

DROP TABLE IF EXISTS `alertes`;
CREATE TABLE IF NOT EXISTS `alertes` (
  `id_alerte` int NOT NULL AUTO_INCREMENT,
  `id_reservoir` int NOT NULL,
  `type` enum('niveau_bas','niveau_haut','info') NOT NULL,
  `message` varchar(255) NOT NULL,
  `lue` tinyint(1) DEFAULT '0',
  `date_alerte` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_alerte`),
  KEY `fk_alerte_reservoir` (`id_reservoir`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `alertes`
--

INSERT INTO `alertes` (`id_alerte`, `id_reservoir`, `type`, `message`, `lue`, `date_alerte`) VALUES
(1, 1, 'niveau_bas', 'Niveau bas détecté', 0, '2026-11-25 16:21:33');

-- --------------------------------------------------------

--
-- Structure de la table `capteurs`
--

DROP TABLE IF EXISTS `capteurs`;
CREATE TABLE IF NOT EXISTS `capteurs` (
  `id_capteur` int NOT NULL AUTO_INCREMENT,
  `id_reservoir` int NOT NULL,
  `modele` varchar(50) DEFAULT 'HC-SR04',
  `hauteur_cm` float NOT NULL,
  `statut` enum('en_ligne','hors_ligne') DEFAULT 'hors_ligne',
  PRIMARY KEY (`id_capteur`),
  KEY `fk_capteur_reservoir` (`id_reservoir`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `capteurs`
--

INSERT INTO `capteurs` (`id_capteur`, `id_reservoir`, `modele`, `hauteur_cm`, `statut`) VALUES
(1, 1, 'HC-SR04', 100, 'en_ligne');

-- --------------------------------------------------------

--
-- Structure de la table `mesures`
--

DROP TABLE IF EXISTS `mesures`;
CREATE TABLE IF NOT EXISTS `mesures` (
  `id_mesure` bigint NOT NULL AUTO_INCREMENT,
  `id_capteur` int NOT NULL,
  `distance_cm` float NOT NULL,
  `niveau_pct` float NOT NULL,
  `date_mesure` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_mesure`),
  KEY `id_capteur` (`id_capteur`,`date_mesure`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `mesures`
--

INSERT INTO `mesures` (`id_mesure`, `id_capteur`, `distance_cm`, `niveau_pct`, `date_mesure`) VALUES
(1, 1, 45.5, 75.5, '2026-11-25 16:21:33');

-- --------------------------------------------------------

--
-- Structure de la table `reservoirs`
--

DROP TABLE IF EXISTS `reservoirs`;
CREATE TABLE IF NOT EXISTS `reservoirs` (
  `id_reservoir` int NOT NULL AUTO_INCREMENT,
  `id_utilisateur` int NOT NULL,
  `nom` varchar(100) NOT NULL,
  `emplacement` varchar(150) DEFAULT NULL,
  `capacite_litres` int NOT NULL,
  `seuil_bas` float DEFAULT '20',
  `seuil_haut` float DEFAULT '85',
  PRIMARY KEY (`id_reservoir`),
  KEY `fk_reservoir_utilisateur` (`id_utilisateur`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `reservoirs`
--

INSERT INTO `reservoirs` (`id_reservoir`, `id_utilisateur`, `nom`, `emplacement`, `capacite_litres`, `seuil_bas`, `seuil_haut`) VALUES
(1, 1, 'Reservoir Principal', 'Bâtiment A - cave', 1000, 20, 85);

-- --------------------------------------------------------

--
-- Structure de la table `utilisateurs`
--

DROP TABLE IF EXISTS `utilisateurs`;
CREATE TABLE IF NOT EXISTS `utilisateurs` (
  `id_utilisateur` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `mot_de_passe` varchar(255) NOT NULL,
  `role` enum('admin','utilisateur') DEFAULT 'utilisateur',
  `date_creation` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_utilisateur`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `utilisateurs`
--

INSERT INTO `utilisateurs` (`id_utilisateur`, `nom`, `email`, `mot_de_passe`, `role`, `date_creation`) VALUES
(1, 'Jean Dupont', 'jean.dupont@smartwater.local', 'motdepasse123', 'admin', '2026-11-25 16:21:33');

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `alertes`
--
ALTER TABLE `alertes`
  ADD CONSTRAINT `fk_alerte_reservoir` FOREIGN KEY (`id_reservoir`) REFERENCES `reservoirs` (`id_reservoir`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `capteurs`
--
ALTER TABLE `capteurs`
  ADD CONSTRAINT `fk_capteur_reservoir` FOREIGN KEY (`id_reservoir`) REFERENCES `reservoirs` (`id_reservoir`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `mesures`
--
ALTER TABLE `mesures`
  ADD CONSTRAINT `fk_mesure_capteur` FOREIGN KEY (`id_capteur`) REFERENCES `capteurs` (`id_capteur`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `reservoirs`
--
ALTER TABLE `reservoirs`
  ADD CONSTRAINT `fk_reservoir_utilisateur` FOREIGN KEY (`id_utilisateur`) REFERENCES `utilisateurs` (`id_utilisateur`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
