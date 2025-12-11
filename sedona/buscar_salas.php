<?php
/**
 * Lógica de búsqueda de horarios por sala.
 * Busca asignaturas asignadas a una sala específica (parcial o exacta)
 * y muestra una tabla de horario semanal.
 * @package Sedona
 */

// Previene el acceso directo a este archivo
if (!defined('SEDONA_INCLUDED')) {
    http_response_code(403);
    die('Acceso denegado.');
}
require_once 'conexion.php';

/**
 * @brief Carga y sanitiza los parámetros de búsqueda desde $_GET.
 *
 * @throws Exception Si faltan parámetros requeridos.
 * @return array Arreglo con 'sala', 'campus' y 'semestre'.
 */
function cargar_parametros() {
    // Sanitización básica para prevenir XSS reflejado
    $sala = filter_input(INPUT_GET, 'sala', FILTER_SANITIZE_SPECIAL_CHARS);
    $campus = filter_input(INPUT_GET, 'campus', FILTER_SANITIZE_SPECIAL_CHARS);
    $semestre = filter_input(INPUT_GET, 'semestre', FILTER_SANITIZE_SPECIAL_CHARS);

    // Comprobación de nulidad
    if (!$sala || !$campus || !$semestre) {
        throw new Exception("Parámetros incompletos o inválidos");
    }

    return [
        'sala' => $sala,
        'campus' => $campus,
        'semestre' => $semestre,
    ];
}

/**
 * @brief Normaliza el nombre de una sala para agrupar variantes.
 * Ej: "B008 LAB-MEC" -> "B008"
 *
 * @param string $nombre_sala Nombre crudo de la sala.
 * @return string Base del nombre normalizada.
 */
function obtener_base_sala($nombre_sala) {
    // Eliminar sufijos comunes de la universidad
    $nombre_sala = preg_replace('/\s*[-]?\s*(SJ|Campus|Laboratorio)\s*$/i', '', $nombre_sala);
    
    // Caso 1: Si contiene "LAB" seguido de identificador
    if (preg_match('/(LAB\s*[-]?\s*\w+)/i', $nombre_sala, $matches)) {
        return trim($matches[1]);
    } 
    // Caso 2: Formato "B008 LAB..."
    elseif (preg_match('/(\w+)\s+LAB/i', $nombre_sala, $matches)) {
        return trim($matches[1]);
    }
    // Caso 3: Default (primera palabra alfanumérica)
    else {
        return preg_replace('/[^a-zA-Z0-9].*$/', '', $nombre_sala);
    }
}

/**
 * @brief Consulta la base de datos buscando coincidencias de sala.
 *
 * @param PDO $pdo Conexión a la BDD.
 * @param string $sala Texto de búsqueda (LIKE).
 * @param string $campus Campus seleccionado.
 * @param string $semestre Semestre seleccionado.
 * @return array Filas encontradas (JOIN completo de horario, asignatura, etc).
 */
function buscar_sala($pdo, $sala, $campus, $semestre) {
    $sql = "
        SELECT 
            h.sala,
            a.codigo AS codigo_asignatura,
            a.nombre AS nombre_asignatura,
            p.paralelo,
            h.dia_semana,
            h.bloque_inicio
        FROM asignatura a
        JOIN paralelo p ON a.id = p.asignatura_id
        JOIN horario h ON p.id = h.paralelo_id
        JOIN semestre s ON a.semestre_id = s.id
        JOIN campus c ON s.campus_id = c.id
        WHERE c.nombre = :campus
        AND s.codigo = :semestre
        AND LOWER(h.sala) LIKE CONCAT('%', LOWER(:sala), '%')  -- Búsqueda insensible a mayúsculas
        ORDER BY h.sala, h.dia_semana, h.bloque_inicio
    ";

    $stmt = $pdo->prepare($sql);
    $stmt->execute([
        ':campus' => $campus,
        ':semestre' => $semestre,
        ':sala' => $sala
    ]);

    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}

/**
 * @brief Renderiza la tabla HTML del horario para una sala específica.
 *
 * @param array $filas Array de clases encontradas para esta sala.
 * @param string $base_sala Nombre normalizado.
 * @param string $nombre_original Nombre completo encontrado en DB.
 * @param string $campus Nombre del campus.
 * @param string $semestre Código del semestre.
 */
