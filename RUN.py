import os
import time
import subprocess

# Définir les commandes pour chaque script à lancer une seule fois
single_run_commands = [
    "python3 01_run.py",  # Depuis 01_run.py
    "python3 02_sp_process_all.py",  # Depuis 02_sp_process_all.py
    "python3 04_sp_events.py",  # Depuis 04_sp_events.py
    "python3 03_sp_battle.py"  # Depuis 03_sp_battle.py
]

# Commande pour le script à exécuter périodiquement
periodic_command = "python3 05_update_player.py"
periodic_interval = 60  # Intervalle en secondes

def launch_single_run_scripts():
    processes = []
    for command in single_run_commands:
        try:
            print(f"Lancement de : {command}")
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append(process)
            time.sleep(2)  # Attendre 2 secondes avant de lancer le prochain script
        except Exception as e:
            print(f"Erreur lors du lancement de la commande : {command}\n{e}")

    # Afficher les sorties des processus
    for process in processes:
        stdout, stderr = process.communicate()
        if stdout:
            print(stdout.decode())
        if stderr:
            print(stderr.decode())

def launch_periodic_script():
    try:
        while True:
            print(f"Exécution périodique de : {periodic_command}")
            process = subprocess.Popen(periodic_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stdout:
                print(stdout.decode())
            if stderr:
                print(stderr.decode())
            time.sleep(periodic_interval)
    except KeyboardInterrupt:
        print("Arrêt de l'exécution périodique.")

if __name__ == "__main__":
    # Vérification des privilèges administrateurs (Linux uniquement)
    if os.name != 'nt' and os.geteuid() != 0:
        print("Ce script doit être exécuté avec les droits administrateur.")
        exit(1)

    # Lancer les scripts exécutés une seule fois
    launch_single_run_scripts()

    # Lancer le script périodique
    launch_periodic_script()
