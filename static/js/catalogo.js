let productos = [];
let categoriaActual = 'todos';
let busquedaActual = '';

// CONSUMIR LA API DE FLASK
async function cargarProductos() {
    try {
        const response = await fetch('/api/productos');
        productos = await response.json();
        renderProducts();
    } catch (error) {
        console.error("Error al conectar con la API interna de Flask:", error);
    }
}

function renderProducts() {
    const grid = document.getElementById('productGrid');
    const noResults = document.getElementById('noResults');
    if (!grid) return; // Guard clause de seguridad
    
    grid.innerHTML = '';

    const filtrados = productos.filter(p => {
        const matchCategoria = categoriaActual === 'todos' || p.categoria === categoriaActual;
        const matchBusqueda = p.nombre.toLowerCase().includes(busquedaActual.toLowerCase()) || 
                              p.codigo.toLowerCase().includes(busquedaActual.toLowerCase());
        return matchCategoria && matchBusqueda;
    });

    if (filtrados.length === 0) {
        noResults.classList.remove('hidden');
    } else {
        noResults.classList.add('hidden');
        filtrados.forEach(p => {
            grid.innerHTML += `
                <div class="bg-white rounded-xl overflow-hidden border border-stone-200 shadow-sm hover:shadow-md transition-all flex flex-col">
                    <div class="relative bg-stone-100 aspect-square w-full overflow-hidden group">
                        <img src="${p.imagen}" alt="${p.nombre}" class="object-cover w-full h-full group-hover:scale-105 transition-transform duration-300">
                        <span class="absolute top-2 left-2 bg-stone-900/80 text-white font-mono text-[10px] uppercase tracking-wider px-2 py-0.5 rounded backdrop-blur-sm">
                            ${p.codigo}
                        </span>
                    </div>
                    <div class="p-4 flex flex-col justify-between flex-1">
                        <div>
                            <h3 class="font-semibold text-stone-900 text-base leading-tight">${p.nombre}</h3>
                            <p class="text-xs text-stone-500 mt-1 line-clamp-2">${p.descripcion}</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-stone-100 flex items-center justify-between">
                            <span class="text-base font-bold text-stone-900">$${p.precio.toFixed(2)}</span>
                            <a href="https://wa.me/525500000000?text=Hola,%20me%20interesa%20el%20producto%20con%20código:%20${p.codigo}" 
                               target="_blank"
                               class="inline-flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition-colors">
                                <i data-lucide="message-circle" class="w-3.5 h-3.5"></i> Pedir
                            </a>
                        </div>
                    </div>
                </div>
            `;
        });
    }
    lucide.createIcons();
}

function filterCategory(cat) {
    categoriaActual = cat;
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('bg-amber-600', 'text-white', 'shadow-sm');
        btn.classList.add('bg-white', 'text-stone-600', 'border', 'border-stone-200');
    });
    const btnActivo = document.getElementById(`btn-${cat}`);
    if (btnActivo) {
        btnActivo.classList.remove('bg-white', 'text-stone-600', 'border', 'border-stone-200');
        btnActivo.classList.add('bg-amber-600', 'text-white', 'shadow-sm');
    }
    renderProducts();
}

// Inicialización cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            busquedaActual = e.target.value;
            renderProducts();
        });
    }
    cargarProductos();
});