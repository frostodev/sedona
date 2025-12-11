<?php
/**
 * Lógica de búsqueda para salas vacías.
 * *Este script recupera y muestra las salas disponibles basándose en el campus, semestre y bloque horario seleccionado.
 * @package Sedona
 */

// Previene el acceso directo a este archivo
if (!defined('SEDONA_INCLUDED')) {
    http_response_code(403);
    die('Acceso denegado.');
}
require_once 'conexion.php';

/**
 * @brief Carga y sanitiza los parámetros GET de la URL.
 *
 * @throws Exception Si faltan parámetros obligatorios o son inválidos.
 * @return array Arreglo asociativo con los parámetros limpios.
 */
function cargar_parametros() {
    // Filtros básicos de cadena
    $campus = filter_input(INPUT_GET, 'campus', FILTER_SANITIZE_SPECIAL_CHARS);
    $semestre = filter_input(INPUT_GET, 'semestre', FILTER_SANITIZE_SPECIAL_CHARS);
    
    // Validación estricta de enteros para el día (1-7)
    $dia = filter_input(INPUT_GET, 'dia', FILTER_VALIDATE_INT, [
        'options' => ['min_range' => 1, 'max_range' => 7]
    ]);

    // Validación de arreglo de bloques (0-9)
    $bloques = filter_input(INPUT_GET, 'bloques', FILTER_VALIDATE_INT, [
        'flags' => FILTER_REQUIRE_ARRAY,
        'options' => ['min_range' => 0, 'max_range' => 9]
    ]);

    if (!$campus || !$semestre || !$dia || !$bloques) {
        throw new Exception("Parámetros incompletos o inválidos");
    }

    return [
        'campus' => $campus,
        'semestre' => $semestre,
        'dia' => $dia,
        'bloques' => $bloques
    ];
}

/**
 * @brief Obtiene todas las salas asociadas a un campus y semestre.
 *
 * @param PDO $pdo Conexión a la base de datos.
 * @param string $campus Nombre del campus.
 * @param string $semestre Código del semestre.
 * @return array Lista simple de nombres de salas (strings).
 */
function obtener_salas_campus($pdo, $campus, $semestre) {
    // Usamos DISTINCT para obtener la lista única de salas que tienen al menos una clase
    // en ese semestre y campus.
    $sql = "
        SELECT DISTINCT h.sala
        FROM horario h
        JOIN paralelo p ON h.paralelo_id = p.id
        JOIN asignatura a ON p.asignatura_id = a.id
        JOIN semestre s ON a.semestre_id = s.id
        JOIN campus c ON s.campus_id = c.id
        WHERE c.nombre = :campus
        AND s.codigo = :semestre
        ORDER BY h.sala ASC
    ";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute([':campus' => $campus, ':semestre' => $semestre]);
    
    return $stmt->fetchAll(PDO::FETCH_COLUMN, 0);
}

/**
 * @brief Obtiene el mapa de ocupación de todas las salas para un día específico.
 * Realiza una sola consulta para traer todos los bloques ocupados del día y los organiza en un array.
 *
 * @param PDO $pdo Conexión a la base de datos.
 * @param string $campus Nombre del campus.
 * @param string $semestre Código del semestre.
 * @param int $dia Número del día (1=Lunes, etc).
 * @return array Mapa asociativo ['NombreSala' => [Bloque1, Bloque2, ...]]
 */
function obtener_mapa_ocupacion($pdo, $campus, $semestre, $dia) {
    $sql = "
        SELECT h.sala, h.bloque_inicio
        FROM horario h
        JOIN paralelo p ON h.paralelo_id = p.id
        JOIN asignatura a ON p.asignatura_id = a.id
        JOIN semestre s ON a.semestre_id = s.id
        JOIN campus c ON s.campus_id = c.id
        WHERE c.nombre = :campus
        AND s.codigo = :semestre
        AND h.dia_semana = :dia
    ";

    $stmt = $pdo->prepare($sql);
    $stmt->execute([
        ':campus' => $campus, 
        ':semestre' => $semestre, 
        ':dia' => $dia
    ]);

    // PDO::FETCH_GROUP agrupa los resultados por la primera columna (sala)
    // El resultado será: ['A-101' => [['bloque_inicio'=>1], ['bloque_inicio'=>2]], ...]
    $raw = $stmt->fetchAll(PDO::FETCH_GROUP | PDO::FETCH_ASSOC);
    
    // Limpiar el array para que sea más fácil de consultar: ['A-101' => [1, 2, 5]]
    $mapa = [];
    foreach ($raw as $sala => $bloques) {
        $mapa[$sala] = array_column($bloques, 'bloque_inicio');
    }
    
    return $mapa;
}

