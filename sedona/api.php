<?php
/**
 * API Endpoint para selectores dinámicos.
 * Este archivo devuelve fragmentos HTML (<option>) para ser inyectados
 * vía AJAX en los selectores de la interfaz (Campus -> Semestre -> Asignatura).
 * @package Sedona
 */

define('SEDONA_INCLUDED', true);
require_once 'conexion.php';

/**
 * @brief Renderiza las opciones HTML para un elemento <select>.
 *
 * @param PDOStatement $stmt Statement ejecutado con los resultados.
 * @param string $valueKey Nombre de la columna DB para el atributo 'value'.
 * @param callable $textCallback Función callback para formatear el texto visible.
 * @param string $selectedValue Valor que debe estar pre-seleccionado.
 * @param string $defaultLabel Texto de la opción por defecto (ej: 'Seleccionar...').
 */
function responder_opciones($stmt, $valueKey, $textCallback, $selectedValue = '', $defaultLabel = 'Seleccionar...') {
    echo "<option value=\"\">$defaultLabel</option>";
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $value = htmlspecialchars($row[$valueKey], ENT_QUOTES, 'UTF-8');
        $text = call_user_func($textCallback, $row);
        $selected = ($value === $selectedValue) ? 'selected' : '';
        echo "<option value=\"$value\" $selected>$text</option>";
    }
}

/**
 * @brief Obtiene y limpia un parámetro GET.
 *
 * @param string $key Clave del parámetro GET.
 * @param string $default Valor por defecto si no existe.
 * @return string Valor limpio.
 */
function limpiar_input($key, $default = '') {
    return isset($_GET[$key]) ? trim($_GET[$key]) : $default;
}

try {
    // Lista blanca de acciones permitidas para evitar llamadas arbitrarias
    $acciones = ['campus', 'semestres', 'asignaturas', 'paralelos'];
    $accion = limpiar_input('action');

    if (!in_array($accion, $acciones)) {
        error_log('Intento de acción inválida en api.php: ' . $accion);
        throw new Exception('Acción inválida');
    }

    switch ($accion) {
        case 'campus':
            $campusSel = limpiar_input('selected');
            // Consulta directa de nombres de campus
            $stmt = $pdo->query("SELECT nombre FROM campus ORDER BY nombre");
            responder_opciones(
                $stmt, 
                'nombre', 
                fn($row) => htmlspecialchars($row['nombre'], ENT_QUOTES, 'UTF-8'), 
                $campusSel, 
                'Seleccionar campus'
            );
            break;

        case 'semestres':
            $campus = limpiar_input('campus');
            $semSel = limpiar_input('selected');

            if (empty($campus)) {
                echo '<option value="">Primero selecciona un campus</option>';
                break;
            }

            $stmt = $pdo->prepare("
                SELECT s.codigo 
                FROM semestre s
                JOIN campus c ON s.campus_id = c.id
                WHERE c.nombre = ?
                ORDER BY s.codigo DESC
            ");
            $stmt->execute([$campus]);

            if ($stmt->rowCount() === 0) {
                echo '<option value="">No hay semestres disponibles</option>';
                break;
            }

            responder_opciones(
                $stmt, 
                'codigo', 
                fn($row) => htmlspecialchars($row['codigo'], ENT_QUOTES, 'UTF-8'), 
                $semSel, 
                'Seleccionar semestre'
            );
            break;

        case 'asignaturas':
            $semestre = limpiar_input('semestre');
            $asigSel = limpiar_input('selected');

            if (empty($semestre)) {
                echo '<option value="">Primero selecciona un semestre</option>';
                break;
            }

            $stmt = $pdo->prepare("
                SELECT a.id, a.codigo, a.nombre
                FROM asignatura a
                JOIN semestre s ON a.semestre_id = s.id
                WHERE s.codigo = ?
                ORDER BY a.nombre
            ");
            $stmt->execute([$semestre]);

            if ($stmt->rowCount() === 0) {
                echo '<option value="">No hay asignaturas disponibles</option>';
                break;
            }

            responder_opciones(
                $stmt,
                'id',
                fn($row) => htmlspecialchars("{$row['codigo']} - {$row['nombre']}", ENT_QUOTES, 'UTF-8'),
                $asigSel,
                'Seleccionar asignatura'
            );
            break;

        case 'paralelos':
            $asigId = limpiar_input('asignatura_id');

            // Validación estricta: el ID de asignatura debe ser numérico
            if (!ctype_digit($asigId)) {
                echo '<option value="">ID de asignatura inválido</option>';
                break;
            }

            $stmt = $pdo->prepare("
                SELECT id, paralelo
                FROM paralelo
                WHERE asignatura_id = ?
                ORDER BY paralelo
            ");
            $stmt->execute([$asigId]);

            if ($stmt->rowCount() === 0) {
                echo '<option value="">No hay paralelos disponibles</option>';
                break;
            }

            responder_opciones(
                $stmt,
                'id',
                fn($row) => htmlspecialchars($row['paralelo'], ENT_QUOTES, 'UTF-8'),
                '', 
                'Seleccionar paralelo'
            );
            break;
    }

} catch (PDOException $e) {
    error_log("Error DB en api.php: " . $e->getMessage());
    echo '<option value="">Error al cargar datos</option>';
    
} catch (Exception $e) {
    error_log("Error general en api.php: " . $e->getMessage());
    echo '<option value="">Error inesperado</option>';
}
?>