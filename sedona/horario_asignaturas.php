<?php define('SEDONA_INCLUDED', true); require_once 'header.php'; ?>
<body>
    <main class="container py-4">
        <h2 class="mb-4">Búsqueda de Asignaturas</h2>

        <?php
        $adv1 = "⚠️ Advertencia: No todos los bloques de ayudantía/laboratorio están públicos en SIGA.";
        echo '<div class="alert alert-warning">' . htmlspecialchars($adv1, ENT_QUOTES, 'UTF-8') . '</div>';
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
                    <div class="col-md-12">
                        <label for="codigo" class="form-label">Buscar por código, nombre o profesor:</label>
                        <div class="input-group">
                            <input type="text" id="codigo" name="codigo" class="form-control"
                                value="<?php echo isset($_GET['codigo']) ? htmlspecialchars($_GET['codigo'], ENT_QUOTES, 'UTF-8') : ''; ?>"
                                placeholder="Ej: Bases de Datos, INF155, MAT024-203" required maxlength="100"
                                pattern="[a-zA-Z0-9 áéíóúüÁÉÍÓÚÜñÑ\-]{1,100}">
                        </div>
                    </div>

                    <!-- Checkbox para ocultar bloques vacíos -->
                    <div class="col-md-12">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="ocultar_vacios" value="1" 
                                <?php if (!empty($_GET['ocultar_vacios'])) echo 'checked'; ?> id="ocultarVacios">
                            <label class="form-check-label" for="ocultarVacios">
                                Ocultar bloques vacíos
                            </label>
                        </div>
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
            if (is_file('buscar_asignaturas.php')) {
                if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset(
                    $_GET['campus'], 
                    $_GET['semestre'], 
                    $_GET['codigo']
                )) {
                    require_once 'buscar_asignaturas.php';
                }
            } else {
                error_log("Error general en horario_asignaturas.php: No se encuentra buscar_asignaturas.php!");
                echo '<div class="alert alert-danger">Error al cargar resultados.</div>';
            }
            ?>
        </div>
    </main>
</body>

<script src="/js/api.js"></script>
<?php require_once 'footer.php'; ?>

<!-- I can't get you out of my mind, thought I've might dreamed it...
     You made me feel something that night I swore I never needed...
     I was doing fine 'til I let you in my mind...
     Honey, what the hell d'you do to me? -->