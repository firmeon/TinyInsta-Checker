import os
import time
import subprocess

# Configuration
BASE_URL = "https://tinyinsta-gcp.ew.r.appspot.com"
LOCUST_FILE = "locustfile.py"
OUT_DIR = "out"

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
        "--run-time", "1s",
        "--host", BASE_URL,
        "--only-summary"
    ]
    
    # Exécution de la commande
    subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Petite pause pour laisser le Cloud respirer entre deux runs
    time.sleep(5)

def delete_base():
    print("Suppression de la base de données...")
    subprocess.run(["gcloud", "datastore", "indexes", "cleanup"])
    subprocess.run(["gcloud", "datastore", "entities", "delete", "--all-kinds"])

def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    print("Nettoyage des anciens résultats et de la base...")

    if os.path.exists(os.path.join(OUT_DIR, "conc.csv")):
        os.remove(os.path.join(OUT_DIR, "conc.csv"))

    delete_base()


    # --- EXPÉRIENCE 1 : PASSAGE À L'ÉCHELLE SUR LA CHARGE (CONCURRENCE) ---
    # Paramètres : 1, 10, 20, 50, 100, 1000 utilisateurs
    #concurrence_levels = [1, 10, 20, 50, 100, 1000]
    concurrence_levels = [1, 2, 3, 5]


    print("Début du benchmark de concurrence...")
    for user in concurrence_levels:
        for run in range(1, 4): # Répété 3 fois
            # spawn_rate est la vitesse à laquelle les users arrivent
            run_locust_session(user, param_value=user, filename="conc.csv", run_id=run)
            
"""
    # --- EXPÉRIENCE 2 : PASSAGE À L'ÉCHELLE SUR TAILLE DES DONNÉES (FANOUT) ---
    # Consigne : 50 users simultanés, faire varier followees : 20, 40, 60
    # NOTE : Vous devez avoir peuplé votre base de données en conséquence avant.
    fanout_levels = [20, 40, 60]
    
    print("Début du benchmark de fanout...")
    for followees in fanout_levels:
        for run in range(1, 4):
            run_locust_session(50, param_value=followees, filename="fanout.csv", run_id=run)
"""
if __name__ == "__main__":
    main()