<?php
/**
 * Lógica de búsqueda de asignaturas.
 * Permite buscar por código, nombre o profesor, mostrando detalles de paralelos, cupos y horarios asociados.
 * @package Sedona
 */

// Previene el acceso directo
if (!defined('SEDONA_INCLUDED')) {
    http_response_code(403);
    die('Acceso denegado.');
}
require_once 'conexion.php';

/**
 * @brief Normaliza texto eliminando caracteres no alfanuméricos (para códigos de asignatura).
 * @param string $texto Texto entrada.
 * @return string Texto limpio en minúsculas.
 */
function normalizar_exacto($texto) {
    return preg_replace('/[^a-z0-9]/', '', strtolower($texto));
}

/**
 * @brief Prepara texto para búsqueda SQL con comodines (LIKE %texto%).
 * Divide palabras por espacios para búsquedas compuestas.
 * @param string $texto Texto entrada.
 * @return string Cadena formateada para SQL.
 */
function normalizar_texto($texto) {
    $texto_minusculas = strtolower($texto);
    $partes = preg_split('/\s+/', $texto_minusculas);
    return '%' . implode('%', $partes) . '%';
}

/**
 * @brief Carga parámetros GET.
 * @throws Exception Si faltan parámetros.
 * @return array Parámetros sanitizados.
 */
function cargar_parametros() {
    $busqueda = filter_input(INPUT_GET, 'codigo', FILTER_SANITIZE_SPECIAL_CHARS);
    $campus = filter_input(INPUT_GET, 'campus', FILTER_SANITIZE_SPECIAL_CHARS);
    $semestre = filter_input(INPUT_GET, 'semestre', FILTER_SANITIZE_SPECIAL_CHARS);
    
    // Filtro booleano para ocultar bloques
    $ocultar_vacios = filter_input(INPUT_GET, 'ocultar_vacios', FILTER_VALIDATE_BOOLEAN, FILTER_NULL_ON_FAILURE);
    if ($ocultar_vacios === null) {
        $ocultar_vacios = false; 
    }
    
    if (!$busqueda || !$campus || !$semestre) {
        throw new Exception("Parámetros incompletos o inválidos");
    }

    return [
        'busqueda' => $busqueda,
        'campus' => $campus,
        'semestre' => $semestre,
        'ocultar_vacios' => $ocultar_vacios
    ];
}

/**
 * @brief Ejecuta la búsqueda en la base de datos.
 * Detecta automáticamente si se está buscando un paralelo específico (MAT021-1) o texto general.
 *
 * @param PDO $pdo Objeto conexión.
 * @param string $busqueda Texto buscado.
 * @param string $campus Campus.
 * @param string $semestre Semestre.
 * @return array Resultados planos de la DB.
 */
function buscar_asignaturas($pdo, $busqueda, $campus, $semestre) {
    // Detección de patrón "CODIGO-PARALELO" (Ej: MAT024-200)
    $es_paralelo = preg_match('/^([^\s\-]+)[\s\-]+(\d+)/', $busqueda, $matches);
    
    $sql = "
        SELECT 
            a.codigo AS codigo_asignatura,
            a.nombre AS nombre_asignatura,
            a.departamento,
            p.paralelo,
            p.cupos,
            GROUP_CONCAT(DISTINCT pr.nombre SEPARATOR ', ') AS profesores,
            h.dia_semana,
            h.bloque_inicio,
            h.sala
        FROM asignatura a
        JOIN paralelo p ON a.id = p.asignatura_id
        LEFT JOIN paralelo_profesor pp ON p.id = pp.paralelo_id
        LEFT JOIN profesor pr ON pp.profesor_id = pr.id
        LEFT JOIN horario h ON p.id = h.paralelo_id
        JOIN semestre s ON a.semestre_id = s.id
        JOIN campus c ON s.campus_id = c.id
        WHERE c.nombre = :campus
        AND s.codigo = :semestre
    ";

    $params = [
        ':campus' => $campus,
        ':semestre' => $semestre
    ];

    if ($es_paralelo) {
        // Búsqueda exacta de paralelo
        $sql .= " AND a.codigo LIKE :codigo AND p.paralelo LIKE CONCAT(:paralelo, '%')";
        $params[':codigo'] = normalizar_exacto($matches[1]);
        $params[':paralelo'] = normalizar_exacto($matches[2]);
    } else {
        // Búsqueda general (Nombre, Código o Profesor)
        $busqueda_norm = normalizar_texto($busqueda);
        $sql .= " AND (
            a.codigo LIKE :busqueda 
            OR a.nombre LIKE :busqueda 
            OR pr.nombre LIKE :busqueda
        )";
        $params[':busqueda'] = $busqueda_norm;
    }

    $sql .= " GROUP BY a.id, p.id, h.dia_semana, h.bloque_inicio";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}