function mostrar_horario_para_sala($filas, $base_sala, $nombre_original, $campus, $semestre) {
    $dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

    // Inicializar matriz de 10 bloques x 7 días
    $tabla_horario = array_fill(0, 10, array_fill(0, 7, []));
    $asignaturas_mostradas = array_fill(0, 10, array_fill(0, 7, []));

    // Poblar matriz
    foreach ($filas as $row) {
        $fila = $row['bloque_inicio'] - 1;
        $columna = $row['dia_semana'] - 1;
        $codigo = $row['codigo_asignatura'];
        $paralelo = $row['paralelo'];

        // Evitar duplicados visuales si la query trae filas redundantes
        if (!in_array($codigo . '-' . $paralelo, $asignaturas_mostradas[$fila][$columna])) {
            $tabla_horario[$fila][$columna][] = [
                'codigo' => $codigo,
                'nombre' => $row['nombre_asignatura'],
                'paralelo' => $paralelo
            ];
            $asignaturas_mostradas[$fila][$columna][] = $codigo . '-' . $paralelo;
        }
    }

    // --- Renderizado HTML ---
    echo '<div class="card mb-4">';
    echo '<div class="card-header bg-primary text-white">';
    echo '<h4 class="mb-0">Resultados para sala: ' . htmlspecialchars($nombre_original) . '</h4>';
    echo '<small class="d-block mt-1">Campus: ' . htmlspecialchars($campus) . ' | Semestre: ' . htmlspecialchars($semestre) . '</small>';
    echo '</div>';
    
    echo '<div class="card-body">';
    echo '<div class="table-responsive">';
    echo '<table class="table table-bordered table-hover table-sm align-middle">';
    echo '<thead class="table-light">';
    echo '<tr><th class="text-center">Bloque</th>';
    foreach ($dias_semana as $dia) {
        echo '<th class="text-center">' . $dia . '</th>';
    }
    echo '</tr></thead><tbody>';

    $horas_bloques = [
        '1-2' => '8.15-9.25', '3-4' => '9.40-10.50', '5-6' => '11.05-12.15',
        '7-8' => '12.30-13.40', '9-10' => '14.40-15.50', '11-12' => '16.05-17.15',
        '13-14' => '17.30-18.40', '15-16' => '18.55-20.05', '17-18' => '20.20-21.30',
        '19-20' => '21.45-22.55'
    ];

    foreach ($tabla_horario as $i => $fila_datos) {
        $bloque_num = ($i * 2 + 1) . '-' . ($i * 2 + 2);
        $hora = $horas_bloques[$bloque_num] ?? '';

        echo '<tr>';
        echo '<td class="text-center"><div class="fw-bold">' . $bloque_num . '</div><div class="small text-muted">' . $hora . '</div></td>';

        foreach ($fila_datos as $celda) {
            echo '<td class="p-2">';
            if (!empty($celda)) {
                echo '<div class="row g-1">';
                foreach ($celda as $clase) {
                    $codigo = htmlspecialchars($clase['codigo']);
                    $paralelo = htmlspecialchars($clase['paralelo']);
                    $nombre = htmlspecialchars($clase['nombre']);
                    
                    // Link cruzado para ver detalles de la asignatura
                    $url_asignatura = 'horario_asignaturas.php?' . http_build_query([
                        'codigo' => $codigo . '-' . $paralelo,
                        'campus' => $campus,
                        'semestre' => $semestre
                    ]);
                    
                    echo '<div class="col-12">';
                    echo '<a href="' . $url_asignatura . '" class="d-block btn btn-sm btn-outline-primary text-start p-2 mb-1">';
                    echo '<div class="fw-bold">' . $codigo . ' <small>(' . $paralelo . ')</small></div>';
                    echo '<div class="small text-muted">' . $nombre . '</div>';
                    echo '</a>';
                    echo '</div>';
                }
                echo '</div>';
            }
            echo '</td>';
        }
        echo '</tr>';
    }
    
    echo '</tbody></table></div></div></div>';
}

try {
    if (isset($_GET['sala'], $_GET['campus'], $_GET['semestre'])) {
        
        $params = cargar_parametros();
        $resultados = buscar_sala($pdo, $params['sala'], $params['campus'], $params['semestre']);

        $grupos = [];
        // Agrupamiento inteligente por nombre base de sala
        foreach ($resultados as $row) {
            $base = obtener_base_sala($row['sala']);
            $grupos[$base]['filas'][] = $row;
            $grupos[$base]['nombre_original'] = $row['sala']; 
        }

        // Ordenar por nombre de sala
        ksort($grupos, SORT_NATURAL | SORT_FLAG_CASE);

        if (empty($grupos)) {
            echo '<div class="alert alert-info mt-4">No se encontraron salas con el nombre <strong>"' . htmlspecialchars($params['sala']) . '"</strong></div>';
        } else {
            foreach ($grupos as $base_sala => $grupo) {
                mostrar_horario_para_sala(
                    $grupo['filas'], 
                    $base_sala,
                    $grupo['nombre_original'],
                    $params['campus'], 
                    $params['semestre']
                );
            }
        }
    }
} catch (Exception $e) {
    error_log("Error en buscar_salas.php: " . $e->getMessage());
    echo '<div class="alert alert-danger mt-4">Ocurrió un error al buscar la sala.</div>';
}
?>