"""
Web-Scraper para el SIGA (Codename "Piedmont").

Este script automatiza la extracción de información académica (asignaturas, horarios, profesores)
desde el portal SIGA de la Universidad Técnica Federico Santa María utilizando Selenium.
Los datos extraídos son normalizados y almacenados en una base de datos MySQL.

@author frostodev
@version 1.5 
"""

import os
import re
import json
import math
import time
import sys
import shutil
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import mysql.connector
from mysql.connector import Error
from colorama import Fore, Style, init


############################################################################
#                             MANEJO DE BDD                                #

def insertarJsonHaciaBDD(cursor, data):
    """
    Inserta los datos extraídos (JSON) en la base de datos MySQL.
 
    En lugar de consultar la BDD por cada asignatura/profesor (lo que generaría 
    miles de queries), cargamos todos los IDs existentes en memoria al inicio.
    Esto convierte un proceso O(N) de red en un proceso O(1) de memoria RAM.
    """
    # Procesar campus
    campus_name = next(iter(data.keys()))
    printInfo(f"Iniciando importación TURBO para: {campus_name}", color="info")
    
    # Gestión de Campus
    cursor.execute("SELECT id FROM campus WHERE nombre = %s", (campus_name,))
    campus_result = cursor.fetchone()
    
    if not campus_result:
        printInfo(f"Creando campus {campus_name}...", color="info")
        cursor.execute("INSERT INTO campus (nombre) VALUES (%s)", (campus_name,))
        campus_id = cursor.lastrowid
    else:
        campus_id = campus_result[0]
        printInfo(f"Campus ID: {campus_id}", color="info")

    # Precarga de caché (La magia de la velocidad)
    printInfo("Cargando caché de profesores y asignaturas en RAM...", color="advertencia")
    
    # Cargar TODOS los profesores de una vez a un diccionario {nombre: id}
    cursor.execute("SELECT nombre, id FROM profesor")
    cache_profesores = {row[0]: row[1] for row in cursor.fetchall()}
    printInfo(f"Caché Profesores: {len(cache_profesores)} registros en memoria.", color="info")
    
    print("")

    # Procesar semestre
    for semestre_key, semestre_data in data[campus_name].items():
        # Convertir formato del semestre (ej: 20251 a 2025-1)
        codigo = f"{semestre_key[:4]}-{semestre_key[4]}"
        printInfo(f"Procesando semestre: {codigo}", color="info")
        
        cursor.execute("SELECT id FROM semestre WHERE campus_id = %s AND codigo = %s", (campus_id, codigo))
        semestre_result = cursor.fetchone()
        
        if not semestre_result:
            cursor.execute("INSERT INTO semestre (campus_id, codigo) VALUES (%s, %s)", (campus_id, codigo))
            semestre_id = cursor.lastrowid
        else:
            semestre_id = semestre_result[0]
            
        # Cargar asignaturas de ESTE semestre a memoria para evitar duplicados sin consultar BDD
        cursor.execute("SELECT codigo, id FROM asignatura WHERE semestre_id = %s", (semestre_id,))
        cache_asignaturas = {row[0]: row[1] for row in cursor.fetchall()}

        # Procesar asignaturas
        for codigo_asig, paralelos in semestre_data.items():
            # Verificamos en RAM primero
            asignatura_id = cache_asignaturas.get(codigo_asig)
            
            # Datos generales de la asignatura (tomamos del primer paralelo)
            meta_data = paralelos[0]

            if not asignatura_id:
                # Si no existe, insertamos y actualizamos la caché RAM
                printInfo(f"SQL: Creando Asignatura {codigo_asig} - {meta_data['Nombre']}", color="info")
                cursor.execute(
                    "INSERT INTO asignatura (semestre_id, codigo, nombre, departamento) VALUES (%s, %s, %s, %s)",
                    (semestre_id, codigo_asig, meta_data['Nombre'], meta_data['Departamento'])
                )
                asignatura_id = cursor.lastrowid
                cache_asignaturas[codigo_asig] = asignatura_id # Actualizamos caché al vuelo
            
            for paralelo_data in paralelos:
                printInfo(f"SQL: Proc. {codigo_asig} - P{paralelo_data['Paralelo']}", color="info")

                # Insertar Paralelo
                cursor.execute(
                    """
                    INSERT INTO paralelo (asignatura_id, paralelo, cupos)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id), cupos=%s
                    """,
                    (asignatura_id, paralelo_data['Paralelo'], paralelo_data['Cupos'], paralelo_data['Cupos'])
                )
                paralelo_id = cursor.lastrowid
                
                # Profesores
                for profesor_nombre in paralelo_data['Profesores']:
                    profesor_nombre = profesor_nombre.replace(" null", "").strip()
                    if not profesor_nombre: continue

                    # Verificamos ID en RAM
                    profesor_id = cache_profesores.get(profesor_nombre)

                    if profesor_id is None:
                        # Si es un profe nuevo, a la BDD y luego a la RAM
                        cursor.execute("INSERT INTO profesor (nombre) VALUES (%s)", (profesor_nombre,))
                        profesor_id = cursor.lastrowid
                        cache_profesores[profesor_nombre] = profesor_id
                        printInfo(f"    + Nuevo Profesor registrado: {profesor_nombre}", color="info", caja=False)
                    
                    # Insertar relación
                    cursor.execute(
                        "INSERT IGNORE INTO paralelo_profesor (paralelo_id, profesor_id) VALUES (%s, %s)",
                        (paralelo_id, profesor_id)
                    )
                
                # Procesar Horario
                for bloque_idx, dias in enumerate(paralelo_data['Horario']):
                    for dia_idx, sala in enumerate(dias):
                        sala_norm = sala.strip()
                        if sala_norm:
                            if sala_norm.startswith("Sala "): sala_norm = sala_norm[5:]
                            
                            cursor.execute(
                                """INSERT INTO horario 
                                (paralelo_id, dia_semana, bloque_inicio, sala)
                                VALUES (%s, %s, %s, %s)""",
                                (paralelo_id, dia_idx + 1, bloque_idx + 1, sala_norm)
                            )
                            printInfo(f"    + Horario: D{dia_idx + 1}/B{bloque_idx + 1} -> {sala_norm}", color="info")
                    printInfo(f"    + Vinculando Profesor: {profesor_nombre} (ID: {profesor_id})", color="info")
                
                # Procesar Horario
                for bloque_idx, dias in enumerate(paralelo_data['Horario']):
                    for dia_idx, sala in enumerate(dias):
                        sala_normalizada = sala.strip()
                        
                        if sala_normalizada:
                            # Eliminar prefijo "Sala " si existe al inicio
                            if sala_normalizada.startswith("Sala "):
                                sala_normalizada = sala_normalizada[5:]
                            
                            cursor.execute(
                                """INSERT INTO horario 
                                (paralelo_id, dia_semana, bloque_inicio, sala)
                                VALUES (%s, %s, %s, %s)""",
                                (paralelo_id, 
                                 dia_idx + 1,
                                 bloque_idx + 1,
                                 sala_normalizada)
                            )
                            printInfo(f"    + Horario Agregado: Día {dia_idx + 1}, Bloque {bloque_idx + 1} en {sala_normalizada}", color="info")

