# IFRI_MentorLink — Rattrapage Projet Intégrateur 2025‑2026

Application web mono-page permettant à un mentoré de rechercher des mentors
compatibles selon les matières recherchées et le créneau horaire souhaité,
**sans authentification**.

## Technologies (imposées par le sujet)

- **Frontend** : HTML / CSS / JavaScript (Tailwind CDN, autorisé par le sujet)
- **Backend** : Python — Flask
- **Base de données** : MySQL

## 1. Créer la base de données MySQL

Assurez-vous d'avoir un serveur MySQL disponible (WAMP, XAMPP, MySQL
Workbench, ou `mysql-server` installé en local).

```bash
mysql -u root -p < schema.sql
```

Ce script crée la base `mentorlink`, la table `mentors`, et l'insère avec
**4 mentors de test** (le minimum demandé par le sujet est 3), couvrant
tous les champs requis : nom, matières/compétences, disponibilités
horaires, filière/niveau, format de mentorat.

## 2. Configurer la connexion

Par défaut, l'application se connecte avec `host=localhost`, `user=root`,
`password=""` (vide), `database=mentorlink`. Si votre configuration MySQL
est différente, définissez les variables d'environnement avant de lancer
le serveur :

```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=votre_mot_de_passe
export DB_NAME=mentorlink
```

## 3. Installer les dépendances et lancer le serveur

```bash
python3 -m venv venv
source venv/bin/activate        # sous Windows : venv\Scripts\activate

pip install -r requirements.txt

python app.py
```

Ouvrez ensuite **http://127.0.0.1:5000**.

## Structure du projet

```
IFRI_MentorLink/
├── app.py                  # Backend Flask : connexion MySQL + algorithme de matching
├── schema.sql               # Création de la base MySQL + jeu de données de test
├── requirements.txt
├── README.md
├── templates/
│   └── index.html          # Page unique (formulaire + résultats)
└── static/
    ├── css/style.css
    └── js/script.js        # Appels API + rendu dynamique des résultats
```

## Algorithme de matching

Implémenté dans `app.py`, fonction `rechercher_mentors()` — interroge
MySQL puis applique les règles côté back-end :

1. **Filtre matières** : un mentor est retenu s'il partage **au moins une**
   matière avec celles recherchées (comparaison insensible à la casse).
2. **Filtre horaire** : l'heure souhaitée doit tomber dans la plage de
   disponibilité du mentor **± 1 heure de tolérance**.
3. **Filtre filière (optionnel)** : si renseignée, ne garde que les
   mentors dont la filière correspond (recherche partielle).
4. **Score de compatibilité (sur 100)** :
   - 70 points au prorata du nombre de matières en commun / matières demandées
   - 30 points selon la proximité horaire (100 % si dans la plage,
     dégressif jusqu'à 0 à la limite des ±60 minutes de tolérance)
5. Les résultats sont triés par score décroissant.


