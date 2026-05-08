# Tests des Capacités Agentiques de BISSI

Cette suite de tests valide les capacités d'agent autonome de BISSI, incluant :

## 🎯 Domaines Testés

### 1. **Tool-Calling (Appel d'outils)**
- Initialisation correcte de l'agent
- Enregistrement des outils disponibles
- Structure de résultats cohérente (`ToolResult`)
- Gestion des erreurs d'exécution

### 2. **Chaînage d'Outils (Tool Chaining)**
- Parsing de réponses single tool-call
- Gestion de multiples appels séquentiels
- Maintien du contexte entre appels

### 3. **Gestion d'Erreurs**
- Validation des noms d'outils invalides
- Gestion d'erreurs d'exécution
- Résilience aux réponses malformées

### 4. **Gestion du Contexte**
- Initialisation du ContextManager
- Stockage des conversations
- Gestion du vecteur store (embeddings)

### 5. **Capacités Principales**

#### Opérations Fichiers
- Lecture/écriture de fichiers texte
- Édition de fichiers
- Recherche de fichiers

#### Traitement de Données
- Lecture/écriture Excel
- Exécution de code Python
- Analyse et transformation

#### Documents
- Traitement Word (.docx)
- Traitement PowerPoint (.pptx)
- Lecture PDF

#### Recherche
- Recherche par nom de fichier
- Recherche par contenu
- Listing de répertoires

### 6. **Fiabilité du Moteur**
- Health checks
- Vérification de disponibilité du modèle
- Configuration personnalisée

### 7. **Scénarios Réalistes**
- Recherche et lecture de fichiers
- Analyse de données (Excel → Python → Excel)
- Génération de documents
- Analyse de code

## 📋 Tests Couverts

```
TestAgentToolCalling (4 tests)
├─ test_agent_initialization
├─ test_agent_has_core_tools
├─ test_tool_result_structure
└─ test_tool_result_with_error

TestAgentChaining (2 tests)
├─ test_single_tool_call_response_parsing
└─ test_multiple_tool_calls_in_sequence

TestAgentErrorHandling (3 tests)
├─ test_handles_invalid_tool_name
├─ test_handles_tool_execution_failure
└─ test_handles_malformed_response

TestAgentContextManagement (3 tests)
├─ test_context_manager_initialization
├─ test_conversation_store_initialization
└─ test_vector_store_initialization

TestAgentCapabilities (5 tests)
├─ test_read_write_workflow
├─ test_search_capability
├─ test_data_processing_capability
├─ test_code_execution_capability
└─ test_document_processing_capability

TestEngineReliability (3 tests)
├─ test_engine_health_check
├─ test_engine_model_availability
└─ test_engine_initialization_with_custom_settings

TestAgentToolIntegration (2 tests)
├─ test_agent_tool_registry
└─ test_tool_result_consistency

TestAgentScenarios (4 tests)
├─ test_scenario_search_and_read
├─ test_scenario_data_analysis
├─ test_scenario_document_generation
└─ test_scenario_code_analysis

Total: 26 tests ✅
```

## 🚀 Exécution

### Installation (première fois)
```bash
cd bissi
source .venv/bin/activate
pip install pytest
```

### Lancer tous les tests
```bash
source .venv/bin/activate
python -m pytest tests/test_agentic_capabilities.py -v
```

### Lancer une classe de tests
```bash
python -m pytest tests/test_agentic_capabilities.py::TestAgentCapabilities -v
```

### Lancer un test spécifique
```bash
python -m pytest tests/test_agentic_capabilities.py::TestAgentCapabilities::test_code_execution_capability -v
```

### Avec couverture de code
```bash
pip install pytest-cov
python -m pytest tests/test_agentic_capabilities.py --cov=core --cov-report=html
```

### Mode verbeux avec détails
```bash
python -m pytest tests/test_agentic_capabilities.py -vv --tb=long
```

## 🏗️ Structure des Tests

### Mocking & Isolation
Les tests utilisent des mocks pour isoler l'agent du moteur LLM réel :
```python
with patch.object(BissiEngine, '__init__', return_value=None):
    with patch.object(BissiEngine, 'health_check', return_value=True):
        agent = BissiAgent()
```

### Fixtures
```python
@pytest.fixture
def mock_engine():
    """Fournir un moteur mocké."""
    ...

@pytest.fixture
def agent_with_mock_engine(mock_engine):
    """Fournir un agent avec moteur mocké."""
    ...
```

### Assertions
Les tests valident :
- Présence des outils attendus
- Structure correcte des résultats
- Gestion cohérente des erreurs
- Intégrité du contexte

## 📊 Résultats

```
============ 26 passed in 3.99s ============
✅ Tous les tests passent
✅ Agent initialisé correctement
✅ 30+ outils disponibles
✅ Gestion d'erreurs robuste
✅ Contexte maintenu
✅ Moteur fiable
```

## 🔧 Maintenance

### Ajouter un nouveau test
1. Créer une classe `Test*` dans le fichier
2. Ajouter des méthodes `test_*`
3. Utiliser les mocks existants
4. Exécuter : `pytest tests/test_agentic_capabilities.py -v`

### Tester un nouveau tool
```python
def test_new_tool_capability(self):
    """Test agent can use new_tool."""
    with patch.object(BissiEngine, '__init__', return_value=None):
        with patch.object(BissiEngine, 'health_check', return_value=True):
            agent = BissiAgent()
            assert "new_tool" in agent.available_functions
```

## 📚 Documentation

Pour plus de détails sur :
- **Agent** : voir `core/agent.py`
- **Types** : voir `core/types.py`
- **Engine** : voir `core/engine.py`
- **Tools** : voir `functions/`

## ✨ Bénéfices

✅ **Fiabilité** : Valide que tous les mécanismes d'agent fonctionnent  
✅ **Régression** : Détecte les cassures lors de changements  
✅ **Documentation** : Démontre comment utiliser l'agent  
✅ **Confiance** : Confirme que les capacités agentiques sont intactes  
✅ **CI/CD** : Peut être intégré dans les pipelines d'automatisation  

---

*Dernière mise à jour : 2026-05-07*
