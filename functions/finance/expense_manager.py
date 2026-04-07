"""Expense manager integration for BISSI.

Interfaces with the existing GestionnaireDeD-penses application.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Expense:
    """Single expense record."""
    date: str
    libelle: str
    montant: float
    categorie: str
    id: str


class ExpenseManager:
    """Expense tracker integration."""
    
    CATEGORIES = [
        'Alimentation', 'Transport', 'Logement', 'Santé',
        'Loisirs', 'Shopping', 'Éducation', 'Travail',
        'Impôts', 'Général'
    ]
    
    def __init__(self, data_path: Optional[Union[str, Path]] = None):
        """Initialize expense manager."""
        if data_path:
            self.data_path = Path(data_path)
        else:
            self.data_path = Path('~/Dev/GestionnaireDeD-penses/depenses.json').expanduser()
        
        self.config_path = self.data_path.parent / 'config.json'
        self.expenses: List[Expense] = []
        self.budget: float = 0
        self.user_name: str = "User"
        
        self._load_data()
    
    def _load_data(self):
        """Load expenses and config."""
        if self.data_path.exists():
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.expenses = [
                    Expense(
                        date=item['date'],
                        libelle=item['libelle'],
                        montant=item['montant'],
                        categorie=item['categorie'],
                        id=item['id']
                    )
                    for item in data
                ]
        
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.budget = config.get('budget', 0)
                self.user_name = config.get('nom', 'User')
    
    def _save_expenses(self):
        """Save expenses to file."""
        data = [
            {
                'date': e.date,
                'libelle': e.libelle,
                'montant': e.montant,
                'categorie': e.categorie,
                'id': e.id
            }
            for e in self.expenses
        ]
        
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_expense(self, libelle: str, montant: float, categorie: str, date: Optional[str] = None) -> Expense:
        """Add new expense."""
        if categorie not in self.CATEGORIES:
            categorie = 'Général'
        
        if date is None:
            date = datetime.now().strftime('%d/%m/%Y')
        
        expense_id = f"{date}_{libelle}_{montant}"
        
        expense = Expense(
            date=date,
            libelle=libelle,
            montant=montant,
            categorie=categorie,
            id=expense_id
        )
        
        self.expenses.append(expense)
        self._save_expenses()
        
        return expense
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get overall budget status."""
        spent = sum(e.montant for e in self.expenses)
        remaining = self.budget - spent
        
        return {
            'user': self.user_name,
            'budget': self.budget,
            'spent': spent,
            'remaining': remaining,
            'percentage_used': (spent / self.budget * 100) if self.budget > 0 else 0,
            'expense_count': len(self.expenses)
        }
    
    def generate_report(self) -> str:
        """Generate expense report."""
        status = self.get_budget_status()
        
        lines = [
            "📊 RAPPORT DE DÉPENSES",
            f"Utilisateur: {status['user']}",
            "",
            "💰 BUDGET",
            f"  Budget: {status['budget']:,.0f} FCFA",
            f"  Dépensé: {status['spent']:,.0f} FCFA ({status['percentage_used']:.1f}%)",
            f"  Restant: {status['remaining']:,.0f} FCFA",
            "",
            f"Nombre de dépenses: {status['expense_count']}"
        ]
        
        return '\n'.join(lines)


def quick_add(libelle: str, montant: float, categorie: str = 'Général') -> Expense:
    """Quick add expense."""
    manager = ExpenseManager()
    return manager.add_expense(libelle, montant, categorie)
