<footer class="bg-light text-muted py-4 mt-auto border-top">
    <div class="container">
        <div class="row align-items-center">
            <div class="col-md-8 text-md-start mb-3 mb-md-0">
                <p class="mb-1">
                    <strong>2025 © frostodev</strong> · Creado con el 
                    <span class="text-danger"><i class="bi bi-heart-fill"></i></span> 
                    por y para estudiantes de la UTFSM.
                </p>
                <?php
                // Previene el acceso directo a este archivo
                if (!defined('SEDONA_INCLUDED')) {
                    http_response_code(403);
                    die('Acceso denegado.');
                }

                $file = __DIR__ . '/../piedmont/ultima_act_bdd.txt';
                if (file_exists($file)) {
                    $lastUpdate = file_get_contents($file);
                    $date = DateTime::createFromFormat('Y-m-d H-i-s', $lastUpdate);
                    if ($date !== false) {
                        echo "<p class='mb-0'><i class='bi bi-clock-history'></i> Última actualización BDD: <strong>" . $date->format('d/m/Y \a \l\a\s H:i') . "</strong></p>";
                    } else {
                        error_log('Error en footer.php: Fecha en formato no reconocido!');
                        echo "<p class='mb-0 text-warning'><i class='bi bi-exclamation-triangle'></i> Fecha en formato no reconocido.</p>";
                    }
                } else {
                    error_log('Error en footer.php: archivo de última actualización BDD no existe!');
                    echo "<p class='mb-0 text-danger'><i class='bi bi-x-circle'></i> Base de datos nunca actualizada.</p>";
                }
                ?>
            </div>
            <div class="col-md-4 text-md-end">
                <span class="small">
                    <i class="bi bi-code-slash"></i> v1.0-sedona2-sql-beta
                </span>
            </div>
        </div>
    </div>
</footer>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>