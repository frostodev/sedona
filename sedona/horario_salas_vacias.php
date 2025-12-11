<?php define('SEDONA_INCLUDED', true); require_once 'header.php'; ?>
<body>
    <main class="container py-4">
        <h2 class="mb-4">Búsqueda de Salas Vacías</h2>

        <?php
        $adv1 = "⚠️ Advertencia: No todas las salas del campus están listadas en SIGA. Pueden existir falso positivos.";
        echo '<div class="alert alert-warning mb-4">' . htmlspecialchars($adv1, ENT_QUOTES, 'UTF-8') . '</div>';
        ?>

        <form method="GET" action="<?php echo htmlspecialchars($_SERVER['PHP_SELF'], ENT_QUOTES, 'UTF-8'); ?>" class="card border-light mb-4">
            <div class="card-body">
                <div class="row g-3">
                    <div class="col-md-4">
                        <label for="campus" class="form-label">Campus:</label>
                        <select name="campus" id="campus" class="form-select" required>
                            <option value="">Cargando campus...</option>
                        </select>
                    </div>

                    <div class="col-md-4">
                        <label for="semestre" class="form-label">Semestre:</label>
                        <select name="semestre" id="semestre" class="form-select" required disabled>
                            <option value="">Primero selecciona un campus</option>
                        </select>
                    </div>

                    <div class="col-md-4">
                        <label for="dia" class="form-label">Día:</label>
                        <select name="dia" id="dia" class="form-select" required>
                            <option value="">Seleccionar día</option>
                            <?php foreach (['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'] as $key => $dia): ?>
                                <option value="<?= $key + 1 ?>" <?= isset($_GET['dia']) && $_GET['dia'] == ($key + 1) ? 'selected' : '' ?>><?= $dia ?></option>
                            <?php endforeach; ?>
                        </select>
                    </div>

                    <div class="col-12">
                        <label class="form-label">Seleccionar bloques:</label>
                        <div class="row row-cols-2 row-cols-sm-3 row-cols-md-4 row-cols-lg-5 g-2">
                            <?php foreach (range(0, 9) as $i):
                                $bloque_inicio = $i * 2 + 1;
                                $bloque_fin = $bloque_inicio + 1;
                                $checked = isset($_GET['bloques']) && in_array($i, $_GET['bloques']) ? 'checked' : '';
                            ?>
                            <div class="col">
                                <div class="form-check">
                                    <input type="checkbox" name="bloques[]" value="<?= $i ?>" id="bloque<?= $i ?>" class="form-check-input" <?= $checked ?>>
                                    <label class="form-check-label" for="bloque<?= $i ?>"><?= "$bloque_inicio-$bloque_fin" ?></label>
                                </div>
                            </div>
                            <?php endforeach; ?>
                        </div>
                    </div>

                    <div class="col-12 d-flex gap-2">
                        <button type="submit" class="btn btn-primary">Buscar</button>
                        <button type="button" id="autofillNowButton" class="btn btn-outline-secondary">Salas vacías ahora</button>
                        <button type="button" id="selectAllBloques" class="btn btn-outline-secondary">Seleccionar todos</button>
                    </div>
                </div>
            </div>
        </form>

        <div id="resultados">
            <?php 
            if (is_file('buscar_salas_vacias.php')) {
                if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset(
                    $_GET['campus'],
                    $_GET['semestre'],
                    $_GET['dia']
                )) {
                    if (!empty($_GET['bloques']) && is_array($_GET['bloques'])) {
                        require_once 'buscar_salas_vacias.php';
                    } else {
                        echo '<div class="alert alert-danger">Debes seleccionar al menos un bloque.</div>';
                    }
                }
            } else {
                echo '<div class="alert alert-danger">Error al cargar resultados.</div>';
            }
            ?>
        </div>
    </main>
</body>

<script src="/js/api.js"></script>
<?php require_once 'footer.php'; ?>

<!-- Espero que me oigas cantar...
	 Esta canción...
	 Y que entiendas la letra...
	 Y que lo escribo para vos.
	 Sé que es una mala idea...
	 Y si no estamos tan cerca sería otra cosa entera...
	 Entera...
	 Es una lástima,
	 Estaría en tu bolsillo,
	 Dios mío.
	 Tan caprichoso soy...
	 Es una lástima. -->