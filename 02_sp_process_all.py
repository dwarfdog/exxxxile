import subprocess

def run_sp_process_all(command):
    """
    Lance sp_process_all en exécutant une commande shell.

    :param command: La commande shell à exécuter.
    """
    try:
        print(f"Lancement de sp_process_all avec la commande : {command}")
        # Exécution de la commande, le processus reste actif
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du lancement de sp_process_all : {command}\n{e}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")

if __name__ == "__main__":
    # Commande pour démarrer sp_process_all
    command = "sudo python3 manage.py sp_process_all"

    # Lancement de sp_process_all
    sp_process_all(command)