/**
 * @brief Genera y renderiza la tabla HTML con los resultados.
 *
 * @param array $salas Lista de todas las salas.
 * @param array $mapa_ocupacion Mapa de ocupación optimizado.
 * @param array $bloques_solicitados Lista de IDs de bloques que el usuario quiere ver (0-9).
 * @param string $campus Nombre del campus.
 * @param string $semestre Nombre del semestre.
 * @param int $dia Día de la semana.
 * @return void Imprime HTML directo.
 */
function generar_tabla_resultados($salas, $mapa_ocupacion, $bloques_solicitados, $campus, $semestre, $dia) {
    $dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    
    // Convertir bloques 0-9 a formato legible "1-2", "3-4"
    $bloques_legibles = array_map(fn($b) => ($b * 2 + 1) . '-' . ($b * 2 + 2), $bloques_solicitados);

    echo '<div class="card mt-4">';
    echo '<div class="card-header bg-primary text-white">';
    echo '<h4 class="mb-0">Estado de Salas</h4>';
    echo '<div class="row mt-2">';
    echo '<div><small>Campus: ' . htmlspecialchars($campus) . ' | Semestre: ' . htmlspecialchars($semestre) . '</small></div>';
    echo '</div></div>';
    
    echo '<div class="card-body">';
    echo '<h5 class="card-title mb-3">';
    echo '<span class="badge bg-secondary me-2">' . $dias_semana[$dia - 1] . '</span>';
    echo '<span class="badge bg-secondary">Bloques: ' . implode(', ', $bloques_legibles) . '</span>';
    echo '</h5>';

    echo '<div class="table-responsive">';
    echo '<table class="table table-bordered table-hover align-middle">';
    echo '<thead class="table-light">';
    echo '<tr><th class="text-center">Sala</th>';
    
    foreach ($bloques_solicitados as $b) {
        $rango = ($b * 2 + 1) . '-' . ($b * 2 + 2);
        echo '<th class="text-center">' . $rango . '</th>';
    }
    echo '</tr></thead><tbody>';

    // Ordenar salas alfabéticamente (Natural sort para que A-2 venga antes que A-10)
    natsort($salas);
    
    foreach ($salas as $sala) {
        // Limpiar prefijo 'Sala ' si existe para el enlace
        $sala_codigo = preg_replace('/^Sala\s+/i', '', $sala);
        $enlace = 'horario_salas.php?' . http_build_query([
            'sala' => $sala_codigo,
            'campus' => $campus,
            'semestre' => $semestre
        ]);
        
        echo '<tr><td class="text-center">';
        echo '<a href="' . htmlspecialchars($enlace) . '" class="btn btn-sm btn-outline-primary">';
        echo htmlspecialchars($sala);
        echo '</a></td>';
        
        // Iterar solo sobre los bloques que el usuario pidió
        foreach ($bloques_solicitados as $bloque_idx) {
            // Los bloques en BDD empiezan en 1, los del input en 0. Ajustamos.
            $bloque_bdd = $bloque_idx + 1; 
            
            // Verificación en memoria O(1) en lugar de consulta SQL
            $esta_ocupada = isset($mapa_ocupacion[$sala]) && in_array($bloque_bdd, $mapa_ocupacion[$sala]);
            
            $clase = $esta_ocupada ? 'bg-danger text-white' : 'bg-success text-white';
            $texto = $esta_ocupada ? 'Ocupado' : 'Libre';
            
            echo '<td class="text-center ' . $clase . '">' . $texto . '</td>';
        }
        echo '</tr>';
    }
    
    echo '</tbody></table></div></div></div>';
}

try {
    // Verificar si existen los parámetros antes de iniciar la lógica pesada
    if (isset($_GET['campus'], $_GET['semestre'], $_GET['dia'], $_GET['bloques'])) {
        
        $params = cargar_parametros();
        
        // Obtener listado maestro de salas
        $salas = obtener_salas_campus($pdo, $params['campus'], $params['semestre']);

        // Obtener mapa de ocupación (Eager Loading)
        // Esto reduce cientos de consultas a una nomás
        $mapa_ocupacion = obtener_mapa_ocupacion(
            $pdo, 
            $params['campus'], 
            $params['semestre'], 
            $params['dia']
        );

        // Renderizar
        generar_tabla_resultados(
            $salas, 
            $mapa_ocupacion, 
            $params['bloques'], 
            $params['campus'], 
            $params['semestre'], 
            $params['dia']
        );
    }
    
} catch (Exception $e) {
    error_log("Error en buscar_salas_vacias.php: " . $e->getMessage());
    echo '<div class="alert alert-danger mt-4">Ocurrió un error al procesar la solicitud.</div>';
}
?>