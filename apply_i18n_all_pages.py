#!/usr/bin/env python3
"""
Script para adicionar i18n.js em todas as páginas HTML do LiberChat
"""

import os
import re

TEMPLATES_DIR = '/mnt/projetos/liberchat/templates'

# Páginas para adicionar i18n
PAGES = [
    'general.html',
    'security.html',
    'relays.html',
    'appearance.html',
    'settings.html',
    'dm_chat.html',
    'group_chat.html',
    'help.html',
    'emojis.html'
]

def add_i18n_script(file_path):
    """Adiciona script i18n.js se ainda não existir"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verifica se já tem i18n.js
    if 'i18n.js' in content:
        print(f'  ✓ {os.path.basename(file_path)} - já tem i18n.js')
        return False

    # Procura por tailwindcss.com e adiciona i18n logo após
    pattern = r'(<script src="https://cdn\.tailwindcss\.com"></script>)'
    replacement = r'\1\n    <script src="{{ url_for(\'static\', filename=\'js/i18n.js\') }}"></script>'

    if re.search(pattern, content):
        new_content = re.sub(pattern, replacement, content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f'  ✅ {os.path.basename(file_path)} - i18n.js adicionado')
        return True
    else:
        print(f'  ⚠️  {os.path.basename(file_path)} - padrão não encontrado')
        return False

def add_language_change_listener(file_path):
    """Adiciona listener para reload quando idioma mudar"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verifica se já tem o listener
    if 'languageChanged' in content:
        print(f'  ✓ {os.path.basename(file_path)} - já tem listener')
        return False

    # Adiciona antes do </script> final
    listener_code = """
// Atualizar página quando idioma mudar
window.addEventListener('languageChanged', () => {
    console.log('[I18N] Idioma alterado, recarregando página...');
    setTimeout(() => {
        window.location.reload();
    }, 500);
});
"""

    # Procura pelo último </script> antes de </body>
    pattern = r'(</script>\s*(?:</div>\s*)?</body>)'
    replacement = listener_code + r'\1'

    if re.search(pattern, content):
        new_content = re.sub(pattern, replacement, content, count=1)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f'  ✅ {os.path.basename(file_path)} - listener adicionado')
        return True
    else:
        print(f'  ⚠️  {os.path.basename(file_path)} - </script> não encontrado')
        return False

def main():
    print("=" * 70)
    print("  Aplicando i18n em todas as páginas do LiberChat")
    print("=" * 70)
    print()

    added_script = 0
    added_listener = 0

    for page in PAGES:
        file_path = os.path.join(TEMPLATES_DIR, page)

        if not os.path.exists(file_path):
            print(f'⚠️  {page} não encontrado')
            continue

        print(f'\n📄 Processando {page}...')

        # Adiciona script
        if add_i18n_script(file_path):
            added_script += 1

        # Adiciona listener
        if add_language_change_listener(file_path):
            added_listener += 1

    print()
    print("=" * 70)
    print(f"  ✅ Concluído!")
    print(f"  Scripts adicionados: {added_script}/{len(PAGES)}")
    print(f"  Listeners adicionados: {added_listener}/{len(PAGES)}")
    print("=" * 70)

if __name__ == '__main__':
    main()
