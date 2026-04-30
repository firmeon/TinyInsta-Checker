import pandas as pd
import matplotlib.pyplot as plt
import os

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

# Génération des deux graphiques demandés
if __name__ == "__main__":
    create_barplot('out/conc.csv', 'conc.png', 
                   "Temps moyen par requête selon la concurrence", 
                   "Nombre d'utilisateurs concurrents")
    
    create_barplot('out/fanout.csv', 'fanout.png', 
                   "Temps moyen par requête selon le nombre d'abonnés", 
                   "Nombre de followees (Abonnés)")