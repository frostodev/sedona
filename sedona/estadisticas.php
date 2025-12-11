<?php
/**
 * Página de Estadísticas Académicas.
 * Muestra métricas generales y específicas sobre la carga académica,
 * permitiendo filtrar por campus y semestre o ver datos históricos globales.
 * * @package Sedona
 */

define('SEDONA_INCLUDED', true);
require_once 'conexion.php';

// --- Lógica de Filtrado ---

// Obtener parámetros de filtro sanitizados
$campus_filtro = filter_input(INPUT_GET, 'campus', FILTER_SANITIZE_SPECIAL_CHARS);
$semestre_filtro = filter_input(INPUT_GET, 'semestre', FILTER_SANITIZE_SPECIAL_CHARS);
$hay_filtro = ($campus_filtro && $semestre_filtro);

// Variables para construir las consultas dinámicamente
$join_base_semestre = ""; // Joins necesarios para llegar a semestre/campus desde asignatura
$where_clause = "";       // Cláusula WHERE
$params = [];             // Parámetros para PDO

if ($hay_filtro) {
    $join_base_semestre = " JOIN semestre s ON a.semestre_id = s.id JOIN campus c ON s.campus_id = c.id ";
    $where_clause = " WHERE c.nombre = :campus AND s.codigo = :semestre ";
    $params = [':campus' => $campus_filtro, ':semestre' => $semestre_filtro];
}

/**
 * Convierte el número de día de la semana a texto.
 * @param int $numero 1=Lunes, 7=Domingo.
 * @return string Nombre del día.
 */
function convertir_dia($numero) {
    $dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    return $dias[$numero - 1] ?? 'Desconocido';
}

// --- Consultas de Totales ---

// Total Asignaturas
$sql = "SELECT COUNT(*) AS total FROM asignatura a" . ($hay_filtro ? $join_base_semestre . $where_clause : "");
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$total_asignaturas = $stmt->fetch(PDO::FETCH_ASSOC)['total'];

// Total Paralelos
$sql = "SELECT COUNT(*) AS total FROM paralelo p JOIN asignatura a ON p.asignatura_id = a.id" . ($hay_filtro ? $join_base_semestre . $where_clause : "");
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$totalParalelos = $stmt->fetch(PDO::FETCH_ASSOC)['total'];

// Total Profesores (Excluyendo NN)
if ($hay_filtro) {
    // Si hay filtro, contamos solo los profesores activos en ese semestre/campus
    $sql = "
        SELECT COUNT(DISTINCT pp.profesor_id) AS total 
        FROM paralelo_profesor pp
        JOIN paralelo p ON pp.paralelo_id = p.id
        JOIN asignatura a ON p.asignatura_id = a.id
        JOIN profesor pr ON pp.profesor_id = pr.id
        $join_base_semestre
        $where_clause
        AND pr.nombre != 'NN'
    ";
} else {
    // Si es global, contamos todos los profesores registrados en la BDD
    $sql = "SELECT COUNT(*) AS total FROM profesor WHERE nombre != 'NN'";
}
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$total_profesores = $stmt->fetch(PDO::FETCH_ASSOC)['total'];


// --- Consultas de Rankings (Top 1) ---

// Profesor con más paralelos (Excluyendo NN)
$sql = "
    SELECT pr.nombre, COUNT(*) AS total_paralelos
    FROM profesor pr
    JOIN paralelo_profesor pp ON pr.id = pp.profesor_id
    JOIN paralelo p ON pp.paralelo_id = p.id
    JOIN asignatura a ON p.asignatura_id = a.id
    " . ($hay_filtro ? $join_base_semestre . $where_clause . " AND " : " WHERE ") . " pr.nombre != 'NN'
    GROUP BY pr.id
    ORDER BY total_paralelos DESC
    LIMIT 1
";
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$profesor_mas_paralelos = $stmt->fetch(PDO::FETCH_ASSOC);

// Profesor con más asignaturas distintas (Excluyendo NN)
$sql = "
    SELECT pr.nombre, COUNT(DISTINCT a.id) AS total_asignaturas
    FROM profesor pr
    JOIN paralelo_profesor pp ON pr.id = pp.profesor_id
    JOIN paralelo p ON pp.paralelo_id = p.id
    JOIN asignatura a ON p.asignatura_id = a.id
    " . ($hay_filtro ? $join_base_semestre . $where_clause . " AND " : " WHERE ") . " pr.nombre != 'NN'
    GROUP BY pr.id
    ORDER BY total_asignaturas DESC
    LIMIT 1
";
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$profesor_mas_asignaturas = $stmt->fetch(PDO::FETCH_ASSOC);

