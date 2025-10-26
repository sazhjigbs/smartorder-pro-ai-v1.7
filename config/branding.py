"""
SmartOrder PRO - Branding Configuration
Identité visuelle et signature
by MAIGA ABOUBACAR

Configuration centralisée pour:
- Signature auteur
- Couleurs premium
- Logos et icônes
- Messages de branding
"""

# ==================== IDENTITÉ ====================

AUTHOR_NAME = "MAIGA ABOUBACAR"
AUTHOR_SIGNATURE = "by MAIGA ABOUBACAR"
COMPANY_NAME = "SmartOrder PRO"
SYSTEM_VERSION = "v2.0 Ultra-Pro"
TAGLINE = "AI Trading System"
COPYRIGHT = f"© 2025 {AUTHOR_NAME}. All rights reserved."

# ==================== COULEURS PREMIUM ====================

COLORS = {
    # Dark theme
    'bg_primary': '#0a0e27',        # Dark blue profond
    'bg_secondary': '#151932',      # Card background
    'bg_tertiary': '#1e2139',       # Hover states
    
    # Accent colors
    'accent_primary': '#00f5ff',    # Cyan électrique
    'accent_secondary': '#667eea',  # Purple
    'accent_gold': '#ffd700',       # Or premium
    'accent_success': '#10b981',    # Green
    'accent_danger': '#ef4444',     # Red
    'accent_warning': '#f59e0b',    # Orange
    
    # Text
    'text_primary': '#ffffff',
    'text_secondary': '#8b93b0',
    'text_muted': '#5a6178',
    
    # Gradients
    'gradient_primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'gradient_cyber': 'linear-gradient(135deg, #00f5ff 0%, #00b4d8 100%)',
    'gradient_gold': 'linear-gradient(135deg, #f7971e 0%, #ffd200 100%)',
    'gradient_success': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
}

# ==================== EMOJIS & ICONS ====================

ICONS = {
    'robot': '🤖',
    'rocket': '🚀',
    'fire': '🔥',
    'star': '⭐',
    'trophy': '🏆',
    'chart_up': '📈',
    'chart_down': '📉',
    'money': '💰',
    'lightning': '⚡',
    'shield': '🛡️',
    'diamond': '💎',
    'warning': '⚠️',
    'check': '✅',
    'cross': '❌',
    'info': 'ℹ️',
    'bell': '🔔',
    'lock': '🔐',
    'key': '🔑',
    'settings': '⚙️',
    'brain': '🧠',
}

# ==================== MESSAGES DE BRANDING ====================

WELCOME_MESSAGE = f"""
╔══════════════════════════════════════╗
║   {ICONS['robot']} SmartOrder PRO {SYSTEM_VERSION}    ║
║                                      ║
║   {ICONS['lightning']} AI Trading System              ║
║   {ICONS['diamond']} {AUTHOR_SIGNATURE}        ║
╚══════════════════════════════════════╝
"""

STARTUP_BANNER = f"""
{'='*60}
{ICONS['rocket']} {COMPANY_NAME} - {TAGLINE}
{'='*60}
Version: {SYSTEM_VERSION}
Author: {AUTHOR_NAME}
Status: Production Ready {ICONS['check']}
{'='*60}
"""

FOOTER_TEXT = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{COMPANY_NAME} {SYSTEM_VERSION}
{AUTHOR_SIGNATURE}
{COPYRIGHT}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# Messages Telegram
TELEGRAM_WELCOME = f"""
{ICONS['robot']} **SmartOrder PRO {SYSTEM_VERSION}**

{ICONS['fire']} AI-Powered Trading Bot
{ICONS['shield']} Secure & Professional
{ICONS['chart_up']} Multi-Exchange Support

{ICONS['diamond']} {AUTHOR_SIGNATURE}

━━━━━━━━━━━━━━━━━━━━━━━━
"""

TELEGRAM_FOOTER = f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n{AUTHOR_SIGNATURE} | {ICONS['lightning']}"

# ==================== HTML SNIPPETS ====================

HTML_SIGNATURE = f"""
<div class="signature-container">
    <div class="signature-line"></div>
    <div class="signature-content">
        <span class="by-text">Powered by</span>
        <span class="author-name gradient-text">{AUTHOR_NAME}</span>
        <span class="badge-premium">{ICONS['lightning']} AI Trading</span>
    </div>
    <div class="signature-line"></div>
</div>
"""

HTML_FOOTER = f"""
<footer class="premium-footer">
    <div class="footer-content">
        <div class="footer-logo">
            <i class="fas fa-robot"></i>
            <span class="gradient-text">{COMPANY_NAME}</span>
        </div>
        <div class="footer-signature">
            <span>{AUTHOR_SIGNATURE}</span>
            <span class="separator">•</span>
            <span>{SYSTEM_VERSION}</span>
        </div>
        <div class="footer-copyright">
            {COPYRIGHT}
        </div>
    </div>
</footer>
"""

# ==================== CLI DECORATORS ====================

def print_branded_header(title: str = "SmartOrder PRO"):
    """Affiche header avec branding"""
    print("\n" + "="*60)
    print(f"{ICONS['robot']} {title}")
    print(f"{ICONS['diamond']} {AUTHOR_SIGNATURE}")
    print("="*60 + "\n")

def print_branded_footer():
    """Affiche footer avec branding"""
    print("\n" + "="*60)
    print(f"{AUTHOR_SIGNATURE} | {SYSTEM_VERSION}")
    print(COPYRIGHT)
    print("="*60 + "\n")

def print_branded_success(message: str):
    """Message de succès brandé"""
    print(f"{ICONS['check']} {message}")

def print_branded_error(message: str):
    """Message d'erreur brandé"""
    print(f"{ICONS['cross']} {message}")

def print_branded_warning(message: str):
    """Message warning brandé"""
    print(f"{ICONS['warning']} {message}")

def print_branded_info(message: str):
    """Message info brandé"""
    print(f"{ICONS['info']} {message}")

# ==================== API RESPONSES ====================

def get_api_response_template(success: bool, data: dict = None, message: str = ""):
    """Template de réponse API brandé"""
    return {
        'success': success,
        'data': data,
        'message': message,
        'meta': {
            'system': COMPANY_NAME,
            'version': SYSTEM_VERSION,
            'author': AUTHOR_NAME,
            'timestamp': None  # À remplir par l'appelant
        }
    }

# ==================== EXPORT ====================

__all__ = [
    'AUTHOR_NAME',
    'AUTHOR_SIGNATURE',
    'COMPANY_NAME',
    'SYSTEM_VERSION',
    'TAGLINE',
    'COPYRIGHT',
    'COLORS',
    'ICONS',
    'WELCOME_MESSAGE',
    'STARTUP_BANNER',
    'FOOTER_TEXT',
    'TELEGRAM_WELCOME',
    'TELEGRAM_FOOTER',
    'HTML_SIGNATURE',
    'HTML_FOOTER',
    'print_branded_header',
    'print_branded_footer',
    'print_branded_success',
    'print_branded_error',
    'print_branded_warning',
    'print_branded_info',
    'get_api_response_template',
]