def prepararConexionBDD():
    """
    Establece la conexión con la base de datos, gestiona la limpieza de datos
    antiguos (si aplica) e inicia la transacción de inserción.
    """
    global config
    global baseDatosGlobal
    global fechaActual
    
    connection = None
    cursor = None
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        printInfo(" === Comenzando la importación de datos JSON a la base de datos === \n", color="info")
        
        if not baseDatosGlobal:
            printInfo("La base de datos global está vacía. No hay nada que importar.", color="error")
            return False

        # Obtener campus y semestre actual de los datos extraídos
        campus_name = next(iter(baseDatosGlobal.keys()))
        semestre_key = next(iter(baseDatosGlobal[campus_name].keys()))
        codigo_semestre = f"{semestre_key[:4]}-{semestre_key[4]}"
        
        # Gestión del Campus
        cursor.execute("SELECT id FROM campus WHERE nombre = %s", (campus_name,))
        campus_result = cursor.fetchone()
        
        if not campus_result:
            printInfo(f"Creando campus {campus_name}...", color="info")
            cursor.execute("INSERT INTO campus (nombre) VALUES (%s)", (campus_name,))
            campus_id = cursor.lastrowid
        else:
            campus_id = campus_result[0]
        
        # Gestión de limpieza de semestre previo
        # Se elimina el semestre completo para re-importar datos limpios y evitar duplicados o datos sucios
        cursor.execute("SELECT id FROM semestre WHERE campus_id = %s AND codigo = %s", 
                       (campus_id, codigo_semestre))
        semestre_existente = cursor.fetchone()
        
        if semestre_existente:
            semestre_id = semestre_existente[0]
            printInfo(f"Eliminando semestre existente {codigo_semestre} para reescritura limpia...", color="advertencia")
            cursor.execute("DELETE FROM semestre WHERE id = %s", (semestre_id,))
            printInfo(f"Datos anteriores eliminados.", color="advertencia")
        
        # Insertar datos nuevos
        insertarJsonHaciaBDD(cursor, baseDatosGlobal)
        
        connection.commit()
        printInfo("Datos importados y commit realizado exitosamente!", color="exito")
        
        # Registrar timestamp de actualización
        try:
            with open("ultima_act_bdd.txt", "w", encoding="utf-8") as archivo:
                archivo.write(fechaActual.replace("_", " "))
        except IOError:
            printInfo("No se pudo escribir el archivo de última actualización.", "advertencia")
        
        return True

    except Error as e:
        printInfo(f"Error CRÍTICO de Base de Datos: {e}", color="error")
        if connection and connection.is_connected():
            connection.rollback()
            printInfo("Se realizó ROLLBACK de la transacción.", color="error")
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            printInfo("Conexión BDD cerrada.", color="normal")


