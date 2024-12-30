import os
import time
import subprocess
import signal

# Commandes pour les scripts exécutés une seule fois
commands = [
    "sudo python3 ./manage.py runserver 0.0.0.0:8000",  # Lancement du serveur
    "sudo python3 ./manage.py sp_process_all",          # Process all
    "sudo python3 ./manage.py sp_events",              # Events
    "sudo python3 ./manage.py sp_battle"               # Battle
]

# Commande pour le script périodique
periodic_command = "sudo python3 ./manage.py update_player"
periodic_interval = 60  # Intervalle en secondes

# Liste pour stocker les processus
processes = []

def launch_scripts():
    for command in commands:
        try:
            print(f"Lancement de : {command}")
            if os.name == 'nt':  # Windows
                raise EnvironmentError("Ce script est conçu pour être utilisé sous Linux avec GNOME Terminal.")
            else:  # Unix/Linux/MacOS
                process = subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"{command}"], start_new_session=True)
                processes.append(process)

            time.sleep(2)  # Attendre 2 secondes avant de lancer le prochain script
        except Exception as e:
            print(f"Erreur lors du lancement de la commande : {command}\n{e}")

def launch_periodic_script():
    try:
        while True:
            print(f"Exécution périodique de : {periodic_command}")
            if os.name == 'nt':  # Windows
                raise EnvironmentError("Ce script est conçu pour être utilisé sous Linux avec GNOME Terminal.")
            else:  # Unix/Linux/MacOS
                process = subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"{periodic_command}"], start_new_session=True)
                processes.append(process)

            time.sleep(periodic_interval)
    except KeyboardInterrupt:
        print("Arrêt de l'exécution périodique.")

# Gestionnaire de signaux pour terminer tous les processus
def terminate_processes(signal_received, frame):
    print("Signal d'interruption reçu, fermeture des processus...")
    for process in processes:
        try:
            process.terminate()
        except Exception as e:
            print(f"Erreur lors de la fermeture du processus : {e}")
    exit(0)

if __name__ == "__main__":
    # Vérification des privilèges administrateurs (Linux uniquement)
    if os.name != 'nt' and os.geteuid() != 0:
        print("Ce script doit être exécuté avec les droits administrateur.")
        exit(1)

    # Attacher le gestionnaire de signaux
    signal.signal(signal.SIGINT, terminate_processes)
    signal.signal(signal.SIGTERM, terminate_processes)

    # Lancer les scripts exécutés une seule fois
    launch_scripts()

    # Lancer le script périodique
    launch_periodic_script()
