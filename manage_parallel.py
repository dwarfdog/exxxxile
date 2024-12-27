import subprocess
import threading
import time

# Fonction pour lancer une commande en boucle infinie
def run_command(command):
    while True:
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erreur avec la commande : {command}\n{e}")
        time.sleep(1)  # Pause d'une seconde avant la relance en cas d'erreur

# Fonction pour exécuter `update_player` toutes les minutes
def periodic_command(command, interval):
    while True:
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erreur avec la commande périodique : {command}\n{e}")
        time.sleep(interval)

if __name__ == "__main__":
    # Commandes à exécuter
    commands = [
        "sudo python3 manage.py runserver 0.0.0.0:8000",
        "sudo python3 manage.py runserver sp_process_all",
        "sudo python3 manage.py sp_battle",
        "sudo python3 manage.py sp_events",
    ]

    # Démarrage des threads pour chaque commande persistante
    threads = []
    for cmd in commands:
        thread = threading.Thread(target=run_command, args=(cmd,))
        thread.daemon = True  # Permet de quitter proprement tous les threads à l'arrêt du script
        thread.start()
        threads.append(thread)

    # Démarrage du thread pour la commande périodique
    periodic_thread = threading.Thread(target=periodic_command, args=("sudo python3 manage.py update_player", 60))
    periodic_thread.daemon = True
    periodic_thread.start()

    # Attente des threads principaux (facultatif pour empêcher la fin prématurée)
    for thread in threads:
        thread.join()