############################################################################
#                       MANEJO DE CREDENCIALES                             #

def cargarCredenciales():
    """Carga usuario y contraseña desde archivo externo."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.normpath(os.path.join(script_dir, '..', 'sedona_config', 'piedmont_cred.txt'))
        
        printInfo(f"Cargando credenciales desde: {cred_path}", "info")

        with open(cred_path, 'r', encoding='utf-8') as f:
            lineas = [line.strip() for line in f.readlines() if line.strip()]

        if len(lineas) < 2:
            printInfo("Archivo de credenciales incompleto.", "error")
            return None, None

        return lineas[0], lineas[1]

    except Exception as e:
        printInfo(f"Error al leer credenciales: {e}", "error")
        return None, None
        
def cargarConfigBDD():
    """Carga configuración de conexión MySQL desde archivo externo."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.normpath(os.path.join(script_dir, '..', 'sedona_config', 'db_config.txt'))
        
        printInfo(f"Cargando config BDD desde: {config_path}", "info")

        config_dict = {}
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config_dict[key.strip()] = value.strip()
        
        required = ['host', 'user', 'password', 'database']
        if not all(k in config_dict for k in required):
            printInfo("Configuración BDD incompleta.", "error")
            return None

        return config_dict

    except Exception as e:
        printInfo(f"Error al leer config BDD: {e}", "error")
        return None


############################################################################
#                       SCRAPING/EXTRACCIÓN                                #

def procesarSala(texto):
    """Limpia el string de la sala eliminando prefijos y manejando casos borde."""
    partes = texto.split("\n")
    
    # Caso borde: El nombre del profesor aparece antes que la sala
    if partes[0].strip().startswith("Prof."):
        return partes[1].strip() if len(partes) > 1 else ""
    
    return partes[0].replace("Sala ", "").strip()