/**
 * @brief Renderiza los resultados de búsqueda agrupados por asignatura y luego por paralelo.
 * Procesa el conjunto de resultados planos de la base de datos, agrupándolos jerárquicamente
 * (Asignatura -> Paralelos -> Horarios) para mostrar tarjetas de información ordenadas.
 * Si no hay resultados, muestra un mensaje de alerta.
 *
 * @param array $resultados Array de resultados obtenidos de la consulta SQL (PDO::FETCH_ASSOC).
 * @param string $campus Nombre del campus para mostrar en el header y generar enlaces.
 * @param string $semestre Código del semestre para mostrar en el header y generar enlaces.
 * @param string $busqueda Término de búsqueda original para mostrar en el título.
 * @param bool $ocultar_vacios Flag para ocultar bloques horarios sin clases.
 * @return void Genera salida HTML directa.
 */
function mostrar_resultados($resultados, $campus, $semestre, $busqueda, $ocultar_vacios) {
    if (empty($resultados)) {
        echo '<div class="alert alert-info mt-4">No se encontraron resultados para "' . htmlspecialchars($busqueda) . '"</div>';
        return;
    }

    echo '<div class="card mt-4">';
    echo '<div class="card-header bg-primary text-white">';
    echo '<h4 class="mb-0">Resultados para: "' . htmlspecialchars($busqueda) . '"</h4>';
    echo '<small class="d-block mt-1">Campus: ' . htmlspecialchars($campus) . ' | Semestre: ' . htmlspecialchars($semestre) . '</small>';
    echo '</div>';

    // Agrupar resultados planos en estructura jerárquica
    $agrupadas = [];
    foreach ($resultados as $row) {
        $codigo = $row['codigo_asignatura'];
        if (!isset($agrupadas[$codigo])) {
            $agrupadas[$codigo] = [
                'nombre' => $row['nombre_asignatura'],
                'departamento' => $row['departamento'],
                'paralelos' => []
            ];
        }
        
        if (!isset($agrupadas[$codigo]['paralelos'][$row['paralelo']])) {
            $agrupadas[$codigo]['paralelos'][$row['paralelo']] = [
                'cupos' => $row['cupos'],
                'profesores' => explode(', ', $row['profesores']),
                'horario' => []
            ];
        }
        
        if ($row['dia_semana'] && $row['bloque_inicio']) {
            $agrupadas[$codigo]['paralelos'][$row['paralelo']]['horario'][] = [
                'dia' => $row['dia_semana'],
                'bloque' => $row['bloque_inicio'],
                'sala' => $row['sala']
            ];
        }
    }

    // Renderizado
    foreach ($agrupadas as $codigo => $asignatura) {
        echo '<div class="card mb-4">';
        echo '<div class="card-header bg-light">';
        echo '<h5 class="card-title mb-0">';
        echo '<span class="badge bg-primary me-2">' . htmlspecialchars($codigo) . '</span>';
        echo htmlspecialchars($asignatura['nombre']);
        echo '</h5></div>';
        
        echo '<div class="card-body">';
        foreach ($asignatura['paralelos'] as $paralelo => $detalle) {
            mostrar_paralelo($paralelo, $detalle, $asignatura['departamento'], $campus, $semestre, $ocultar_vacios);
        }
        echo '</div></div>';
    }
    echo '</div>';
}

/**
 * @brief Muestra el bloque de información detallada de un paralelo individual.
 * Renderiza la información de cupos, departamento y lista de profesores.
 * Delega la visualización de la tabla de horas a la función mostrar_horario() si existen datos.
 *
 * @param string|int $paralelo Número o identificador del paralelo.
 * @param array $detalle Array asociativo con las claves: 'cupos', 'profesores' (array), y 'horario' (array).
 * @param string $departamento Nombre del departamento académico.
 * @param string $campus Campus actual (pasado para generación de enlaces en sub-funciones).
 * @param string $semestre Semestre actual (pasado para generación de enlaces en sub-funciones).
 * @param bool $ocultar_vacios Configuración para visualizar u ocultar filas vacías en el horario.
 * @return void Genera salida HTML directa.
 */
