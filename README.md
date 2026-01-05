# 🏜 Sedona ️

**Sedona** es un "visualizador de asignaturas" y horarios de salas desarrollado para facilitar la consulta de disponibilidad de espacios en la UTFSM. Este proyecto busca resolver la dificultad de encontrar salas vacías o consultar el horario específico de una sala a través de SIGA.

Nació como ejercicio personal luego de cursar **INF239 Bases de Datos**.

Sedona hace uso de un script externo (**Piedmont**) para obtener los datos de asignaturas.

[Link a la versión Live del sitio web](https://sedona2.duckdns.org/)

## Características principales

- **Búsqueda de Asignaturas**: Encuentra ramos por código, nombre o profesor y visualiza sus paralelos, cupos y horarios.

- **Horario de Salas**: Consulta qué clases se dictan en una sala específica durante la semana.

- **Buscador de Salas Vacías**: Filtra salas disponibles por campus, día y bloque horario. Incluye una función de "Autofill" para encontrar salas libres en el momento actual.

- **Estadísticas**: Visualización de datos curiosos sobre la carga académica (profesores con más ramos, salas más usadas, etc.).

## Tecnologías utilizadas

- **Backend**: PHP 8+.

- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript (vanilla).

- **Base de Datos**: MariaDB / MySQL.

- **Servidor**: Nginx o Apache.

## Instalación rápida

1. **Clonar el repositorio**:

    ```bash
    git clone https://github.com/frostodev/sedona
    ```

2. **Configurar la Base de Datos**:

	- Crea una base de datos en MariaDB/MySQL llamada `sedona`.
	- Importa el schema de tablas incluido en el repositorio:

        ```bash
        mysql -u root -p sedona < piedmont/sedona_bdd.sql
        ```
	
3. **Configuración**:

    - Navega fuera del directorio público y hacia carpeta de configuración

        ```bash
        cd sedona_config
        ```

    - Copia y renombra el archivo de ejemplo:

        ```bash
        mv config.sample.php config.php
        ```
    
    - Edita `sedona_config/config.php` con las credenciales de la Base de Datos.

4. **Servidor web**:

    - Apunta el `root` del servidor a la carpeta `/sedona` del repositorio.

## Uso de Piedmont

El proyecto incluye un script de Python (`piedmont/piedmont-webscraper.py`) encargado de poblar la base de datos extrayendo información desde el SIGA.

#### Requisitos Previos
El servidor donde se ejecute el scraper debe tener instalado:

- **Python 3.10+**
- **Google Chrome / Chromium**
- **ChromeDriver** (compatible con la versión del navegador instalado)

Instalación de dependencias de Python:

```bash
pip install -r requirements.txt 
```

#### Configuración de credenciales
Piedmont requiere dos archivos de configuración en la carpeta `sedona_config` (fuera del webroot por seguridad):

1. `piedmont_cred.txt`: Credenciales de acceso al SIGA
    - Línea 1: Usuario (@usm.cl)
    - Línea 2: Contraseña

2. `db_config.txt`: Configuración de conexión a la BDD.
    ```bash
    host=localhost
    user=usuario_bdd
    password=password_bdd
    database=sedona
    ```
#### Ejecución
Simplemente ejecutar:
```bash
python3 piedmont/piedmont-webscraper.py
```

## Seguridad

Este proyecto implementa medidas de seguridad estándar para entornos de producción:

- **Consultas seguras**: Uso estricto de PDOs para prevenir inyección SQL.

- **Hardening HTTP**: Headers CSP, X-Frame-Options y protecciones XSS activas.

- **Aislamiento**: Las credenciales de la base de datos residen fuera del directorio público (`webroot`).

- **Validación**: Sanitización estricta de parámetros de entrada.

## ⚠️ Disclaimer

El uso de este software cae puramente bajo la responsabilidad del usuario. Este software no pretende dañar o robar información, su propósito está destinado a fines educativos y de apoyo para los estudiantes. El software, por defecto, sólamente obtiene información de los horarios de la UTFSM, y no modifica ni obtiene otro tipo de información. Ninguno de los datos obtenidos mediante el software, o ingresados por el usuario, son utilizados con fines maliciosos ni subidos a Internet. El software no pide ni pedirá información personal al usuario. Este software debe considerarse en beta, y puede fallar en cualquier momento. Este software no fue desarrollado ni patrocinado por la Universidad Técnica Federico Santa María.

**En resumen, sea responsable y recuerde las clases de Ética de su malla curricular.**