def extraerHorario(driver):
    """
    Extrae la matriz de horario y la lista de profesores desde el popup o frame.
    Utiliza esperas explícitas para mayor estabilidad.
    """
    global timeoutWeb
    wait = WebDriverWait(driver, 10) # Espera máxima de 10 segundos para elementos críticos
    
    try:
        # Asegurar que estamos en el frame "cuerpo"
        wait.until(EC.frame_to_be_available_and_switch_to_it("cuerpo"))
        
        # Lógica para extraer profesores (buscando variaciones en el header)
        try:
            profesoresHeader = driver.find_element(By.XPATH, "//tr[td[1][contains(text(), 'Profesor') or contains(text(), 'Profesores')]]/td[1]")
            header_text = profesoresHeader.text.strip()
            
            xpath_prof = "//tr[td[1][contains(text(), 'Profesores')]]/td[3]" if "Profesores" in header_text else "//tr[td[1][contains(text(), 'Profesor')]]/td[3]"
            profesoresFind = driver.find_element(By.XPATH, xpath_prof)
            profesores = profesoresFind.text
            listaProfesores = [nombre.strip() for nombre in profesores.split("\n") if nombre.strip()]
        except Exception:
            # Si falla la extracción de profes, asumimos lista vacía para no romper el flujo
            listaProfesores = []

        # Encontrar tabla de horario
        tablaHorario = wait.until(EC.presence_of_element_located((By.XPATH, '//table[@class="letra8" and @bgcolor="#959595"]')))
        filas = tablaHorario.find_elements(By.TAG_NAME, "tr")
        filas = filas[1:] # Omitir encabezado

        # Matriz 10 bloques x 7 días
        matriz = [["" for _ in range(7)] for _ in range(10)]
        
        # Mapeo de filas HTML a filas lógicas de la matriz (índices 0-9)
        mapaFilas = {
            1: 0, 20: 1, 39: 2, 58: 3, 77: 4, 96: 5,
            115: 6, 134: 7, 153: 8, 172: 9
        }

        filaActual = 1
        for fila in filas:
            bloque = fila.find_elements(By.XPATH, './/table[@class="letra7"]')
            
            # Si la fila tiene suficientes celdas (bloques de días)
            if len(bloque) >= 9:
                # Indices 2 al 8 corresponden a Lunes-Domingo en la estructura visual del SIGA
                datos_bloques = [procesarSala(bloque[i].text.strip()) for i in range(2, 9)]

                if filaActual in mapaFilas:
                    idx_matriz = mapaFilas[filaActual]
                    for i in range(7):
                        if datos_bloques[i]:
                            matriz[idx_matriz][i] = datos_bloques[i]

            filaActual += 1

        driver.switch_to.default_content()
        return matriz, listaProfesores
    
    except Exception as e:
        printInfo(f"Error extrayendo horario: {e}", "error")
        driver.switch_to.default_content()
        return None, []

def agregarHorario(contador, fila, driver):
    """
    Gestiona la apertura de la ventana secundaria (popup) para ver el detalle del horario.
    """
    try:
        # Click en el enlace JS
        enlaceHorario = fila.find_element(By.XPATH, f".//a[contains(@href, 'javascript:Envia(document.form{contador});')]")
        enlaceHorario.click()
        
        # Esperar a que se abra la nueva ventana
        WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)

        ventanas = driver.window_handles
        ventanaSiga = ventanas[0]
        ventanaHorario = ventanas[1]
        
        driver.switch_to.window(ventanaHorario)
        
        horario, profesores = extraerHorario(driver)
        
        # Cerrar ventana auxiliar si sigue abierta (buena práctica para no saturar memoria)
        try:
            driver.close()
        except:
            pass # Ya estaba cerrada o hubo error

        driver.switch_to.window(ventanaSiga)
        driver.switch_to.default_content()
        
        # Volver al frame correcto
        WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it("frame3"))

        return horario, profesores

    except Exception as e:
        printInfo(f"Error al navegar ventanas de horario: {e}", "error")
        # Intentar recuperación básica de estado
        try:
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except:
            pass
        return None, []

