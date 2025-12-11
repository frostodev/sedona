<?php define('SEDONA_INCLUDED', true); require_once 'header.php'; ?>
<body>
    <main class="container py-4">
        <h2 class="mb-4">Horario por Sala</h2>

        <?php
        $adv1 = "⚠️ Advertencia: No se muestran horarios de certámenes/ayudantías/tutorías no incluidas en SIGA. También se debe considerar que actividades extraprogramáticas (asambleas, etc) no están en SIGA.";
        echo '<div class="alert alert-warning mb-4">' . htmlspecialchars($adv1, ENT_QUOTES, 'UTF-8') . '</div>';
        ?>

        <form method="GET" action="<?php echo htmlspecialchars($_SERVER['PHP_SELF'], ENT_QUOTES, 'UTF-8'); ?>" class="card border-light mb-4">
            <div class="card-body">
                <div class="row g-3">
                    <!-- Selector de Campus -->
                    <div class="col-md-4">
                        <label for="campus" class="form-label">Campus:</label>
                        <select name="campus" id="campus" class="form-select" required>
                            <option value="">Cargando campus...</option>
                        </select>
                    </div>

                    <!-- Selector de Semestre -->
                    <div class="col-md-4">
                        <label for="semestre" class="form-label">Semestre:</label>
                        <select name="semestre" id="semestre" class="form-select" required disabled>
                            <option value="">Primero selecciona un campus</option>
                        </select>
                    </div>

                    <!-- Campo de búsqueda -->
                    <div class="col-md-4">
                        <label for="sala" class="form-label">Nombre de sala:</label>
                        <input type="text" id="sala" name="sala" 
                               class="form-control"
                               value="<?php echo isset($_GET['sala']) ? htmlspecialchars($_GET['sala'], ENT_QUOTES, 'UTF-8') : ''; ?>" 
                               placeholder="Ej: K101" 
                               pattern="[A-Za-z0-9\s\-]+" 
                               required>
                    </div>

                    <!-- Botón de búsqueda -->
                    <div class="col-md-12">
                        <button type="submit" class="btn btn-primary">Buscar</button>
                    </div>
                </div>
            </div>
        </form>

        <div id="resultados">
            <?php 
            if (is_file('buscar_salas.php')) {
                if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset(
                    $_GET['campus'], 
                    $_GET['semestre'], 
                    $_GET['sala']
                )) {
                    require_once 'buscar_salas.php';
                }
            } else {
                error_log('Error general en horario_salas.php: No se encuentra buscar_salas.php!');
                echo '<div class="alert alert-danger">Error al cargar resultados.</div>';
            }
            ?>
        </div>
    </main>
</body>

<script src="/js/api.js"></script>
<?php require_once 'footer.php'; ?>

<!-- You were the right way...
     I was just waitin' for you to look at me... 
     You are the right one...
     And I'm just the boy who is lookin' at you. -->