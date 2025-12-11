// Esperar a que el DOM esté listo para asegurar que el canvas existe
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('estadisticasChart');
    
    // Verificar si el elemento existe (para evitar errores en otras páginas)
    if (canvas) {
        const ctx = canvas.getContext('2d');
        
        // Leer datos desde los atributos data-* del HTML (CSP Friendly)
        const totalAsignaturas = canvas.dataset.asignaturas;
        const totalParalelos = canvas.dataset.paralelos;
        const totalProfesores = canvas.dataset.profesores;

        const estadisticasChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Asignaturas', 'Paralelos', 'Profesores'],
                datasets: [{
                    label: 'Totales',
                    data: [
                        totalAsignaturas,
                        totalParalelos,
                        totalProfesores
                    ],
                    backgroundColor: [
                        '#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f'
                    ],
                    borderColor: '#333',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            // Asegurar que solo se muestren números enteros
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false // Ocultar leyenda si es redundante
                    }
                }
            }
        });
    }
});