def scrapingSIGA(estadoPrevio=None):
    """
    Función principal que orquesta la navegación y extracción de datos del SIGA.
    """
    global chromeDriverService, opcionesChromeDriver, baseDatosGlobal
    global usuarioSIGA, passwordSIGA, campus, jornada, timeoutWeb, archivoJSONActual
    
    printInfo(" === Comenzando la preparación de scraping === \n", color="info")
    
    try:
       printInfo("Iniciando ChromeDriver ...")
       driver = webdriver.Chrome(service=chromeDriverService, options=opcionesChromeDriver)
       driver.maximize_window()
       wait = WebDriverWait(driver, 10)
    except Exception as e:
        printInfo(f"Error crítico iniciando ChromeDriver: {e}", "error")
        return False
    
    inicioTiempo = time.time()
    
    try:
        printInfo("Navegando al portal SIGA...")
        
        # Configuración de reanudación
        contadorInicio = 0
        if estadoPrevio:
            contadorInicio = estadoPrevio.get('ultimo_contador', -1) + 1
            archivoJSONActual = estadoPrevio.get('archivo_json')
        
        periodo = determinarSemestreActual()
        driver.get("https://siga.usm.cl/pag/home.jsp")
        
        # Bypass manual para el CAPTCHA en caso de estar rate-limited (toma de ramos, etc)
        # printInfo("Por favor, resuelva el CAPTCHA de forma manual en la ventana del navegador.")
        # printInfo("Una vez resuelto, presione enter para comenzar la actualización para la base de datos.")
        # input("")

        # Login
        wait.until(EC.presence_of_element_located((By.NAME, "login"))).send_keys(usuarioSIGA)
        driver.find_element(By.NAME, "passwd").send_keys(passwordSIGA)
        driver.find_element(By.XPATH, "//a[contains(@href, 'ValidaLogin')]").click()

        # Navegación hacia menús
        driver.get("https://siga.usm.cl/pag/menu.jsp")
        
        # Click en "Horario Asignaturas"
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'insc_procesos.jsp')]"))).click()

        # --- Frame 1: Configuración de búsqueda ---
        wait.until(EC.frame_to_be_available_and_switch_to_it("frame1"))
        
        Select(driver.find_element(By.NAME, "periodo")).select_by_value(periodo)
        
        valJornada = "1" if jornada == "1" else "2" # Simplificación
        Select(driver.find_element(By.NAME, "jornada")).select_by_value(jornada)
        
        # Mapeo de campus para logs
        mapaCampus = {"1": "Casa Central", "4": "Concepción", "7": "Santiago San Joaquín", "2": "Vitacura", "3": "Viña del Mar"}
        nombreCampus = mapaCampus.get(campus, "Desconocido")
        
        Select(driver.find_element(By.NAME, "sede")).select_by_value(campus)
        printInfo(f"Configurando búsqueda: {periodo} | {nombreCampus}")

        # --- Frame 5: Opciones de listado ---
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it("frame5"))
        
        Select(driver.find_element(By.NAME, "op")).select_by_value("1")      # Todas las asignaturas
        Select(driver.find_element(By.NAME, "op_asig")).select_by_value("1") # Ordenar por nombre
        
        driver.find_element(By.NAME, "form_f1").submit()

        # --- Frame 3: Tabla de resultados ---
        driver.switch_to.default_content()
        # Espera extendida aquí porque la carga de la tabla puede ser lenta
        WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it("frame3"))
        
        filas = driver.find_elements(By.XPATH, "//table[@class='Celda01']/tbody/tr")
        printInfo(f"Se encontraron {len(filas)} filas potenciales para procesar.")

        # Inicialización de estructuras de datos
        if not baseDatosGlobal:
            baseDatosGlobal = {}
        
        if nombreCampus not in baseDatosGlobal:
            baseDatosGlobal[nombreCampus] = {}
        
        if periodo not in baseDatosGlobal[nombreCampus]:
            baseDatosGlobal[nombreCampus][periodo] = {}

        baseDatosNueva = baseDatosGlobal[nombreCampus][periodo]
        
        ultimaSigla = None
        ultimoNombre = None
        ultimoDepto = None
        
        # Loop principal de extracción
        contadorGlobal = 0
        
        for fila in filas:
            # Control de reanudación
            if contadorGlobal < contadorInicio:
                contadorGlobal += 1
                continue

            # Saltar separadores
            if fila.find_elements(By.TAG_NAME, "td") and fila.find_element(By.TAG_NAME, "td").get_attribute("colspan") == "7":
                continue

            try:
                cells = fila.find_elements(By.TAG_NAME, "td")
                if len(cells) > 0:
                    sigla = cells[0].text.strip()
                    nombre = cells[1].text.strip()
                    depto = cells[2].text.strip()
                    paralelo = cells[3].text.strip()
                    profesStr = cells[4].text.strip() # Solo referencial, se extrae real del popup
                    cupos = cells[5].text.strip()
                    
                    if sigla:
                        print(f"")
                        printInfo(f"ID {contadorGlobal}")
                        printInfo(f"Nombre: {nombre}")
                        printInfo(f"Sigla: {sigla}, Paralelo: {paralelo}")
                        printInfo(f"Departamento: {depto}")
                        printInfo(f"Profesor: {profesStr}")
                    else:
                        printInfo(f"Asignatura: {ultimaSigla}, Paralelo: {paralelo}")
                    
                    objAsignatura = {
                        "Nombre": nombre if sigla else ultimoNombre,
                        "Departamento": depto if sigla else ultimoDepto,
                        "Paralelo": paralelo,
                        "Profesores": [],
                        "Cupos": cupos,
                        "Horario": []
                    }

                    # Extracción profunda (Popup de horario)
                    horario, profesores = agregarHorario(contadorGlobal, fila, driver)
                    
                    if horario is None:
                        printInfo(f"Fallo crítico obteniendo horario para fila {contadorGlobal}", "error")
                        return False # Fail-fast strategy
                    
                    objAsignatura["Horario"] = horario
                    objAsignatura["Profesores"] = profesores

                    # Almacenamiento en estructura
                    keySigla = sigla if sigla else ultimaSigla
                    
                    if keySigla not in baseDatosNueva:
                        baseDatosNueva[keySigla] = []
                    
                    baseDatosNueva[keySigla].append(objAsignatura)

                    # Actualizar punteros de "último visto" para paralelos sin sigla explícita
                    if sigla:
                        ultimaSigla = sigla
                        ultimoNombre = nombre
                        ultimoDepto = depto
                        printInfo(f"Horario extraído (P{paralelo})")
                    else:
                        printInfo(f"Horario extraído (P{paralelo})")

                    # Persistencia incremental
                    if guardarJSON():
                        guardarEstado(contadorGlobal, archivoJSONActual)
                    
                contadorGlobal += 1
                
                # Debugging limit
                if limite != 0 and contadorGlobal >= limite:
                    break

            except Exception as e:
                printInfo(f"Error procesando fila {contadorGlobal}: {e}", "error")
                return False

    except Exception as e:
        printInfo(f"Error general en ciclo de scraping: {e}", "error")
        return False
        
    finally:
        driver.quit()
        printInfo("Navegador cerrado.")

    # Resumen final
    duracion = time.time() - inicioTiempo
    minutos, segundos = segundosAMinutos(duracion)
    
    printInfo(f"Scraping finalizado en {minutos}m {math.floor(segundos)}s. Total procesado: {contadorGlobal} ítems.", "exito")
    return True


