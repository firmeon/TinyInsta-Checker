import os
import time
import subprocess
import pandas as pd
import matplotlib.pyplot as plt

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
        "-r", "500",
        "--run-time", "1min",
        "--host", BASE_URL,
        "--only-summary"
    ]
    
    # Exécution de la commande
    subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Pause de 2 minutes pour laisser le Cloud respirer entre deux runs
    time.sleep(120)

def supprimer_fichier_si_existe(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)

def vider_database():
    client = datastore.Client()
    # Liste des Kinds utilisés dans TinyInsta
    kinds = ["User", "Post"] 

    for kind in kinds:
        print(f"Suppression des entités du type : {kind}")
        
        while True:
            query = client.query(kind=kind)
            query.keys_only()
            
            # Limite de suppression à 500 entités par itération pour éviter les timeouts (imposé par Datastore)
            keys = [entity.key for entity in query.fetch(limit=500)]
            if not keys:
                break # Plus rien à supprimer pour ce type
            client.delete_multi(keys)


def peupler_database(nb_user_total, nb_posts_to_create, follow_to_add):
    """infos = {
        "users": nb_user_total,
        "posts": nb_posts_to_create,
        "follows_min": follow_to_add,
        "follows_max": follow_to_add,
        "prefix": prefix
    }
    response = requests.post(f"{BASE_URL}/admin/seed?token={TOKEN}", data=infos, timeout=None)
    if response.status_code != 200:
        print(f"Erreur lors du peuplement de la base : {response.status_code} - {response.text}")
    """
    print(f"Peuplement de la base de données (users: {nb_user_total}, posts: {nb_posts_to_create}, follows: {follow_to_add})")
    cmd = [
        "python3", "seed.py",
        "--users", str(nb_user_total),
        "--posts", str(nb_posts_to_create),
        "--follows-min", str(follow_to_add),
        "--follows-max", str(follow_to_add)
    ]
    subprocess.run(cmd, env=os.environ.copy())


def experience_concurrence():
    # --- EXPÉRIENCE 1 : PASSAGE À L'ÉCHELLE SUR LA CHARGE (CONCURRENCE) ---
    # Paramètres : 1, 10, 20, 50, 100, 1000 utilisateurs
    concurrence_levels = [1, 10, 20, 50, 100, 1000]
    
    print("Début du test de concurrence")
    for user in concurrence_levels:
        for run in range(1, 4): # Répété 3 fois
            run_locust_session(user, param_value=user, filename="conc.csv", run_id=run)


def experience_fanout():
    # --- EXPÉRIENCE 2 : PASSAGE À L'ÉCHELLE SUR TAILLE DES DONNÉES (FANOUT) ---
    # Consigne : 50 users simultanés, faire varier followees : 20, 40, 60

    # On ajoute 50 posts pour chaque utilisateur, on a déjà 20 follow par personne
    peupler_database(nb_user_total=1000, nb_posts_to_create=50, follow_to_add=0)

    fanout_levels = [20, 40, 60]
    last_follow = 20

    print("Début du test de fanout")
    for followees in fanout_levels:
        peupler_database(nb_user_total=1000, nb_posts_to_create=0, follow_to_add=followees - last_follow)
        last_follow = followees
        for run in range(1, 4):
            run_locust_session(50, param_value=followees, filename="fanout.csv", run_id=run)

def create_barplot(csv_file, output_name, title, xlabel):
    if not os.path.exists(csv_file):
        print(f"Fichier {csv_file} introuvable.")
        return

    # Chargement des données (Header majuscule, séparateur virgule)
    df = pd.read_csv(csv_file)
    
    # Nettoyage : conversion de '10ms' en entier 10
    df['AVG_TIME'] = df['AVG_TIME'].str.replace('ms', '').astype(float)

    # Groupement par paramètre pour calculer : moyenne, min (meilleur) et max (pire)
    stats = df.groupby('PARAM')['AVG_TIME'].agg(['mean', 'min', 'max']).reset_index()
    
    # Calcul de l'écart pour les barres d'erreur (yerr)
    # L'indicateur montre l'écart entre la moyenne et les extrêmes
    yerr = [stats['mean'] - stats['min'], stats['max'] - stats['mean']]

    # Création du graphique
    plt.figure(figsize=(10, 6))
    bars = plt.bar(stats['PARAM'].astype(str), stats['mean'], 
                   yerr=yerr, 
                   capsize=7, 
                   color='skyblue', 
                   edgecolor='navy',
                   label='Temps moyen')

    # Mise en forme selon l'exemple fourni
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Temps moyen par requête (ms)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Sauvegarde du fichier PNG
    plt.savefig(output_name)
    print(f"Graphique sauvegardé sous : {output_name}")
    plt.close()

def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    print("Nettoyage des anciens résultats et de la base")

    supprimer_fichier_si_existe(os.path.join(OUT_DIR, "conc.csv"))
    supprimer_fichier_si_existe(os.path.join(OUT_DIR, "fanout.csv"))

    vider_database()

    peupler_database(nb_user_total=1000, nb_posts_to_create=50000, follow_to_add=20)

    experience_concurrence()
    experience_fanout()

    print("Génération des graphiques à partir des résultats")
    create_barplot('out/conc.csv', 'conc.png', 
                   "Temps moyen par requête selon la concurrence", 
                   "Nombre d'utilisateurs concurrents")
    
    create_barplot('out/fanout.csv', 'fanout.png', 
                   "Temps moyen par requête selon le nombre d'abonnés", 
                   "Nombre de followees (Abonnés)")

    print("Expérience terminée")
if __name__ == "__main__":
    main()
