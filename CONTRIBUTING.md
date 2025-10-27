# 🤝 Guide de Contribution - SmartOrder PRO

Merci de votre intérêt pour contribuer à SmartOrder PRO ! Ce document vous guide à travers le processus de contribution.

---

## 📋 Table des Matières

- [Code de Conduite](#code-de-conduite)
- [Comment Contribuer](#comment-contribuer)
- [Standards de Code](#standards-de-code)
- [Processus de Pull Request](#processus-de-pull-request)
- [Rapporter des Bugs](#rapporter-des-bugs)
- [Proposer des Fonctionnalités](#proposer-des-fonctionnalités)
- [Configuration de l'Environnement](#configuration-de-lenvironnement)
- [Tests](#tests)
- [Documentation](#documentation)

---

## 📜 Code de Conduite

### Notre Engagement

Nous nous engageons à faire de la participation à ce projet une expérience sans harcèlement pour tous, indépendamment de l'âge, de la taille corporelle, du handicap, de l'ethnicité, de l'identité et de l'expression de genre, du niveau d'expérience, de la nationalité, de l'apparence personnelle, de la race, de la religion ou de l'identité et de l'orientation sexuelles.

### Nos Standards

**Comportements encouragés:**
- Utiliser un langage accueillant et inclusif
- Respecter les points de vue et expériences différents
- Accepter gracieusement les critiques constructives
- Se concentrer sur ce qui est le mieux pour la communauté

**Comportements inacceptables:**
- Langage ou images à connotation sexuelle
- Trolling, commentaires insultants/dérogatoires, attaques personnelles
- Harcèlement public ou privé
- Publication d'informations privées sans permission

---

## 🚀 Comment Contribuer

### Types de Contributions

Nous acceptons plusieurs types de contributions:

1. **Corrections de bugs** 🐛
2. **Nouvelles fonctionnalités** ✨
3. **Améliorations de documentation** 📚
4. **Optimisations de performance** ⚡
5. **Tests supplémentaires** 🧪
6. **Traductions** 🌍

### Workflow Général

1. **Fork** le repository
2. **Clone** votre fork localement
3. **Créez une branche** pour votre contribution
4. **Committez** vos changements
5. **Testez** votre code
6. **Push** vers votre fork
7. **Créez une Pull Request**

---

## 💻 Standards de Code

### Style Python

Nous suivons **PEP 8** avec quelques adaptations:

```python
# ✅ BON
def calculate_position_size(account_balance: float, risk_percent: float) -> float:
    """
    Calculate position size based on account balance and risk.
    
    Args:
        account_balance: Total account balance in USD
        risk_percent: Risk percentage (0-100)
        
    Returns:
        Position size in USD
    """
    return account_balance * (risk_percent / 100)

# ❌ MAUVAIS
def calc_pos(bal,risk):
    return bal*(risk/100)
```

### Règles Importantes

1. **Indentation**: 4 espaces (pas de tabs)
2. **Longueur de ligne**: Maximum 100 caractères
3. **Imports**: Groupés et triés alphabétiquement
4. **Docstrings**: Format Google pour toutes les fonctions publiques
5. **Type hints**: Obligatoires pour toutes les fonctions
6. **Nommage**:
   - Classes: `PascalCase`
   - Fonctions/Variables: `snake_case`
   - Constantes: `UPPER_SNAKE_CASE`

### Structure des Imports

```python
# Standard library
import os
import sys
from datetime import datetime

# Third-party
import requests
from flask import Flask

# Local modules
from core.exchange_router import ExchangeRouter
from utils.logger import get_logger
```

### Exemples de Bonnes Pratiques

```python
# ✅ BON - Type hints, docstring, error handling
def place_order(
    symbol: str,
    side: str,
    quantity: float,
    price: Optional[float] = None
) -> Dict[str, Any]:
    """
    Place an order on the exchange.
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        side: Order side ("BUY" or "SELL")
        quantity: Order quantity
        price: Limit price (None for market order)
        
    Returns:
        Order details dictionary
        
    Raises:
        OrderPlacementError: If order fails
    """
    try:
        # Implementation
        return {"order_id": "12345", "status": "filled"}
    except Exception as e:
        logger.error(f"Order placement failed: {e}")
        raise OrderPlacementError(str(e))

# ❌ MAUVAIS - Pas de types, pas de docs, pas de gestion d'erreur
def place_order(sym, side, qty, price=None):
    return {"order_id": "12345"}
```

---

## 🔀 Processus de Pull Request

### Avant de Soumettre

1. **Vérifiez les issues existantes** pour éviter les doublons
2. **Testez votre code** localement
3. **Mettez à jour la documentation** si nécessaire
4. **Ajoutez des tests** pour les nouvelles fonctionnalités
5. **Assurez-vous que tous les tests passent**

### Créer une Pull Request

1. **Titre descriptif**:
   ```
   ✅ BON: "Add support for Kraken exchange connector"
   ❌ MAUVAIS: "Fix bug"
   ```

2. **Description détaillée**:
   ```markdown
   ## Description
   Add Kraken exchange connector with full API support
   
   ## Type de changement
   - [ ] Bug fix
   - [x] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Tests effectués
   - [x] Unit tests
   - [x] Integration tests
   - [x] Manual testing on testnet
   
   ## Checklist
   - [x] Code follows project style
   - [x] Self-reviewed code
   - [x] Commented complex code
   - [x] Updated documentation
   - [x] No new warnings
   - [x] Added tests
   - [x] All tests pass
   ```

3. **Liez les issues**: `Fixes #123` ou `Closes #456`

### Review Process

1. Un mainteneur reviewera votre PR sous 48h
2. Des changements peuvent être demandés
3. Une fois approuvée, votre PR sera mergée
4. Vous serez ajouté aux contributeurs ! 🎉

---

## 🐛 Rapporter des Bugs

### Avant de Rapporter

1. **Vérifiez les issues existantes**
2. **Testez avec la dernière version**
3. **Essayez de reproduire** le bug

### Template de Bug Report

```markdown
**Description du bug**
Description claire et concise du bug.

**Étapes pour reproduire**
1. Allez à '...'
2. Cliquez sur '...'
3. Scrollez jusqu'à '...'
4. Voyez l'erreur

**Comportement attendu**
Ce qui devrait se passer.

**Comportement actuel**
Ce qui se passe réellement.

**Screenshots**
Si applicable, ajoutez des screenshots.

**Environnement:**
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.9.7]
- Version du bot: [e.g., 1.9-FINAL]

**Logs**
```
Coller les logs pertinents ici
```

**Contexte additionnel**
Tout autre contexte utile.
```

---

## 💡 Proposer des Fonctionnalités

### Template de Feature Request

```markdown
**La fonctionnalité est-elle liée à un problème?**
Description claire du problème. Ex: "Je suis frustré quand [...]"

**Solution proposée**
Description de la solution souhaitée.

**Alternatives considérées**
Autres solutions envisagées.

**Contexte additionnel**
Screenshots, mockups, liens, etc.

**Priorité**
- [ ] Basse
- [ ] Moyenne
- [ ] Haute
- [ ] Critique
```

---

## 🛠️ Configuration de l'Environnement

### Installation Développeur

```bash
# 1. Fork et clone
git clone https://github.com/VOTRE_USERNAME/smartorder-pro-ai.git
cd smartorder-pro-ai-v1.7

# 2. Setup environnement
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Si disponible

# 4. Setup pre-commit hooks
pre-commit install  # Si configuré

# 5. Configuration
cp .env.example .env
# Éditer .env avec vos clés de test

# 6. Setup base de données et chiffrement
python security/database_encryption.py setup
```

### Structure des Branches

- `main`: Production, toujours stable
- `develop`: Développement actif
- `feature/nom-feature`: Nouvelles fonctionnalités
- `bugfix/nom-bug`: Corrections de bugs
- `hotfix/nom-hotfix`: Corrections urgentes en production

### Nommer vos Branches

```bash
# ✅ BON
git checkout -b feature/kraken-connector
git checkout -b bugfix/order-placement-error
git checkout -b docs/api-documentation

# ❌ MAUVAIS
git checkout -b my-changes
git checkout -b fix
```

---

## 🧪 Tests

### Lancer les Tests

```bash
# Tous les tests
pytest tests/

# Tests spécifiques
pytest tests/test_bybit_connector.py -v

# Avec coverage
pytest --cov=. tests/

# Tests E2E (nécessite testnet)
pytest tests/test_e2e.py --testnet
```

### Écrire des Tests

```python
# tests/test_new_feature.py
import pytest
from core.new_feature import NewFeature

class TestNewFeature:
    """Test suite for NewFeature class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.feature = NewFeature()
    
    def test_basic_functionality(self):
        """Test basic functionality works as expected."""
        result = self.feature.process()
        assert result == expected_value
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            self.feature.process(invalid_input)
    
    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 4),
        (3, 6)
    ])
    def test_multiple_cases(self, input, expected):
        """Test multiple input/output cases."""
        assert self.feature.double(input) == expected
```

### Coverage Requis

- **Nouveau code**: Minimum 80% de coverage
- **Code critique** (trading, security): Minimum 90% de coverage

---

## 📚 Documentation

### Documentation Code

```python
def complex_function(param1: str, param2: int = 10) -> Dict[str, Any]:
    """
    Une ligne de description courte.
    
    Description détaillée sur plusieurs lignes si nécessaire.
    Expliquez le comportement, les cas limites, etc.
    
    Args:
        param1: Description du premier paramètre
        param2: Description du second paramètre (default: 10)
        
    Returns:
        Description du retour avec structure si dict/list
        
    Raises:
        ValueError: Si param1 est vide
        ConnectionError: Si connexion échoue
        
    Example:
        >>> result = complex_function("test", 20)
        >>> print(result)
        {'status': 'success'}
        
    Note:
        Information importante sur l'utilisation
        
    Warning:
        Avertissement sur comportement dangereux
    """
    pass
```

### Documentation Markdown

- Utilisez des titres clairs
- Ajoutez des exemples de code
- Incluez des screenshots si pertinent
- Liens vers documentation externe si nécessaire

---

## 🎯 Checklist Contributeur

Avant de soumettre votre PR:

- [ ] Code suit les standards du projet
- [ ] Tests ajoutés et passent tous
- [ ] Documentation mise à jour
- [ ] CHANGELOG.md mis à jour
- [ ] Pas de warnings/erreurs de linting
- [ ] Commits sont clairs et descriptifs
- [ ] Branche est à jour avec `main`
- [ ] PR description est complète
- [ ] Code a été self-reviewed

---

## 🏆 Reconnaissance

Tous les contributeurs seront:

1. Ajoutés au README.md
2. Mentionnés dans CHANGELOG.md
3. Cités dans les release notes
4. Remerciés publiquement ! 🙏

---

## 📞 Questions?

- **GitHub Discussions**: Pour questions générales
- **GitHub Issues**: Pour bugs/features
- **Email**: support@smartorderpro.com
- **Discord**: [Lien serveur Discord]

---

## 📜 Licence

En contribuant, vous acceptez que vos contributions soient licensées sous la licence MIT du projet.

---

**Merci de contribuer à SmartOrder PRO ! 🚀**

*Ensemble, construisons le meilleur bot de trading crypto open-source !*

---

*Document mis à jour: 2024-10-27*
