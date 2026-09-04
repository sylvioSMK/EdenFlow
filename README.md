# EdenFlow

Application Django pour la gestion des fiches de commande optique avec séparation des rôles : Vente, Comptabilité et Conformité.

## Objectif

EdenFlow permet de suivre une fiche de commande depuis sa création jusqu’à sa validation finale, avec un circuit bien défini et un historique des actions.

## Stack technique

- Python
- Django
- MySQL
- SQLite par défaut uniquement si nécessaire pour un essai local non productif

## Structure du projet

```text
EdenFlow/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── comptes/
│   ├── models.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/
│   ├── tests.py
│   └── __init__.py
├── fiches/
│   ├── models.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/
│   ├── tests.py
│   └── __init__.py
├── manage.py
├── requirements.txt
├── .env
├── .env.example
├── README.md
└── db.sqlite3
```

## Configuration

Copiez `.env.example` vers `.env` et adaptez les valeurs selon votre environnement.

Exemple :

```env
DEBUG=True
DJANGO_SECRET_KEY=dev-secret-local-only
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
DB_NAME=edenflow
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
```

## Installation

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Modèles principaux

### Utilisateur
- héritage de `AbstractUser`
- rôle : Vente / Comptabilité / Conformité / Admin
- département
- statut actif/inactif

### FicheCommande
- numéro de commande auto-généré
- données client
- données optiques (OD / OG)
- montant, acompte, assurance
- statut avec cycle complet :
  - `CREEE`
  - `ATTENTE_COMPTA`
  - `ATTENTE_CONFORMITE`
  - `TERMINEE`
  - `ANNULEE`

### HistoriqueFiche
- trace des actions et transitions
- utile pour la traçabilité des validations

## Développement actuel

Le projet est bien structuré en Django avec les modèles et les migrations. L’état actuel est orienté “base fonctionnelle métier” :

- structure Django correctement installée
- app `comptes` avec utilisateur personnalisé
- app `fiches` avec fiche de commande et historique
- configuration MySQL active
- migrations synchronisées

## À venir

- compléter les vues et templates
- créer les parcours d’authentification et gestion
- ajouter les formulaires de saisie
- finaliser le tableau de bord et la logique métier
- finaliser les exportations / pdf / impression
- sécuriser la configuration de production

## Auteur

Projet interne / de développement EdenFlow.
