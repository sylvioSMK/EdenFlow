# EdenFlow — Gestion des fiches de commande

Application Django qui digitalise le circuit d'une fiche de commande entre
Vente, Comptabilité et Conformité.

## Démarrage rapide

```bash
python3 -m venv venv
source venv/bin/activate          # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

## Configuration MySQL et variables d'environnement

Le projet utilise des variables d'environnement pour la base de données et la clé secrète Django. Copiez le fichier `.env.example` vers `.env` et adaptez les valeurs selon votre environnement.

Pour le développement local/test actuel, la configuration attend une base MySQL nommée `edenflow` sur `localhost`, avec un utilisateur `root` sans mot de passe. Cette configuration est acceptable uniquement pour le développement local. Avant toute mise en production, il faudra créer un utilisateur MySQL dédié non-root avec mot de passe fort, limité aux permissions strictement nécessaires sur la base `edenflow`.

## Créer des comptes de test (un par rôle)

```bash
python3 manage.py shell
```
```python
from comptes.models import Utilisateur
Utilisateur.objects.create_user('vente1', password='motdepasse', role='VENTE', first_name='Marie-Gabrielle')
Utilisateur.objects.create_user('compta1', password='motdepasse', role='COMPTABILITE')
Utilisateur.objects.create_user('conformite1', password='motdepasse', role='CONFORMITE', first_name='Bienvenu')
```

## Ce qui est fait (V1)

- Modèles complets : FicheCommande, Utilisateur (avec rôles), HistoriqueFiche
- Circuit de statut Créée → En attente Comptabilité → En attente Conformité → Terminée
- Verrouillage anti-conflit : `FicheCommande.transiter()` empêche deux validations
  simultanées de la même fiche (testé avec un scénario à deux "onglets")
- Tableau de bord filtré par rôle, création de fiche, page de détail avec
  actions conditionnées au rôle/statut, recherche, historique, admin Django

## Ce qui reste à faire (voir aussi le doc "structure-app-optics-eden")

- Génération du PDF imprimable identique au formulaire papier (le bouton
  "Imprimer" est présent dans le template mais pas encore branché)
- Statut "Annulée" (le champ existe dans le modèle, pas encore de bouton)
- Style à affiner (c'est une base fonctionnelle, pas encore peaufinée)
- Déploiement + passage de SQLite à MySQL (le modèle est déjà compatible)