############################################################################
#                        MANEJO DE ARCHIVOS                                #

def guardarEstado(contador, archivo_json_actual):
    """Guarda un checkpoint para poder reanudar si el script falla."""
    estado = {
        'campus': campus,
        'periodo': determinarSemestreActual(),
        'ultimo_contador': contador,
        'archivo_json': archivo_json_actual
    }
    try:
        with open('scraping_state.json', 'w', encoding='utf-8') as f:
            json.dump(estado, f)
    except IOError:
        pass # No es crítico si falla esto

def cargarEstado():
    """Carga el checkpoint anterior si coincide con la configuración actual."""
    try:
        if not os.path.exists('scraping_state.json'):
            return None

        with open('scraping_state.json', 'r', encoding='utf-8') as f:
            estado = json.load(f)

        if estado.get('campus') == campus and estado.get('periodo') == determinarSemestreActual():
            printInfo(f"Reanudando sesión previa desde ítem {estado['ultimo_contador'] + 1}.", "advertencia")
            if os.path.exists(estado['archivo_json']):
                with open(estado['archivo_json'], 'r', encoding='utf-8') as db_file:
                    global baseDatosGlobal
                    baseDatosGlobal = json.load(db_file)
            return estado
        else:
            printInfo("Estado previo no coincide con configuración actual. Iniciando de cero.", "info")
            limpiarEstado()
            return None
            
    except Exception:
        return None

def limpiarEstado():
    if os.path.exists('scraping_state.json'):
        try:
            os.remove('scraping_state.json')
        except:
            pass

