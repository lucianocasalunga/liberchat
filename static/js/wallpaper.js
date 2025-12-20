/**
 * LiberChat - Aplicação de Wallpaper Global
 * Carrega e aplica o wallpaper selecionado
 */

(function() {
    // Carrega wallpaper do localStorage
    const savedWallpaper = localStorage.getItem('liberchat_wallpaper') || 'wallpaper-default';

    // Aplica wallpaper ao body
    function applyWallpaper() {
        // Remove todas as classes de wallpaper anteriores
        const body = document.body;
        const wallpaperClasses = [
            'wallpaper-default',
            'wallpaper-gradient-pink',
            'wallpaper-gradient-blue',
            'wallpaper-gradient-purple',
            'wallpaper-gradient-green',
            'wallpaper-gradient-orange',
            'wallpaper-geometric',
            'wallpaper-dark-subtle',
            'wallpaper-minimal-light'
        ];

        wallpaperClasses.forEach(cls => body.classList.remove(cls));

        // Adiciona a classe do wallpaper selecionado
        body.classList.add(savedWallpaper);
    }

    // Aplica quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyWallpaper);
    } else {
        applyWallpaper();
    }

    // Escuta mudanças no wallpaper
    window.addEventListener('storage', (e) => {
        if (e.key === 'liberchat_wallpaper') {
            applyWallpaper();
        }
    });

    // Evento customizado para mudanças no wallpaper
    window.addEventListener('wallpaperChanged', applyWallpaper);
})();
