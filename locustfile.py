import os
import subprocess
import csv
from locust import HttpUser, task, between, events

# Configuration des fichiers de sortie
OUT_DIR = "out"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

def get_gcp_instances_count():
    """
    Récupère le nombre d'instances App Engine en cours d'exécution.
    Nécessite que gcloud soit configuré sur votre machine.
    """
    try:
        # Exécute la commande demandée dans les consignes
        result = subprocess.run(
            ['gcloud', 'app', 'instances', 'list', '--format=json'],
            capture_output=True, text=True
        )
        # On compte simplement le nombre d'entrées dans la liste JSON retournée
        import json
        instances = json.loads(result.stdout)
        return len(instances)
    except Exception as e:
        print(f"Erreur lors de la récupération des instances : {e}")
        return 0

class TinyInstaUser(HttpUser):
    # Temps d'attente entre les requêtes pour simuler un comportement humain
    wait_time = between(1, 2)
    
    def on_start(self):
        """ Initialisation : on pourrait choisir un ID utilisateur au hasard ici """
        self.user_id = "user1" # À dynamiser selon votre génération de données

    @task
    def get_timeline(self):
        """ Simule la requête de récupération de la timeline """
        with self.client.get(f"/api/timeline?user={self.user_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

# Hook Locust pour enregistrer les résultats en CSV à la fin de chaque run
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    # Récupération des statistiques globales de Locust
    stats = environment.stats.total
    avg_time = stats.avg_response_time
    failed = 1 if stats.num_failures > 0 else 0
    nb_instances = get_gcp_instances_count()
    
    # Note : Dans un usage réel, vous passeriez le paramètre (concurrence ou fanout)
    # via une variable d'environnement ou un argument personnalisé.
    param_value = os.getenv("BENCHMARK_PARAM", "1")
    file_name = os.getenv("BENCHMARK_FILE", "conc.csv")
    run_number = os.getenv("BENCHMARK_RUN", "1")

    file_path = os.path.join(OUT_DIR, file_name)
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        # Header en majuscule, séparateur virgule comme demandé
        if not file_exists:
            writer.writerow(["PARAM", "AVG_TIME", "RUN", "FAILED", "NB_INSTANCES"])
        
        writer.writerow([param_value, f"{avg_time}ms", run_number, failed, nb_instances])