def guardarJSON():
    global baseDatosGlobal, archivoJSONActual, fechaActual
    
    directorioJson = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json')
    os.makedirs(directorioJson, exist_ok=True)
        
    if archivoJSONActual is None:
        archivoJSONActual = os.path.join(directorioJson, f"bdd_general-{fechaActual}.json")
    
    try:
        with open(archivoJSONActual, "w", encoding="utf-8") as archivo:
            json.dump(baseDatosGlobal, archivo, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        printInfo(f"Error guardando JSON: {e}", "error")
        return False


############################################################################
#                             UTILIDADES                                   #

def segundosAMinutos(segundos):
    return segundos // 60, segundos % 60

def determinarSemestreActual():
    now = datetime.now()
    semestre = "1" if 1 <= now.month <= 7 else "2"
    return f"{now.year}{semestre}"
    
def cambiarFechaActual():
    global fechaActual
    fechaActual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def printInfo(mensaje, color="info", caja=True):
    """Sistema de logging unificado a consola y archivo."""
    global fechaActual
    
    # Escribir a Log
    logDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(logDir, exist_ok=True)
    log_file = os.path.join(logDir, f"{fechaActual}.txt")
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            clean_msg = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', mensaje)
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {clean_msg}\n")
    except:
        pass # Logging silencioso si falla escritura

    # Colores Consola
    colores = {
        "normal": Fore.WHITE,
        "info": Fore.LIGHTWHITE_EX,
        "error": Fore.RED,
        "advertencia": Fore.YELLOW,
        "exito": Fore.GREEN,
    }
    
    c = colores.get(color.lower(), Fore.WHITE)
    prefix = f"{Fore.GREEN}[+]{c}" if caja else f"{c}"
    print(f"{prefix} {mensaje}{Style.RESET_ALL}")

def mostrarLogo():
    printInfo(r"       _          _                       _   ", "advertencia", False)
    printInfo(r" _ __ (_) ___  __| |_ __ ___   ___  _ __ | |_ ", "advertencia", False)
    printInfo(r"| '_ \| |/ _ \/ _` | '_ ` _ \ / _ \| '_ \| __|", "advertencia", False)
    printInfo(r"| |_) | |  __/ (_| | | | | | | (_) | | | | |_ ", "advertencia", False)
    printInfo(r"| .__/|_|\___|\__,_|_| |_| |_|\___/|_| |_|\__|", "advertencia", False)
    printInfo(r"|_|                                           ", "advertencia", False)
    printInfo(f"Web Scraper/Motor de extracción de Asignaturas para el SIGA de la UTFSM", "info", False)
    printInfo(f"Versión {piedmontVersion} | Revisión {piedmontRevision}\n")
    
def prepararTodo():
    global intentosMax, baseDatosGlobal
    
    estadoPrevio = cargarEstado()
    
    for i in range(1, intentosMax + 1):
        printInfo(f"Intento de ciclo completo {i}/{intentosMax} ...", "advertencia")
        
        # Scraping
        exitoScraping = scrapingSIGA(estadoPrevio)
        
        if exitoScraping:
            estadoPrevio = None # Ya no necesitamos reanudar si completamos
            
            # Base de Datos
            if prepararConexionBDD():
                printInfo("Ciclo completado con éxito. Limpiando estado y saliendo.", "info")
                limpiarEstado()
                return
            else:
                printInfo("Fallo en BDD. Reintentando...", "error")
        else:
            printInfo("Fallo en Scraping. Reiniciando variables...", "error")
            baseDatosGlobal = None
        
        time.sleep(5) # Cooldown entre intentos

    printInfo(f"Se superó el número máximo de intentos ({intentosMax}).", "error")

def inicializar():
    global opcionesChromeDriver, chromeDriverService
    global usuarioSIGA, passwordSIGA, config

    init(autoreset=True)
    cambiarFechaActual()
    mostrarLogo()
    
    config = cargarConfigBDD()
    if not config: sys.exit(1)

    usuarioSIGA, passwordSIGA = cargarCredenciales()
    if not usuarioSIGA: sys.exit(1)
    
    # Configuración del Driver
    opcionesChromeDriver = Options()
    opcionesChromeDriver.add_argument("--headless")
    opcionesChromeDriver.add_argument("--no-sandbox")
    opcionesChromeDriver.add_argument("--disable-dev-shm-usage")
    opcionesChromeDriver.add_argument("--window-size=1920,1080") # Importante para headless
    
    # Solución alternativa para Raspberry Pi 4 (problemas de compatibilidad con Selenium/Chromedriver)
    try:
        chromeDriverPath = shutil.which("chromedriver")
        if chromeDriverPath:
            chromeDriverService = webdriver.ChromeService(executable_path=chromeDriverPath)
        else:
            chromeDriverService = Service() # Default
    except Exception:
        chromeDriverService = Service()

    prepararTodo()

#####################################################################################

# Configuración Global
config = None
usuarioSIGA = None
passwordSIGA = None

# Parámetros Operativos
campus = "7" # (1: CC, 4: Conce, 7: CSSJ, 2: Vitacura, 3: Viña)
jornada = "1" # (1: diurno, 2: vespertino)
baseDatosGlobal = None
archivoJSONActual = None
chromeDriverService = None
opcionesChromeDriver = None
fechaActual = None

# Configuración de Tiempos
timeoutWeb = 2
limite = 0
intentosMax = 5

# Metadatos
piedmontVersion = "v1.5-optimized"
piedmontRevision = "20251211"

if __name__ == "__main__":
    inicializar()