function mostrar_paralelo($paralelo, $detalle, $departamento, $campus, $semestre, $ocultar_vacios) {
    echo '<div class="mb-4 p-3 border rounded">';
    echo '<h6 class="mb-3">';
    echo '<span class="badge bg-secondary me-2">Paralelo ' . htmlspecialchars($paralelo) . '</span>';
    echo '<small class="text-muted">Cupos: ' . htmlspecialchars($detalle['cupos']) . '</small>';
    echo '</h6>';

    echo '<div class="row mb-3">';
    echo '<div class="col-md-6">';
    echo '<p class="mb-1"><strong>Departamento:</strong> ' . htmlspecialchars($departamento) . '</p>';
    echo '<p class="mb-1"><strong>Profesores:</strong> ' . implode(', ', array_map('htmlspecialchars', $detalle['profesores'])) . '</p>';
    echo '</div></div>';

    if (!empty($detalle['horario'])) {
        mostrar_horario($detalle['horario'], $campus, $semestre, $ocultar_vacios);
    } else {
        echo '<div class="alert alert-primary" role="alert">No hay horario disponible para este paralelo.</div>';
    }
    
    echo '</div>';
}

/**
 * @brief Renderiza la tabla de horario semanal de un paralelo.
 * * Genera una matriz de 10 bloques x 7 días. Rellena las celdas con la información de la sala
 * y crea enlaces a horario_salas.php. Si $ocultar_vacios es true, omite las filas de bloques
 * donde no haya clases ningún día de la semana.
 *
 * @param array $horarios Lista de objetos/arrays con 'dia', 'bloque' y 'sala'.
 * @param string $campus Nombre del campus para los enlaces de las salas.
 * @param string $semestre Código del semestre para los enlaces de las salas.
 * @param bool $ocultar_vacios Si es true, no renderiza las filas de la tabla que estén totalmente vacías.
 * @return void Genera salida HTML directa (<table>).
 */
function mostrar_horario($horarios, $campus, $semestre, $ocultar_vacios) {
    $dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    $horas_bloques = [
        '1-2' => '8.15-9.25', '3-4' => '9.40-10.15', '5-6' => '11.05-12.15',
        '7-8' => '12.30-13.40', '9-10' => '14.40-15.50', '11-12' => '16.05-17.15',
        '13-14' => '17.30-18.40', '15-16' => '18.55-20.05', '17-18' => '20.20-21.30',
        '19-20' => '21.45-22.55'
    ];

    $tabla_horario = array_fill(0, 10, array_fill(0, 7, ''));

    foreach ($horarios as $h) {
        $fila = $h['bloque'] - 1;
        $columna = $h['dia'] - 1;
        $tabla_horario[$fila][$columna] = 'Sala ' . $h['sala'];
    }

    echo '<h6 class="mt-3 mb-2">Horario</h6>';
    echo '<div class="table-responsive">';
    echo '<table class="table table-bordered table-hover table-sm">';
    echo '<thead class="table-light">';
    echo '<tr><th class="text-center">Bloque</th>';
    foreach ($dias_semana as $dia) {
        echo '<th class="text-center">' . $dia . '</th>';
    }
    echo '</tr></thead><tbody>';

    foreach ($tabla_horario as $i => $fila) {
        $bloque_num = ($i * 2 + 1) . '-' . ($i * 2 + 2);
        $hora = $horas_bloques[$bloque_num] ?? '';
        
        if ($ocultar_vacios && implode('', $fila) === '') continue;
        
        echo '<tr>';
        echo '<td class="text-center"><div class="fw-bold">' . $bloque_num . '</div><div class="small text-muted">' . $hora . '</div></td>';
        
        foreach ($fila as $celda) {
            if (!empty($celda)) {
                $sala = preg_replace('/^Sala\s+/i', '', $celda);
                $url = 'horario_salas.php?' . http_build_query([
                    'sala' => $sala,
                    'campus' => $campus,
                    'semestre' => $semestre
                ]);
                echo '<td class="text-center"><a href="' . htmlspecialchars($url) . '" class="btn btn-sm btn-outline-primary">' . htmlspecialchars($celda) . '</a></td>';
            } else {
                echo '<td class="bg-light"></td>';
            }
        }
        echo '</tr>';
    }
    echo '</tbody></table></div>';
}

try {
    if (isset($_GET['codigo'], $_GET['campus'], $_GET['semestre'])) {
        $params = cargar_parametros();
        $resultados = buscar_asignaturas($pdo, $params['busqueda'], $params['campus'], $params['semestre']);
        mostrar_resultados($resultados, $params['campus'], $params['semestre'], $params['busqueda'], $params['ocultar_vacios']);
    }
} catch (Exception $e) {
    error_log("Error en buscar_asignaturas.php: " . $e->getMessage());
    echo '<div class="alert alert-danger mt-4">Ocurrió un error al procesar la búsqueda.</div>';
}
?>