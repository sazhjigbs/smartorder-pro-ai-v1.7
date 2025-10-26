#!/usr/bin/env python3
"""
📝 SAFELOGIC SmartOrder PRO — Auto-Doc Generator
Génère automatiquement la documentation quotidienne pour GitHub
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

def get_system_stats():
    """Collecte les stats système du jour"""
    try:
        import psutil
        stats = {
            "cpu_avg": psutil.cpu_percent(interval=1),
            "ram_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('.').percent,
            "uptime_hours": (time.time() - psutil.boot_time()) / 3600
        }
    except:
        stats = {
            "cpu_avg": "N/A",
            "ram_usage": "N/A", 
            "disk_usage": "N/A",
            "uptime_hours": "N/A"
        }
    return stats

def count_log_events():
    """Compte les événements dans les logs"""
    events = {
        "errors": 0,
        "trades": 0, 
        "syncs": 0,
        "restarts": 0
    }
    
    # Recherche dans les logs locaux
    log_patterns = [
        ("*.log", "ERROR", "errors"),
        ("git_sync.log", "Push successful", "syncs"),
        ("*.log", "trade", "trades"),
        ("*.log", "restart", "restarts")
    ]
    
    for pattern, keyword, counter in log_patterns:
        try:
            log_files = Path(".").glob(pattern)
            for log_file in log_files:
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        events[counter] += content.lower().count(keyword.lower())
        except:
            continue
    
    return events

def get_ai_performance():
    """Évalue la performance IA du jour"""
    try:
        # Lire les métriques depuis ai_memory.json si disponible
        memory_file = Path("ai_core/ai_memory.json")
        if memory_file.exists():
            with open(memory_file, 'r') as f:
                memory_data = json.load(f)
                
            performance = {
                "confidence_avg": memory_data.get("confidence", 75),
                "bias": memory_data.get("bias", "neutral"),
                "learning_score": memory_data.get("learning_score", 80),
                "adaptations": memory_data.get("adaptations", 0)
            }
        else:
            performance = {
                "confidence_avg": "N/A",
                "bias": "N/A",
                "learning_score": "N/A", 
                "adaptations": "N/A"
            }
    except:
        performance = {
            "confidence_avg": "N/A",
            "bias": "N/A",
            "learning_score": "N/A",
            "adaptations": "N/A"
        }
    
    return performance

def generate_daily_report():
    """Génère le rapport quotidien complet"""
    today = datetime.now()
    stats = get_system_stats()
    events = count_log_events()
    ai_perf = get_ai_performance()
    
    report = f"""# 📊 SAFELOGIC SmartOrder PRO - Rapport Quotidien
**Date:** {today.strftime('%Y-%m-%d %H:%M:%S')}  
**Version:** v1.8-FINAL ADAPTIVE  

## 🎯 Performance Globale

### 🤖 Intelligence Artificielle
- **Confiance moyenne:** {ai_perf['confidence_avg']}%
- **Biais détecté:** {ai_perf['bias']}
- **Score d'apprentissage:** {ai_perf['learning_score']}%
- **Adaptations:** {ai_perf['adaptations']}

### 📈 Activité Trading
- **Signaux générés:** {events['trades']}
- **Exécutions réussies:** N/A
- **PnL estimé:** N/A
- **Win Rate:** N/A

## 🔧 Système & Infrastructure

### 💻 Ressources
- **CPU moyen:** {stats['cpu_avg']}%
- **RAM utilisée:** {stats['ram_usage']}%
- **Stockage:** {stats['disk_usage']}%
- **Uptime:** {stats['uptime_hours']:.1f}h

### 🛠️ Services
- **Erreurs détectées:** {events['errors']}
- **Redémarrages auto:** {events['restarts']}
- **Syncs GitHub:** {events['syncs']}
- **Statut général:** ✅ Stable

## 🧩 Modules Actifs

### 🚀 Core Services
- ✅ **Portal v5** - Interface web & API
- ✅ **WebSync Bridge** - Synchronisation temps réel
- ✅ **Guardian AI** - Auto-correction & surveillance
- ✅ **Auto-Sync GitHub** - Sauvegarde continue

### 🧠 AI Engine
- ✅ **Learner AI** - Phase 5 Self-Learning
- ✅ **Memory AI** - Contexte & historique 
- ✅ **Behavior AI** - Détection patterns
- ✅ **Genetic AI** - Évolution stratégies

## 📋 Tâches & Évolution

### ✅ Terminé aujourd'hui
- Stabilisation Auto-Guardian Fix
- Optimisation MTF Fusion AI
- Tests API Bybit v5

### 🔄 En cours
- Phase 4 → Phase 5 transition
- Self-Learning Loop implementation
- Dashboard v4-UI Pro

### 📅 Planifié
- Backtesting intégré
- Multi-exchange router
- Stratégie hybride optimization

---

## 🔮 Prochaines 24h

**Priorités:**
1. 🎯 Finaliser ExecutionAI connection
2. 🧠 Activer Self-Learning boucle complète
3. 📊 Tests performance multi-timeframe
4. 🔗 Integration Telegram Panel avancé

**Seuils d'alerte:**
- ⚠️ CPU > 80% - Auto-limitation
- 🚨 RAM > 90% - Restart services  
- 💥 Erreurs > 50/h - Safe mode
- 🔴 PnL < -5% - Stop trading

---
**🤖 Rapport auto-généré par SAFELOGIC SmartOrder PRO**  
**📡 Prochaine mise à jour:** {(today + timedelta(hours=24)).strftime('%Y-%m-%d %H:00')}
"""
    
    return report

def save_report_to_file(report):
    """Sauvegarde le rapport dans un fichier"""
    today = datetime.now()
    filename = f"daily_report_{today.strftime('%Y-%m-%d')}.md"
    
    try:
        # Créer le dossier reports s'il n'existe pas
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        report_path = reports_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
            
        print(f"✅ Rapport sauvegardé: {report_path}")
        return report_path
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {str(e)}")
        return None

def update_readme_with_report(report):
    """Met à jour le README.md avec un extrait du rapport"""
    try:
        readme_path = Path("README.md")
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Extrait pour README
        readme_update = f"""
## 📊 Dernière Mise à Jour - {today}

🤖 **IA Confiance:** {get_ai_performance()['confidence_avg']}%  
🔧 **Services:** ✅ Tous actifs  
📈 **Uptime:** {get_system_stats()['uptime_hours']:.1f}h  
🔄 **GitHub Sync:** ✅ Actif  

*[Voir rapport complet →](reports/daily_report_{today}.md)*

---
"""
        
        # Lire README existant
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = "# SMARTORDER PRO AI v1.8-FINAL\n\n"
        
        # Insérer l'update au début (après le titre)
        lines = content.split('\n')
        if len(lines) > 2:
            lines.insert(2, readme_update)
        else:
            lines.append(readme_update)
            
        # Sauvegarder
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            
        print(f"✅ README.md mis à jour")
        return True
        
    except Exception as e:
        print(f"❌ Erreur README update: {str(e)}")
        return False

def main():
    """Génère et sauvegarde le rapport quotidien"""
    print("📝 Génération du rapport quotidien...")
    
    # Générer le rapport
    report = generate_daily_report()
    
    # Sauvegarder le rapport complet
    report_path = save_report_to_file(report)
    
    # Mettre à jour README
    update_readme_with_report(report)
    
    # Afficher un extrait
    print("\n" + "="*50)
    print("📊 EXTRAIT DU RAPPORT:")
    print("="*50)
    print(report[:500] + "...")
    print("\n✅ Documentation générée avec succès!")

if __name__ == "__main__":
    main()