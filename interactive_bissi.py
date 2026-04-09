import sys
from pathlib import Path

# Ajout du dossier racine au PATH
sys.path.insert(0, str(Path(__file__).parent))

from manager import get_manager
import os

# Couleurs pour le terminal
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

def main():
    manager = get_manager()
    manager.start_conversation("Session de Test Interactive")
    
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print(f"{BLUE}{BOLD}=== BISSI INTERACTIVE SANDBOX (2026) ==={RESET}")
    print(f"{YELLOW}Modèle : {manager.model}{RESET}")
    print(f"{YELLOW}Prêt pour vos commandes. Tapez 'exit' pour quitter.{RESET}\n")

    while True:
        try:
            # Entrée utilisateur
            user_input = input(f"{BOLD}[User] > {RESET}")
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print(f"\n{BLUE}Au revoir, Samuel.{RESET}")
                break
                
            if not user_input.strip():
                continue

            # Traitement par le manager
            # Note: Les logs [Core] s'afficheront automatiquement via manager.py
            print(f"{GREEN}--- Réflexion en cours ---{RESET}")
            response = manager.process_request(user_input)
            
            # Affichage de la réponse finale
            print(f"\n{BLUE}{BOLD}[BISSI]{RESET}")
            print(f"{response}\n")
            print("-" * 40 + "\n")

        except KeyboardInterrupt:
            print(f"\n\n{BLUE}Session interrompue. Au revoir !{RESET}")
            break
        except Exception as e:
            print(f"\n{BOLD}[ERREUR]{RESET} {e}")

if __name__ == "__main__":
    main()