// Día con más bloques horarios
$sql = "
    SELECT h.dia_semana, COUNT(*) AS total_bloques
    FROM horario h
    JOIN paralelo p ON h.paralelo_id = p.id
    JOIN asignatura a ON p.asignatura_id = a.id
    " . ($hay_filtro ? $join_base_semestre . $where_clause : "") . "
    GROUP BY h.dia_semana
    ORDER BY total_bloques DESC
    LIMIT 1
";
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$dia_mas_ocupado = $stmt->fetch(PDO::FETCH_ASSOC);

// Asignatura con más profesores distintos (Excluyendo NN)
$sql = "
    SELECT a.nombre, COUNT(DISTINCT pp.profesor_id) AS total_profesores
    FROM asignatura a
    JOIN paralelo p ON a.id = p.asignatura_id
    JOIN paralelo_profesor pp ON p.id = pp.paralelo_id
    JOIN profesor pr ON pp.profesor_id = pr.id
    " . ($hay_filtro ? $join_base_semestre . $where_clause . " AND " : " WHERE ") . " pr.nombre != 'NN'
    GROUP BY a.id
    ORDER BY total_profesores DESC
    LIMIT 1
";
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$asignatura_mas_profesores = $stmt->fetch(PDO::FETCH_ASSOC);

// Sala más utilizada
$sql = "
    SELECT h.sala, COUNT(*) AS usos 
    FROM horario h
    JOIN paralelo p ON h.paralelo_id = p.id
    JOIN asignatura a ON p.asignatura_id = a.id
    " . ($hay_filtro ? $join_base_semestre . $where_clause : "") . "
    GROUP BY h.sala 
    ORDER BY usos DESC 
    LIMIT 1
";
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$sala_mas_usada = $stmt->fetch(PDO::FETCH_ASSOC);

// Asignatura con mayor cantidad de paralelos
$sql = "
    SELECT a.nombre, COUNT(p.id) AS total_paralelos
    FROM asignatura a
    JOIN paralelo p ON a.id = p.asignatura_id
    " . ($hay_filtro ? $join_base_semestre . $where_clause : "") . "
    GROUP BY a.id
    ORDER BY total_paralelos DESC
    LIMIT 1
";
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$asignatura_mas_paralelos = $stmt->fetch(PDO::FETCH_ASSOC);

