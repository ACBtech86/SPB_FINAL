/**
 * Finvest DTVM SPB — Client-side JavaScript
 * Replaces IE-specific scripts from the original ASP application.
 */

// Table sorting (replaces XSL Classifica function)
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.sortable th[data-sort]').forEach(function(th) {
        th.addEventListener('click', function() {
            var table = th.closest('table');
            var tbody = table.querySelector('tbody');
            var rows = Array.from(tbody.querySelectorAll('tr'));
            var colIndex = Array.from(th.parentElement.children).indexOf(th);
            var currentDir = th.dataset.sortDir || 'asc';
            var newDir = currentDir === 'asc' ? 'desc' : 'asc';

            // Reset all sort indicators
            table.querySelectorAll('th[data-sort]').forEach(function(h) {
                h.dataset.sortDir = '';
                h.textContent = h.textContent.replace(/ [▲▼]$/, '');
            });

            th.dataset.sortDir = newDir;
            th.textContent += newDir === 'asc' ? ' ▲' : ' ▼';

            rows.sort(function(a, b) {
                var aText = a.children[colIndex] ? a.children[colIndex].textContent.trim() : '';
                var bText = b.children[colIndex] ? b.children[colIndex].textContent.trim() : '';

                // Try numeric comparison
                var aNum = parseFloat(aText.replace(/[.]/g, '').replace(',', '.'));
                var bNum = parseFloat(bText.replace(/[.]/g, '').replace(',', '.'));
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return newDir === 'asc' ? aNum - bNum : bNum - aNum;
                }

                // String comparison
                return newDir === 'asc'
                    ? aText.localeCompare(bText, 'pt-BR')
                    : bText.localeCompare(aText, 'pt-BR');
            });

            rows.forEach(function(row) { tbody.appendChild(row); });
        });
    });
});

// Brazilian currency formatting helper
function formatBRL(value) {
    if (typeof value !== 'number') value = parseFloat(value) || 0;
    return value.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}
