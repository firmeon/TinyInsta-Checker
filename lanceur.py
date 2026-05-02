import os
import time
import subprocess
import requests

from google.cloud import datastore

# Configuration
BASE_URL = "https://tinyinsta-gcp.ew.r.appspot.com"
LOCUST_FILE = "locustfile.py"
OUT_DIR = "out"
TOKEN = "change-me-seed-token"

def run_locust_session(users, param_value, filename, run_id):
    """Lance une instance de Locust en mode headless avec des variables d'env."""
    print(f"--- Lancement : {filename} | Param: {param_value} | Run: {run_id} ---")
    
    # On passe les consignes à locustfile.py via les variables d'environnement
    env = os.environ.copy()
    env["BENCHMARK_PARAM"] = str(param_value)
    env["BENCHMARK_FILE"] = filename
    env["BENCHMARK_RUN"] = str(run_id)

    cmd = [
        "locust",
        "-f", LOCUST_FILE,
        "--headless",
        "-u", str(users),
        "-r", "100",
        "--run-time", "1min",
        "--host", BASE_URL,
        "--only-summary"
    ]
    
    # Exécution de la commande
    subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Petite pause pour laisser le Cloud respirer entre deux runs
    time.sleep(60)

def supprimer_fichier_si_existe(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)

def vider_database():
    client = datastore.Client()
    # Liste des Kinds utilisés dans TinyInsta
    kinds = ["User", "Post"] 

    for kind in kinds:
        print(f"Suppression des entités du type : {kind}...")
        query = client.query(kind=kind)
        query.keys_only() # On ne récupère que les clés pour aller plus vite
        
        keys = list([entity.key for entity in query.fetch()])
        
        # Datastore limite les suppressions par lots à 500 entités
        for i in range(0, len(keys), 500):
            batch = keys[i:i + 500]
            client.delete_multi(batch)

def peupler_database(nb_user_total, nb_posts_to_create, follow_to_add):
    infos = {
        "users": nb_user_total,
        "posts": nb_posts_to_create,
        "follows_min": follow_to_add,
        "follows_max": follow_to_add
    }
    response = requests.post(f"{BASE_URL}/admin/seed?token={TOKEN}", data=infos, timeout=None)
    if response.status_code != 200:
        print(f"Erreur lors du peuplement de la base : {response.status_code} - {response.text}")


def experience_concurrence():
    # --- EXPÉRIENCE 1 : PASSAGE À L'ÉCHELLE SUR LA CHARGE (CONCURRENCE) ---
    # Paramètres : 1, 10, 20, 50, 100, 1000 utilisateurs
    #concurrence_levels = [1, 10, 20, 50, 100, 1000]
    concurrence_levels = [1, 10, 20]

    print("Début du benchmark de concurrence...")
    for user in concurrence_levels:
        for run in range(1, 4): # Répété 3 fois
            run_locust_session(user, param_value=user, filename="conc.csv", run_id=run)


def experience_fanout():
    # --- EXPÉRIENCE 2 : PASSAGE À L'ÉCHELLE SUR TAILLE DES DONNÉES (FANOUT) ---
    # Consigne : 50 users simultanés, faire varier followees : 20, 40, 60

    # On ajoute 50 posts pour chaque utilisateur, on a déjà 20 follow par personne
    peupler_database(nb_user_total=1000, nb_posts_to_create=50, follow_to_add=0)

    #fanout_levels = [20, 40, 60]
    fanout_levels = [20, 40]
    last_follow = 20

    print("Début du benchmark de fanout...")
    for followees in fanout_levels:
        peupler_database(nb_user_total=1000, nb_posts_to_create=0, follow_to_add=followees - last_follow)
        last_follow = followees
        for run in range(1, 4):
            run_locust_session(50, param_value=followees, filename="fanout.csv", run_id=run)

def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    print("Nettoyage des anciens résultats et de la base...")

    supprimer_fichier_si_existe(os.path.join(OUT_DIR, "conc.csv"))
    supprimer_fichier_si_existe(os.path.join(OUT_DIR, "fanout.csv"))

    vider_database()

    for i in range(9):
        peupler_database(nb_user_total=100 * (i + 1), nb_posts_to_create=0, follow_to_add=0)


    peupler_database(nb_user_total=1000, nb_posts_to_create=50, follow_to_add=20)

    ##experience_concurrence()
    ##experience_fanout()

if __name__ == "__main__":
    main()
    #vider_database()
    #peupler_database(nb_user_total=1000, nb_posts_to_create=50, follow_to_add=20)