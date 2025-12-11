document.addEventListener('DOMContentLoaded', () => {
    // Elementos comunes
    const campusSelect = document.getElementById('campus');
    const semestreSelect = document.getElementById('semestre');
    const urlParams = new URLSearchParams(window.location.search);
    const selectedCampus = urlParams.get('campus') || '';
    const selectedSemestre = urlParams.get('semestre') || '';

    // --- Funciones de carga comunes ---
    async function cargarCampus(campusSeleccionado = '') {
        try {
            const response = await fetch(`api.php?action=campus&selected=${encodeURIComponent(campusSeleccionado)}`, {
                method: 'GET',
                credentials: 'same-origin'
            });
            
            if (!response.ok) throw new Error('Error cargando campus');
            
            campusSelect.innerHTML = await response.text();
            campusSelect.value = campusSeleccionado;
        } catch (error) {
            console.error(error);
            campusSelect.innerHTML = '<option value="">Error al cargar campus</option>';
        }
    }

    async function cargarSemestres(campus, semestreSeleccionado = '') {
        if (!campus) {
            semestreSelect.innerHTML = '<option value="">Primero selecciona un campus</option>';
            semestreSelect.disabled = true;
            return;
        }
        
        try {
            const response = await fetch(`api.php?action=semestres&campus=${encodeURIComponent(campus)}&selected=${encodeURIComponent(semestreSeleccionado)}`, {
                method: 'GET',
                credentials: 'same-origin'
            });
            
            if (!response.ok) throw new Error('Error cargando semestres');
            
            semestreSelect.innerHTML = await response.text();
            semestreSelect.disabled = false;
            semestreSelect.value = semestreSeleccionado;
        } catch (error) {
            console.error(error);
            semestreSelect.innerHTML = '<option value="">Error al cargar semestres</option>';
            semestreSelect.disabled = true;
        }
    }

    // --- Funciones para Horario de Clases ---
    async function cargarAsignaturas() {
        const semestre = semestreSelect.value;
        const asignaturaSelect = document.getElementById('asignatura');
        
        if (!semestre) {
            asignaturaSelect.innerHTML = '<option value="">Selecciona un semestre</option>';
            asignaturaSelect.disabled = true;
            return;
        }
        
        try {
            const response = await fetch(`api.php?action=asignaturas&semestre=${encodeURIComponent(semestre)}`);
            asignaturaSelect.innerHTML = await response.text();
            asignaturaSelect.disabled = false;
            cargarParalelos(); // Cargar paralelos si hay asignatura seleccionada
        } catch (error) {
            asignaturaSelect.innerHTML = '<option value="">Error al cargar asignaturas</option>';
        }
    }

    async function cargarParalelos() {
        const asignaturaSelect = document.getElementById('asignatura');
        const paraleloSelect = document.getElementById('paralelo');
        const asignaturaId = asignaturaSelect.value;
        
        if (!asignaturaId) {
            paraleloSelect.innerHTML = '<option value="">Selecciona una asignatura</option>';
            paraleloSelect.disabled = true;
            return;
        }
        
        try {
            const response = await fetch(`api.php?action=paralelos&asignatura_id=${encodeURIComponent(asignaturaId)}`);
            paraleloSelect.innerHTML = await response.text();
            paraleloSelect.disabled = false;
        } catch (error) {
            paraleloSelect.innerHTML = '<option value="">Error al cargar paralelos</option>';
        }
    }

    // --- Funcionalidad Salas Vacías ---
    function setupSalasVacias() {
        const autofillNowButton = document.getElementById('autofillNowButton');
        const selectAllBloquesButton = document.getElementById('selectAllBloques');
        
        // Autofill basado en hora actual
        if (autofillNowButton) {
            autofillNowButton.addEventListener('click', () => {
                if (!campusSelect.value || semestreSelect.disabled || !semestreSelect.value) {
                    alert('Primero selecciona un Campus y un Semestre antes de continuar.');
                    return;
                }

                const now = new Date();
                const horaActual = now.getHours() * 60 + now.getMinutes();
                const diaPHP = ((now.getDay() + 6) % 7) + 1;

				const bloques = [
					{ inicio: 495, fin: 565 },   // 8:15 - 9:25
					{ inicio: 580, fin: 615 },   // 9:40 - 10:15
					{ inicio: 665, fin: 735 },   // 11:05 - 12:15
					{ inicio: 750, fin: 820 },   // 12:30 - 13:40
					{ inicio: 880, fin: 950 },   // 14:40 - 15:50
					{ inicio: 965, fin: 1035 },  // 16:05 - 17:15
					{ inicio: 1050, fin: 1120 }, // 17:30 - 18:40
					{ inicio: 1135, fin: 1205 }, // 18:55 - 20:05
					{ inicio: 1220, fin: 1290 }, // 20:20 - 21:30
					{ inicio: 1305, fin: 1375 }  // 21:45 - 22:55
				];

                let bloqueActual = -1;
                for (let i = 0; i < bloques.length; i++) {
                    const bloque = bloques[i];
                    if (horaActual >= bloque.inicio && horaActual <= bloque.fin) {
                        bloqueActual = i;
                        break;
                    }
                    if (i > 0 && horaActual > bloques[i-1].fin && horaActual < bloque.inicio) {
                        bloqueActual = i;
                        break;
                    }
                }

                if (bloqueActual === -1) {
                    alert('No hay clases en este momento.');
                    return;
                }

                document.getElementById('dia').value = diaPHP;
                document.querySelectorAll('input[name="bloques[]"]').forEach(checkbox => {
                    checkbox.checked = (checkbox.value == bloqueActual);
                });
                document.querySelector('form').submit();
            });
        }

        // Seleccionar todos los bloques
        if (selectAllBloquesButton) {
            selectAllBloquesButton.addEventListener('click', () => {
                document.querySelectorAll('input[name="bloques[]"]').forEach(checkbox => {
                    checkbox.checked = true;
                });
            });
        }
    }

    // --- Inicialización ---
    async function inicializar() {
        await cargarCampus(selectedCampus);
        await cargarSemestres(selectedCampus, selectedSemestre);
        
        // Configurar elementos específicos de Horario de Clases
        const asignaturaSelect = document.getElementById('asignatura');
        const paraleloSelect = document.getElementById('paralelo');
        
        if (asignaturaSelect && paraleloSelect) {
            campusSelect.addEventListener('change', () => {
                cargarSemestres(campusSelect.value);
                asignaturaSelect.disabled = true;
                paraleloSelect.disabled = true;
            });
            
            semestreSelect.addEventListener('change', cargarAsignaturas);
            asignaturaSelect.addEventListener('change', cargarParalelos);
            
            // Cargar asignaturas si ya hay semestre seleccionado
            if (semestreSelect.value) cargarAsignaturas();
        } 
        // Configurar elementos específicos de Salas Vacías
        else {
            campusSelect.addEventListener('change', () => {
                cargarSemestres(campusSelect.value);
            });
            setupSalasVacias();
        }
    }

    // Iniciar
    inicializar();
});