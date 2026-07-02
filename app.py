"""
IFRI_MentorLink - Rattrapage Projet Intégrateur 2025-2026
-----------------------------------------------------------
Application web mono-page permettant à un mentoré de rechercher
des mentors compatibles (matières + créneau horaire) sans
authentification.

Technologies imposées par le sujet :
- Frontend : HTML / CSS / JavaScript
- Backend  : Python / Flask
- Base de données : MySQL

Auteur : Ozias (FAST-UAC)
"""

import os
from datetime import datetime, time

import mysql.connector
from mysql.connector import pooling
from flask import Flask, request, jsonify, render_template, g


FALLBACK_MENTORS = [
    {
        "nom": "Dr. Adéyèmi KOUDOGBO",
        "matieres": "Mathématiques,Algorithmique,Structures Algébriques",
        "disponibilite_debut": time(8, 0),
        "disponibilite_fin": time(12, 0),
        "filiere": "Mathématiques Informatique et Applications",
        "format_mentorat": "les_deux",
    },
    {
        "nom": "Ing. Falilath ZANNOU",
        "matieres": "Programmation Python,Bases de données,Développement Web",
        "disponibilite_debut": time(14, 0),
        "disponibilite_fin": time(17, 0),
        "filiere": "Génie Logiciel",
        "format_mentorat": "en_ligne",
    },
    {
        "nom": "Prof. Cyrille AHOUANDJINOU",
        "matieres": "Physique,Optique,Probabilité et Statistique",
        "disponibilite_debut": time(9, 0),
        "disponibilite_fin": time(11, 30),
        "filiere": "Sciences de l'Ingénieur",
        "format_mentorat": "presentiel",
    },
    {
        "nom": "Mme Rachida ISSIFOU",
        "matieres": "Réseaux,Systèmes d'exploitation,Sécurité informatique",
        "disponibilite_debut": time(16, 0),
        "disponibilite_fin": time(19, 0),
        "filiere": "Systèmes et Réseaux",
        "format_mentorat": "les_deux",
    },
]

# ---------------------------------------------------------------------------
# Configuration de l'application et de la base de données MySQL
# ---------------------------------------------------------------------------

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "mentorlink"),
}

# Pool de connexions MySQL (créé à la demande pour permettre le démarrage
# même si la base n'est pas accessible au moment du lancement).
connection_pool = None


def create_connection_pool():
    global connection_pool
    if connection_pool is not None:
        return connection_pool

    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="mentorlink_pool",
            pool_size=5,
            **DB_CONFIG,
        )
    except mysql.connector.Error:
        connection_pool = False

    return connection_pool


def get_connection():
    """Récupère une connexion MySQL depuis le pool pour la requête en cours."""
    if "db" not in g:
        pool = create_connection_pool()
        if not pool:
            g.db = None
        else:
            g.db = pool.get_connection()
    return g.db