?>
<?php require_once 'header.php'; ?>
<body>
    <main class="container py-4">
        <div class="row g-4">
            <div class="col-12">
                <h1 class="display-4 mb-2">Estadísticas Académicas</h1>
            </div>

            <!-- Panel de Filtros -->
            <div class="col-12">
                <div class="card border-light shadow-sm">
                    <div class="card-body bg-light">
                        <form method="GET" action="estadisticas.php" class="row g-3 align-items-end">
                            <div class="col-md-4">
                                <label for="campus" class="form-label fw-bold">Campus:</label>
                                <select name="campus" id="campus" class="form-select">
                                    <option value="">Cargando...</option>
                                </select>
                            </div>
                            <div class="col-md-4">
                                <label for="semestre" class="form-label fw-bold">Semestre:</label>
                                <select name="semestre" id="semestre" class="form-select" disabled>
                                    <option value="">Selecciona un campus</option>
                                </select>
                            </div>
                            <div class="col-md-4 d-flex gap-2">
                                <button type="submit" class="btn btn-primary w-100">
                                    <i class="bi bi-funnel-fill me-1"></i> Filtrar
                                </button>
                                <?php if ($hay_filtro): ?>
                                    <a href="estadisticas.php" class="btn btn-outline-secondary w-100">
                                        <i class="bi bi-globe me-1"></i> Ver Global
                                    </a>
                                <?php else: ?>
                                    <button type="button" class="btn btn-secondary w-100" disabled>
                                        <i class="bi bi-globe me-1"></i> Vista Global
                                    </button>
                                <?php endif; ?>
                            </div>
                        </form>
                    </div>
                </div>
            </div>

            <?php if ($hay_filtro): ?>
                <div class="col-12">
                    <div class="alert alert-info d-flex align-items-center">
                        <i class="bi bi-info-circle-fill me-2"></i>
                        <div>
                            Viendo estadísticas filtradas para: <strong><?= htmlspecialchars($campus_filtro) ?> - <?= htmlspecialchars($semestre_filtro) ?></strong>
                        </div>
                    </div>
                </div>
            <?php endif; ?>

            <!-- Estadísticas Generales -->
            <div class="col-lg-4">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-primary text-white">
                        <h3 class="h5 mb-0"><i class="bi bi-bar-chart-fill me-2"></i>Datos Generales</h3>
                    </div>
                    <div class="card-body">
                        <div class="list-group list-group-flush">
                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                <span><i class="bi bi-journal-bookmark me-2"></i>Asignaturas</span>
                                <span class="badge bg-primary rounded-pill"><?= number_format($total_asignaturas) ?></span>
                            </div>
                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                <span><i class="bi bi-people-fill me-2"></i>Paralelos</span>
                                <span class="badge bg-primary rounded-pill"><?= number_format($totalParalelos) ?></span>
                            </div>
                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                <span><i class="bi bi-person-badge-fill me-2"></i>Profesores</span>
                                <span class="badge bg-primary rounded-pill"><?= number_format($total_profesores) ?></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Gráfico -->
            <div class="col-lg-8">
                <div class="card shadow-sm">
                    <div class="card-header bg-primary text-white">
                        <h3 class="h5 mb-0"><i class="bi bi-pie-chart-fill me-2"></i>Distribución Académica</h3>
                    </div>
                    <div class="card-body">
                        <div class="chart-container" style="position: relative; height:300px; width:100%">
                            <canvas id="estadisticasChart" 
                                    data-asignaturas="<?= $total_asignaturas ?>" 
                                    data-paralelos="<?= $totalParalelos ?>" 
                                    data-profesores="<?= $total_profesores ?>">
                            </canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Profesores Destacados -->
            <div class="col-md-6">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-success text-white">
                        <h3 class="h5 mb-0"><i class="bi bi-award-fill me-2"></i>Profesores Destacados</h3>
                    </div>
                    <div class="card-body">
                        <div class="list-group">
                            <div class="list-group-item">
                                <h5 class="mb-1"><i class="bi bi-trophy-fill text-warning me-2"></i>Más paralelos</h5>
                                <?php if ($profesor_mas_paralelos): ?>
                                    <p class="mb-0"><?= htmlspecialchars($profesor_mas_paralelos['nombre']) ?>
                                        <span class="badge bg-success ms-2"><?= $profesor_mas_paralelos['total_paralelos'] ?> paralelos</span>
                                    </p>
                                <?php else: ?>
                                    <p class="text-muted mb-0">Sin datos suficientes.</p>
                                <?php endif; ?>
                            </div>
                            <div class="list-group-item">
                                <h5 class="mb-1"><i class="bi bi-stars text-warning me-2"></i>Más asignaturas</h5>
                                <?php if ($profesor_mas_asignaturas): ?>
                                    <p class="mb-0"><?= htmlspecialchars($profesor_mas_asignaturas['nombre']) ?>
                                        <span class="badge bg-success ms-2"><?= $profesor_mas_asignaturas['total_asignaturas'] ?> asignaturas</span>
                                    </p>
                                <?php else: ?>
                                    <p class="text-muted mb-0">Sin datos suficientes.</p>
                                <?php endif; ?>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Datos Relevantes -->
            <div class="col-md-6">
                <div class="card shadow-sm h-100">
                    <div class="card-header bg-info text-white">
                        <h3 class="h5 mb-0"><i class="bi bi-graph-up-arrow me-2"></i>Datos Relevantes</h3>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li class="mb-3">
                                <h5 class="mb-1"><i class="bi bi-calendar-event me-2"></i>Día más ocupado</h5>
                                <?php if ($dia_mas_ocupado): ?>
                                    <p class="mb-0"><?= convertir_dia($dia_mas_ocupado['dia_semana']) ?>
                                        <span class="badge bg-info"><?= $dia_mas_ocupado['total_bloques'] ?> bloques</span>
                                    </p>
                                <?php else: ?>
                                    <p class="text-muted">Sin datos.</p>
                                <?php endif; ?>
                            </li>
                            <li class="mb-3">
                                <h5 class="mb-1"><i class="bi bi-door-open-fill me-2"></i>Sala más usada</h5>
                                <?php if ($sala_mas_usada): ?>
                                    <p class="mb-0"><?= htmlspecialchars($sala_mas_usada['sala']) ?>
                                        <span class="badge bg-info"><?= $sala_mas_usada['usos'] ?> usos</span>
                                    </p>
                                <?php else: ?>
                                    <p class="text-muted">Sin datos.</p>
                                <?php endif; ?>
                            </li>
                            <li>
                                <h5 class="mb-1"><i class="bi bi-collection-fill me-2"></i>Asignatura con más paralelos</h5>
                                <?php if ($asignatura_mas_paralelos): ?>
                                    <p class="mb-0"><?= htmlspecialchars($asignatura_mas_paralelos['nombre']) ?>
                                        <span class="badge bg-info"><?= $asignatura_mas_paralelos['total_paralelos'] ?> paralelos</span>
                                    </p>
                                <?php else: ?>
                                    <p class="text-muted">Sin datos.</p>
                                <?php endif; ?>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script src="js/api.js"></script>
    <script src="js/chart.js"></script>
    <script src="js/graficos.js"></script>
<?php require_once 'footer.php'; ?>

<!-- Sometimes when I'm with you, it makes me wanna get better...
	 And sometimes when I'm with you, I like to enjoy the weather...
	 And sometimes seems to be enough to make me wanna get better...
	 Cause sometimes you are all I have, and sometimes is better than never... -->