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
periodic_interval = 30  # Intervalle en secondes

# Liste pour stocker les processus
processes = []

def launch_scripts():
    for command in commands:
        try:
            print(f"Lancement de : {command}")
            if os.name == 'nt':  # Windows
                raise EnvironmentError("Ce script est conçu pour être utilisé sous Linux avec GNOME Terminal.")
            else:  # Unix/Linux/MacOS
                process = subprocess.Popen(
                    ["gnome-terminal", "--", "bash", "-c", f"{command}"],
                    start_new_session=True
                )
                processes.append(process)

            time.sleep(0.5)  # Attendre 0,5 secondes avant de lancer le prochain script
        except Exception as e:
            print(f"Erreur lors du lancement de la commande : {command}\n{e}")

def run_periodic_command(command, interval):
    """
    Exécute une commande périodiquement à un intervalle donné.
    :param command: La commande shell à exécuter.
    :param interval: Intervalle en secondes entre chaque exécution.
    """
    while True:
        try:
            print(f"Exécution de la commande : {command}")
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'exécution de la commande : {command}\n{e}")
        except Exception as e:
            print(f"Erreur inattendue : {e}")
        finally:
            print(f"Attente de {interval} secondes avant la prochaine exécution.")
            time.sleep(interval)

# Gestionnaire de signaux pour terminer tous les processus
def terminate_processes(signal_received, frame):
    print("Signal d'interruption reçu, fermeture des processus...")
    for process in processes:
        try:
            process.terminate()
            process.wait()
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

    # Lancement de la commande périodique
    run_periodic_command(periodic_command, periodic_interval)
