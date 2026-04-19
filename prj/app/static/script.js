// Otevírání štítků
document.addEventListener('DOMContentLoaded', function() {
    const tags = document.querySelectorAll('.dynamic-tag-container');

    tags.forEach(tagContainer => {
        tagContainer.addEventListener('mouseenter', function() {
            const tagId = this.dataset.tagId;
            const tooltip = this.querySelector('.tag-tooltip');
            const loader = this.querySelector('.tooltip-loader');
            const content = this.querySelector('.tooltip-data');

            // Pokud už data máme, znovu se neptej (cache)
            if (this.dataset.loaded === 'true') return;

            fetch(`/api/stitek/${tagId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Vyplnění dat z tvého JSONu
                        content.querySelector('.tooltip-title').textContent = data.stitek;
                        
                        const list = content.querySelector('.tooltip-list');
                        list.innerHTML = ''; // Vyčistit původní obsah
                        
                        data.prvky.forEach(prvek => {
                            const li = document.createElement('li');
                            li.textContent = prvek.nazev;
                            list.appendChild(li);
                        });

                        content.querySelector('.tooltip-footer').textContent = 
                            `Celkem prvků: ${data.prvky_count} | Uživatel: ${data.request_user}`;

                        // Přepnutí viditelnosti
                        loader.style.display = 'none';
                        content.style.display = 'block';
                        this.dataset.loaded = 'true'; // Označíme jako načtené
                    }
                })
                .catch(error => {
                    loader.textContent = 'Chyba při načítání.';
                    console.error('Error fetching tag data:', error);
                });
        });
    });
});