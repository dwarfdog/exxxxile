import subprocess

def run_sp_battle(command):
    """
    Lance sp_battle en exécutant une commande shell.

    :param command: La commande shell à exécuter.
    """
    try:
        print(f"Lancement de sp_battle avec la commande : {command}")
        # Exécution de la commande, le processus reste actif
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du lancement de sp_battle : {command}\n{e}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")

if __name__ == "__main__":
    # Commande pour démarrer sp_battle
    command = "sudo python3 manage.py sp_battle"

    # Lancement de sp_battle
    run_sp_battle(command)
