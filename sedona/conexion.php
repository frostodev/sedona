<?php
/**
 * Archivo de conexión a la Base de Datos.
 * Establece la conexión PDO con la base de datos MySQL/MariaDB.
 * Maneja las credenciales de forma segura importándolas desde un directorio
 * fuera del webroot.
 * @package Sedona
 */

// Previene el acceso directo a este archivo para evitar ejecución no deseada
if (!defined('SEDONA_INCLUDED')) {
    header("HTTP/1.1 403 Forbidden");
    header("Location: /403.php");
    exit();
}

// Importación de credenciales desde fuera del directorio público
require_once __DIR__ . '/../sedona_config/config.php';

try {
    // Configuración del DSN (Data Source Name)
    // Se fuerza UTF-8 para evitar problemas de codificación con tildes y caracteres especiales.
    $dsn = "mysql:host=$host;dbname=$dbname;charset=utf8mb4";
    
    $options = [
        // Lanzar excepciones en caso de error, esencial para bloques try-catch
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        // Configurar el fetch por defecto a array asociativo
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        // Desactivar la emulación de prepared statements para mayor seguridad real
        PDO::ATTR_EMULATE_PREPARES => false,
    ];

    $pdo = new PDO($dsn, $user, $password, $options);
	
} catch (PDOException $e) {
    // Registrar el error real en el log del servidor (no visible al usuario)
    error_log('Error crítico de conexión a BDD: ' . $e->getMessage());
    
    // Mensaje genérico para no revelar información sensible (IPs, usuarios, etc.)
    http_response_code(500);
    die('Lo sentimos, hubo un error interno de conexión a la base de datos. Por favor intente más tarde.');
}
?>