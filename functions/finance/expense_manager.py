"""Expense manager integration for BISSI.

Interfaces with the existing GestionnaireDeD-penses application.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from utils.helpers import expand_path, load_json, save_json


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
            self.data_path = expand_path('~/Dev/GestionnaireDeD-penses/depenses.json')
        
        self.config_path = self.data_path.parent / 'config.json'
        self.expenses: List[Expense] = []
        self.budget: float = 0
        self.user_name: str = "User"
        
        self._load_data()
    
    def _load_data(self):
        """Load expenses and config."""
        data = load_json(self.data_path)
        if data:
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
        
        config = load_json(self.config_path)
        if config:
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
        save_json(data, self.data_path)
    
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
