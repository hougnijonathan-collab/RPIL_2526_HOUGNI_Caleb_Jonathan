-- IFRI_MentorLink — Rattrapage Projet Intégrateur 2025-2026
-- Script de création de la base de données MySQL et jeu de données de test

CREATE DATABASE IF NOT EXISTS mentorlink
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE mentorlink;

CREATE TABLE IF NOT EXISTS mentors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(120) NOT NULL,
    matieres VARCHAR(300) NOT NULL,          -- matières séparées par des virgules
    disponibilite_debut TIME NOT NULL,
    disponibilite_fin TIME NOT NULL,
    filiere VARCHAR(120) NOT NULL,
    format_mentorat ENUM('presentiel', 'en_ligne', 'les_deux') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Jeu de données de test (le sujet impose au moins 3 mentors)
INSERT INTO mentors (nom, matieres, disponibilite_debut, disponibilite_fin, filiere, format_mentorat)
VALUES
  ('Dr. Adéyèmi KOUDOGBO',
   'Mathématiques,Algorithmique,Structures Algébriques',
   '08:00:00', '12:00:00',
   'Mathématiques Informatique et Applications', 'les_deux'),

  ('Ing. Falilath ZANNOU',
   'Programmation Python,Bases de données,Développement Web',
   '14:00:00', '17:00:00',
   'Génie Logiciel', 'en_ligne'),

  ('Prof. Cyrille AHOUANDJINOU',
   'Physique,Optique,Probabilité et Statistique',
   '09:00:00', '11:30:00',
   "Sciences de l'Ingénieur", 'presentiel'),

  ('Mme Rachida ISSIFOU',
   'Réseaux,Systèmes d''exploitation,Sécurité informatique',
   '16:00:00', '19:00:00',
   'Systèmes et Réseaux', 'les_deux');
