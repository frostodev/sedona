<?php define('SEDONA_INCLUDED', true);
http_response_code(401);
require_once 'header.php';
?>
<body class="d-flex flex-column min-vh-100">
    <main class="container flex-grow-1 d-flex align-items-center">
        <div class="w-100 text-center py-5">
            <div class="mb-4">
                <h1 class="display-1 fw-bold">401</h1>
                <h2 class="display-5 text-muted mb-4">Acceso no autorizado</h2>
                <div class="alert alert-danger mx-auto" style="max-width: 500px;">
                    <i class="bi bi-shield-lock-fill me-2"></i>No tienes permiso para acceder a este recurso
                </div>
            </div>
            
            <div class="poem text-muted mx-auto" style="max-width: 600px;">
                <p class="lead mb-3">"Everything rises and falls.<br>
                Wheel of fortune rules us all...</p>
                <p class="lead mb-3">I lost my group of friends about twelve years ago...<br>
                And again, I'm a snake shedding skin..."</p>
            </div>
            
            <div class="mt-5">
                <a href="/index.php" class="btn btn-primary btn-lg">
                    <i class="bi bi-house-door-fill me-2"></i>Volver al inicio
                </a>
            </div>
        </div>
    </main>
<?php require_once 'footer.php'; ?>

<!-- I was meant to love you and always keep you in my life...
	 I was meant to love you,
	 I knew I loved you at first sight... -->