<?php
/**
 * Header principal del sitio.
 * Este archivo maneja el inicio de sesión, la configuración de cabeceras de seguridad HTTP
 * y la estructura HTML inicial (DOCTYPE, head, apertura del body y barra de navegación)
 * * @package Sedona
 */

// Previene el acceso directo a este archivo
if (!defined('SEDONA_INCLUDED')) {
    http_response_code(403);
    die('Acceso denegado.');
}

// Iniciar el buffer de salida para prevenir errores de "headers already sent"
ob_start(); 

// Configuración de codificación
header('Content-Type: text/html; charset=utf-8');

// --- Headers de Seguridad (Hardening) ---

// Previene que el navegador "adivine" el tipo de contenido (MIME sniffing)
header('X-Content-Type-Options: nosniff');

// Content Security Policy (CSP): La defensa más fuerte contra XSS.
// Permite:
// 1. Scripts: Solo del mismo dominio ('self') y CDN de confianza (cdn.jsdelivr.net).
// 2. Estilos: Mismo dominio, CDN y 'unsafe-inline' (necesario para algunos estilos de Bootstrap/JS).
// 3. Fuentes: Mismo dominio y CDN.
// 4. Imágenes: Mismo dominio y data URIs (para gráficos generados).
header("Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; font-src 'self' https://cdn.jsdelivr.net; img-src 'self' data:;");

// Previene que el sitio sea cargado dentro de un iframe (protección contra Clickjacking)
header("X-Frame-Options: DENY");

// Habilita el filtro XSS integrado en navegadores antiguos
header("X-XSS-Protection: 1; mode=block");

// Strict-Transport-Security (HSTS)
// header("Strict-Transport-Security: max-age=31536000; includeSubDomains");

?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    
    <link rel="icon" href="/img/favicon.ico" type="image/x-icon">
    <title>Sedona (beta)</title>
    
    <link rel="stylesheet" href="/css/styles.css">
</head>
<body class="d-flex flex-column min-vh-100">

<nav class="navbar navbar-expand-lg navbar-light bg-light shadow-sm">
    <div class="container">
        <a class="navbar-brand" href="/index.php">
            Sedona <span class="badge bg-secondary align-top small">beta</span>
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse justify-content-end" id="navbarNav">
            <div class="d-flex flex-wrap gap-2">
                <a href="/index.php" class="btn btn-primary">
                    <i class="bi bi-house-door"></i> Inicio
                </a>
                <a href="/horario_asignaturas.php" class="btn btn-success">
                    <i class="bi bi-calendar3"></i> Horario Asignaturas
                </a>
                <a href="/horario_salas.php" class="btn btn-warning">
                    <i class="bi bi-door-open"></i> Horario Salas
                </a>
                <a href="/horario_salas_vacias.php" class="btn btn-info">
                    <i class="bi bi-hourglass-split"></i> Salas Vacías
                </a>
                <a href="/estadisticas.php" class="btn btn-dark">
                    <i class="bi bi-bar-chart"></i> Estadísticas
                </a>
            </div>
        </div>
    </div>
</nav>