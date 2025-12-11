<?php define('SEDONA_INCLUDED', true);
http_response_code(404);
require_once 'header.php';
?>
<body class="d-flex flex-column min-vh-100">
    <main class="container flex-grow-1 d-flex align-items-center">
        <div class="w-100 text-center py-5">
            <div class="mb-4">
                <h1 class="display-1 fw-bold">404</h1>
                <h2 class="display-5 text-muted mb-4">Página no encontrada</h2>
                <div class="alert alert-info mx-auto" style="max-width: 500px;">
                    <i class="bi bi-binoculars-fill me-2"></i>El recurso solicitado no existe
                </div>
            </div>
            
            <div class="poem text-muted mx-auto" style="max-width: 600px;">
                <p class="lead mb-3">"Nostalgic for memories, I haven't had...<br>
                I can't put my finger on it...</p>
                <p class="lead mb-3">There are all these things...<br>
                that I'll never know..."</p>
            </div>
            
            <div class="mt-5">
                <a href="/index.php" class="btn btn-primary btn-lg">
                    <i class="bi bi-house-door-fill me-2"></i>Volver al inicio
                </a>
            </div>
        </div>
    </main>
<?php require_once 'footer.php'; ?>

<!-- K❤️ -->