@app.teardown_appcontext
def close_connection(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def matieres_list(matieres_str):
    return [m.strip() for m in matieres_str.split(",") if m.strip()]


def _to_time(value):
    """MySQL renvoie les colonnes TIME sous forme de timedelta ; on les
    convertit en objet datetime.time pour l'algorithme de matching."""
    if isinstance(value, time):
        return value
    total_seconds = int(value.total_seconds())
    heures, reste = divmod(total_seconds, 3600)
    minutes = reste // 60
    return time(hour=heures % 24, minute=minutes)


def _format_hhmm(t: time) -> str:
    return t.strftime("%H:%M")


# ---------------------------------------------------------------------------
# Algorithme de matching
# ---------------------------------------------------------------------------

HORAIRE_TOLERANCE_MINUTES = 60  # ±1 heure


def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def horaire_compatible(heure_souhaitee: time, debut: time, fin: time) -> bool:
    """
    Vérifie si l'heure souhaitée par le mentoré tombe dans la plage de
    disponibilité du mentor, avec une tolérance de ±1 heure sur les bornes.
    """
    h = _to_minutes(heure_souhaitee)
    d = _to_minutes(debut) - HORAIRE_TOLERANCE_MINUTES
    f = _to_minutes(fin) + HORAIRE_TOLERANCE_MINUTES
    return d <= h <= f


def ecart_horaire_minutes(heure_souhaitee: time, debut: time, fin: time) -> int:
    """Distance (en minutes) entre l'heure souhaitée et la plage du mentor.
    0 si l'heure souhaitée est déjà dans la plage."""
    h = _to_minutes(heure_souhaitee)
    d = _to_minutes(debut)
    f = _to_minutes(fin)
    if d <= h <= f:
        return 0
    return min(abs(h - d), abs(h - f))


def calculer_score(matieres_communes, nb_matieres_demandees, ecart_minutes):
    """
    Score de compatibilité simple sur 100 :
      - 70 points répartis selon la proportion de matières en commun
      - 30 points selon la proximité horaire (100% si dans la plage,
        dégressif jusqu'à 0 à ±60 min de tolérance)
    """
    score_matieres = 0
    if nb_matieres_demandees > 0:
        score_matieres = (len(matieres_communes) / nb_matieres_demandees) * 70

    score_horaire = max(0, 30 * (1 - (ecart_minutes / HORAIRE_TOLERANCE_MINUTES)))

    return round(score_matieres + score_horaire)


def get_mentor_rows():
    """Retourne les mentors depuis MySQL si possible, sinon un jeu de données de secours."""
    conn = get_connection()
    if conn is None:
        return FALLBACK_MENTORS

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM mentors")
        rows = cursor.fetchall()
        cursor.close()
        return rows if rows else FALLBACK_MENTORS
    except mysql.connector.Error:
        return FALLBACK_MENTORS


def rechercher_mentors(matieres_recherchees, heure_souhaitee, filiere=None):
    """
    Fonction de matching côté serveur (back-end) : interroge MySQL, applique
    les critères de compatibilité, calcule le score, et trie les résultats.
    """
    matieres_recherchees_norm = [
        m.strip().lower() for m in matieres_recherchees if m.strip()
    ]

    rows = get_mentor_rows()

    resultats = []

    for row in rows:
        mentor_matieres = matieres_list(row["matieres"])
        matieres_communes = [
            m for m in mentor_matieres
            if m.lower() in matieres_recherchees_norm
        ]

        # Condition obligatoire : au moins une matière en commun
        if not matieres_communes:
            continue

        debut = _to_time(row["disponibilite_debut"])
        fin = _to_time(row["disponibilite_fin"])

        # Condition obligatoire : tolérance horaire de ±1h
        if not horaire_compatible(heure_souhaitee, debut, fin):
            continue

        # Filtre optionnel sur la filière (si fourni par le mentoré)
        if filiere and filiere.strip():
            if filiere.strip().lower() not in row["filiere"].lower():
                continue

        ecart = ecart_horaire_minutes(heure_souhaitee, debut, fin)
        score = calculer_score(
            matieres_communes, len(matieres_recherchees_norm), ecart
        )

        resultats.append({
            "nom": row["nom"],
            "matieres_communes": matieres_communes,
            "disponibilites": f"{_format_hhmm(debut)} - {_format_hhmm(fin)}",
            "format_mentorat": row["format_mentorat"],
            "filiere": row["filiere"],
            "score": score,
        })

    resultats.sort(key=lambda r: r["score"], reverse=True)
    return resultats


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/matieres", methods=["GET"])
def api_matieres():
    """Retourne la liste unique des matières disponibles (pour aider l'UI)."""
    rows = get_mentor_rows()

    matieres = set()
    for row in rows:
        matieres.update(matieres_list(row["matieres"]))
    return jsonify(sorted(matieres))


@app.route("/api/rechercher", methods=["POST"])
def api_rechercher():
    data = request.get_json(silent=True) or {}

    matieres_raw = data.get("matieres", "")
    if isinstance(matieres_raw, list):
        matieres = matieres_raw
    else:
        matieres = str(matieres_raw).split(",")

    heure_str = data.get("heure", "")
    filiere = data.get("filiere", "")

    if not matieres or not any(m.strip() for m in matieres):
        return jsonify({"erreur": "Veuillez indiquer au moins une matière recherchée."}), 400

    try:
        heure_souhaitee = datetime.strptime(heure_str, "%H:%M").time()
    except ValueError:
        return jsonify({"erreur": "Format d'heure invalide. Utilisez HH:MM."}), 400

    try:
        resultats = rechercher_mentors(matieres, heure_souhaitee, filiere)
    except mysql.connector.Error as err:
        return jsonify({"erreur": f"Erreur de base de données : {err}"}), 500

    return jsonify({
        "nombre_resultats": len(resultats),
        "resultats": resultats,
    })


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
