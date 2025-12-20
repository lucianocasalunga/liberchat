/**
 * LiberChat - Sistema de Internacionalização (i18n)
 * Gerencia carregamento e aplicação de traduções
 */

class I18n {
    constructor() {
        this.currentLang = this.getSavedLanguage() || 'pt-BR';
        this.translations = {};
        this.fallbackLang = 'pt-BR';
    }

    /**
     * Obtém o idioma salvo no localStorage
     */
    getSavedLanguage() {
        return localStorage.getItem('liberchat_language');
    }

    /**
     * Salva o idioma no localStorage
     */
    saveLanguage(lang) {
        localStorage.setItem('liberchat_language', lang);
    }

    /**
     * Carrega arquivo de tradução
     */
    async loadTranslation(lang) {
        try {
            const response = await fetch(`/static/i18n/${lang}.json`);
            if (!response.ok) {
                throw new Error(`Failed to load ${lang}`);
            }
            this.translations[lang] = await response.json();
            return true;
        } catch (error) {
            console.error(`Error loading translation ${lang}:`, error);
            return false;
        }
    }

    /**
     * Inicializa o sistema de tradução
     */
    async init() {
        // Carrega idioma atual
        await this.loadTranslation(this.currentLang);

        // Carrega fallback se diferente
        if (this.currentLang !== this.fallbackLang) {
            await this.loadTranslation(this.fallbackLang);
        }

        // Aplica traduções na página
        this.applyTranslations();

        return this.currentLang;
    }

    /**
     * Obtém texto traduzido usando notação de ponto (ex: "nav.chats")
     */
    t(key, variables = {}) {
        const keys = key.split('.');
        let value = this.translations[this.currentLang];

        // Navega pelo objeto de tradução
        for (const k of keys) {
            if (value && typeof value === 'object') {
                value = value[k];
            } else {
                value = undefined;
                break;
            }
        }

        // Se não encontrou, tenta fallback
        if (value === undefined) {
            value = this.translations[this.fallbackLang];
            for (const k of keys) {
                if (value && typeof value === 'object') {
                    value = value[k];
                } else {
                    value = key; // Retorna a chave se não encontrar
                    break;
                }
            }
        }

        // Substitui variáveis {{var}}
        if (typeof value === 'string') {
            value = value.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
                return variables[varName] !== undefined ? variables[varName] : match;
            });
        }

        return value || key;
    }

    /**
     * Aplica traduções em elementos com atributo data-i18n
     */
    applyTranslations() {
        // Traduz elementos com data-i18n (texto)
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            element.textContent = this.t(key);
        });

        // Traduz placeholders com data-i18n-placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });

        // Traduz títulos com data-i18n-title
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });

        // Traduz aria-label com data-i18n-aria
        document.querySelectorAll('[data-i18n-aria]').forEach(element => {
            const key = element.getAttribute('data-i18n-aria');
            element.setAttribute('aria-label', this.t(key));
        });
    }

    /**
     * Troca o idioma da aplicação
     */
    async changeLanguage(lang) {
        // Carrega tradução se ainda não estiver carregada
        if (!this.translations[lang]) {
            const loaded = await this.loadTranslation(lang);
            if (!loaded) {
                console.error(`Cannot load language: ${lang}`);
                return false;
            }
        }

        // Atualiza idioma atual
        this.currentLang = lang;
        this.saveLanguage(lang);

        // Reaplica traduções
        this.applyTranslations();

        // Dispara evento customizado
        window.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language: lang }
        }));

        return true;
    }

    /**
     * Retorna lista de idiomas disponíveis
     */
    getAvailableLanguages() {
        return [
            { code: 'pt-BR', name: 'Português (Brasil)', flag: '🇧🇷', available: true },
            { code: 'en-US', name: 'English (US)', flag: '🇺🇸', available: true },
            { code: 'es-ES', name: 'Español', flag: '🇪🇸', available: true },
            { code: 'he-IL', name: 'עברית (Hebrew)', flag: '🇮🇱', available: false },
            { code: 'uk-UA', name: 'Українська (Ukrainian)', flag: '🇺🇦', available: false },
            { code: 'ru-RU', name: 'Русский (Russian)', flag: '🇷🇺', available: false }
        ];
    }

    /**
     * Retorna idioma atual
     */
    getCurrentLanguage() {
        return this.currentLang;
    }

    /**
     * Retorna nome do idioma atual
     */
    getCurrentLanguageName() {
        const langs = this.getAvailableLanguages();
        const current = langs.find(l => l.code === this.currentLang);
        return current ? current.name : this.currentLang;
    }
}

// Cria instância global
const i18n = new I18n();

// Inicializa quando DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        i18n.init();
    });
} else {
    i18n.init();
}

// Exporta para uso global
window.i18n = i18n;
