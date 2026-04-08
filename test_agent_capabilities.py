"""
Validation Script for BISSI Agent - Native Function Calling
This script tests the autonomous reasoning and tool execution of the Gemma 4 agent.
"""
import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent))

from manager import get_manager
import json

def test_autonomous_directory_listing():
    print("\n=== Directory Listing ===")
    manager = get_manager()
    user_query = "Peux-tu me lister les fichiers présents dans le dossier racine de ce projet ?"
    print(f"[User] {user_query}")
    
    try:
        response = manager.process_request(user_query)
        print(response)
    except Exception as e:
        print(f"Error: {e}")

def test_office_integration_reasoning():
    print("\n=== Office (Word) ===")
    manager = get_manager()
    
    test_file = Path("test_validation.docx")
    if not test_file.exists():
        from functions.office.word import create_document
        doc_agent = create_document()
        doc_agent.document.add_paragraph("Ceci est un document de test secret pour BISSI.")
        doc_agent.save(str(test_file))
    
    user_query = f"Lis le contenu du fichier {test_file.name} et résume-moi ce qu'il contient."
    print(f"[User] {user_query}")
    
    try:
        response = manager.process_request(user_query)
        print(response)
    except Exception as e:
        print(f"Error: {e}")

def test_excel_integration():
    print("\n=== Excel ===")
    manager = get_manager()
    
    test_file = Path("test_validation.xlsx")
    if not test_file.exists():
        try:
            from functions.office.excel import write_excel
            import pandas as pd
            data = pd.DataFrame({
                'Produit': ['A', 'B', 'C'],
                'Prix': [100, 200, 300],
                'Quantité': [5, 10, 15]
            })
            write_excel(str(test_file), data)
        except Exception as e:
            print(f"Error creating file: {e}")
            return
    
    user_query = f"Analyse les données du fichier {test_file.name} et donne-moi le total par produit."
    print(f"[User] {user_query}")
    
    try:
        response = manager.process_request(user_query)
        print(response)
    except Exception as e:
        print(f"Error: {e}")


def test_python_code_execution():
    print("\n=== Python Code ===")
    manager = get_manager()
    user_query = "Calcule la somme des nombres de 1 à 100 en utilisant Python et montre le code utilisé."
    print(f"[User] {user_query}")
    
    try:
        response = manager.process_request(user_query)
        print(response)
    except Exception as e:
        print(f"Error: {e}")


def test_multi_step_reasoning():
    print("\n=== Multi-Step Reasoning ===")
    manager = get_manager()
    user_query = """Dans le dossier racine de ce projet:
    1. Liste tous les fichiers Python (.py)
    2. Compte combien il y en a
    3. Trouve le plus gros fichier en taille
    4. Résume ces informations"""
    print(f"[User] {user_query}")
    
    try:
        response = manager.process_request(user_query)
        print(response)
    except Exception as e:
        print(f"Error: {e}")


def test_memory_conversation():
    print("\n=== Conversation Memory ===")
    manager = get_manager()
    
    query1 = "Mon nom est Samuel et je travaille sur un projet d'IA éducative."
    print(f"[User] {query1}")
    manager.process_request(query1)
    
    query2 = "Quel est mon nom et sur quel projet travaille-je ?"
    print(f"[User] {query2}")
    
    try:
        response2 = manager.process_request(query2)
        print(response2)
    except Exception as e:
        print(f"Error: {e}")


def test_system_info_retrieval():
    print("\n=== System Info ===")
    manager = get_manager()
    user_query = "Quelle est la version de Python utilisée et quel est le répertoire de travail actuel ?"
    print(f"[User] {user_query}")
    
    try:
        response = manager.process_request(user_query)
        print(response)
    except Exception as e:
        print(f"Error: {e}")


def test_file_content_analysis():
    print("\n=== File Analysis (README) ===")
    manager = get_manager()
    
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("README.md not found")
        return
    
    user_query = "Lis le fichier README.md et explique en 2-3 phrases ce que fait ce projet BISSI."
    print(f"[User] {user_query}")
    
    try:
        response = manager.process_request(user_query)
        print(response)
    except Exception as e:
        print(f"Error: {e}")


def run_all_tests():
    """Run all tests and display model responses."""
    tests = [
        test_autonomous_directory_listing,
        test_office_integration_reasoning,
        test_excel_integration,
        test_python_code_execution,
        test_multi_step_reasoning,
        test_memory_conversation,
        test_system_info_retrieval,
        test_file_content_analysis,
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    run_all_tests()
