#   Web-Scraper para el SIGA (codename "Sedona")
#       Sergio Cárcamo Naranjo (Alumno)
#         Departamento de Informática
#   Universidad Técnica Federico Santa María

#    Creado con el <3 por y para estudiantes

'''
DISCLAIMER:
    El uso de este software cae puramente bajo la responsabilidad del usuario.
    Este software no pretende dañar o robar información, su propósito está destinado a fines educativos y de apoyo para los estudiantes.
    El software, por defecto, sólamente obtiene información de los horarios de la UTFSM, y no modifica ni obtiene otro tipo de información.
    Se debe proporcionar un usuario y contraseña de una cuenta @usm.cl de un alumno regular para que este software funcione.
    Ninguno de los datos obtenidos mediante el software, o ingresados por el usuario, son utilizados con fines maliciosos ni subidos a internet.
    Ante cualquier duda, este software es open source, y su código es libremente accesible y modificable.
    
    Este software es beta, y puede fallar en cualquier momento. 
'''

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from colorama import Fore, Style, init
from tabulate import tabulate
from unidecode import unidecode
from datetime import datetime

import os
import sys
import math
import json
import time
import getpass
import platform
import requests
import subprocess


############################################################################
#                           ACTUALIZADOR                                   #

# Función que detecta la última versión del script
def obtenerUltimaVersionGithub(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("tag_name", False)
        
    except requests.ConnectionError as e:
        printInfo(f"No se puede conectar al servidor: {e}", "error")
        return False
        
    except requests.HTTPError as e:
        printInfo(f"Error HTTP al obtener la última versión: {e}", "error")
        return False
        
    except requests.RequestException as e:
        printInfo(f"Error al obtener la última versión: {e}", "error")
        return False
        
    except ValueError as e:
        printInfo(f"Error al procesar la respuesta JSON: {e}", "error")
        return False

# Función que descarga la ultima versión del script
def descargarUltimaVersionGithub(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open("sedona.py", "wb") as file:
            file.write(response.content)
        return True
        
    except requests.ConnectionError as e:
        printInfo(f"No se puede conectar al servidor: {e}", "error")
        return False
        
    except requests.HTTPError as e:
        printInfo(f"Error HTTP al descargar la nueva versión: {e}", "error")
        return False
        
    except requests.RequestException as e:
        printInfo(f"Error al descargar la nueva versión: {e}", "error")
        return False
        
    except IOError as e:
        printInfo(f"Error al escribir el archivo: {e}", "error")
        return False

# Función que maneja la búsqueda de actualizaciones
def buscarActualizaciones():
    global sedonaVersion
    
    urlApi = f"https://api.github.com/repos/frostodev/sedona/releases/latest"
    ultimaVersion = obtenerUltimaVersionGithub(urlApi)

    # Si falla obteniendo la última versión...
    if not ultimaVersion:
        return False

    # Si existe alguna actualización
    if sedonaVersion != ultimaVersion:
        
        urlRelease = f"https://github.com/frostodev/sedona/releases/download/{ultimaVersion}/sedona.py"
        
        printInfo(f"Actualización disponible: {ultimaVersion}.")
        time.sleep(2)
        
        print(f"")
        printInfo(f"Deseas actualizar? (si/no)")
        decisionActualizar = unidecode(input("> ")).lower()
        
        if decisionActualizar == "si":

            print(f"")
            printInfo("Descargando la nueva versión...")
            
            # Intentar descargar la última versión
            descargarFlag = descargarUltimaVersionGithub(urlRelease)
            
            # Si falla descargando...
            if not descargarFlag:
                return False
            
            else:
                print(f"")
                printInfo("Actualización completada. Sedona debe reiniciarse.")
                printInfo("Presiona enter para salir...")
                input("")
                printInfo("Saliendo...")
                sys.exit(0)
        
        else:
            return True
    
    # Si no hay actualizaciones disponibles
    else:
        return True

############################################################################
#                       SCRAPING/EXTRACCIÓN                                #

# Función que devuelve la sala de un string extraído de del horario
def procesarSala(texto):
    # Primero, separamos el texto en partes usando el carácter \n
    partes = texto.split('\n')
    
    # Por alguna razón, a veces la tabla del horario tiene el nombre del profesor primero...
    if partes[0].strip().startswith("Prof."):
        return partes[1].strip()
    
    # Si la primera línea no comienza con "Prof.", procesamos la primera línea
    # Para eliminar la palabra "Sala" (si existe) y devolver el texto limpio
    parteProcesada = partes[0].replace('Sala ', '').strip()
    
    return parteProcesada

# Función que extrae el horario desde la ventana de este
def extraerHorario(driver):
    
    global configuracionGlobal
    timeoutWeb = configuracionGlobal["timeoutWeb"]
    
    try:
        # Esperar a que la página y los frames estén completamente cargados
        time.sleep(timeoutWeb)

        # Cambiar al frame "cuerpo"
        driver.switch_to.frame("cuerpo")
        
        # Extraer la lista de profesores
        profesoresHeader = driver.find_element(By.XPATH, "//tr[td[1][contains(text(), 'Profesor') or contains(text(), 'Profesores')]]/td[1]")
        profesoresHeaderText = profesoresHeader.text.strip()
        
        # Encontrar la lista de profesores dependiendo del encabezado encontrado
        if "Profesores" in profesoresHeaderText:
            profesoresFind = driver.find_element(By.XPATH, "//tr[td[1][contains(text(), 'Profesores')]]/td[3]")
        elif "Profesor" in profesoresHeaderText:
            profesoresFind = driver.find_element(By.XPATH, "//tr[td[1][contains(text(), 'Profesor')]]/td[3]")

        profesores = profesoresFind.text
        listaProfesores = [nombre.strip() for nombre in profesores.split('\n') if nombre.strip()]

        # Encuentra la tabla del horario basada en su clase y atributo bgcolor
        tablaHorario = driver.find_element(By.XPATH, '//table[@class="letra8" and @bgcolor="#959595"]')

        # Encuentra todas las filas dentro de la tabla
        filas = tablaHorario.find_elements(By.TAG_NAME, 'tr')

        # Saltar la primera fila (Encabezado03) hasta el ultimo letra7
        filas = filas[1:]

        # Crear la matriz del horario de 10 filas y 7 columnas inicializada con strings vacíos
        matriz = [["" for _ in range(7)] for _ in range(10)]

        # Por alguna razón que desconozco, la cantidad de filas está separada por una candidad arbitraria de filas vacías...
        filaActual = 1

        # Iterar en cada fila
        for fila in filas:
            # Cada bloque está contenido en una tabla con nombre "letra7"
            bloque = fila.find_elements(By.XPATH, './/table[@class="letra7"]')
            if len(bloque) >= 9:
                # Obtener el texto de cada bloque y procesar el nombre de la sala
                bloque1 = procesarSala(bloque[2].text.strip())
                bloque2 = procesarSala(bloque[3].text.strip())
                bloque3 = procesarSala(bloque[4].text.strip())
                bloque4 = procesarSala(bloque[5].text.strip())
                bloque5 = procesarSala(bloque[6].text.strip())
                bloque6 = procesarSala(bloque[7].text.strip())
                bloque7 = procesarSala(bloque[8].text.strip())

                # Crear un diccionario que mapea filaActual a las filas de la matriz
                mapaFilas = {
                    1: 0, 20: 1, 39: 2, 58: 3, 77: 4, 96: 5,
                    115: 6, 134: 7, 153: 8, 172: 9
                }

                # Definir los bloques
                bloques = [bloque1, bloque2, bloque3, bloque4, bloque5, bloque6, bloque7]

                # Actualizar la matriz según el valor de filaActual
                if filaActual in mapaFilas:
                    filaMatriz = mapaFilas[filaActual]
                    for i in range(7):
                        if bloques[i] != "":
                            matriz[filaMatriz][i] = bloques[i]

            # Aumentar el contador de filas
            filaActual += 1

        # Volver al contexto principal
        driver.switch_to.default_content()

        # Devolver el horario y la lista de profesores
        return matriz, listaProfesores
    
    except Exception as e:
        printInfo(f"Error al extraer el horario: {e}")
        time.sleep(2)
        return None
        
    return None

# Función que maneja el cambio de ventanas para extraer el horario
def agregarHorario(contador, fila, driver):
    
    global configuracionGlobal
    timeoutWeb = configuracionGlobal["timeoutWeb"]    
    
    # Hacer clic en el enlace para obtener el horario
    enlaceHorario = fila.find_element(By.XPATH, ".//a[contains(@href, 'javascript:Envia(document.form" + str(contador) + ");')]")
    #time.sleep(5)
    enlaceHorario.click()
    time.sleep(timeoutWeb)

    ventanas = driver.window_handles
    ventanaSiga = driver.window_handles[0]
    ventanaHorario = driver.window_handles[1]
    #printInfo(f"Ventanas abiertas: {ventanas}")
      
    # Cambiar a la ventana del horario
    printInfo(f"Cambiando a la ventana del horario...")
    driver.switch_to.window(ventanaHorario)
        
    # Extraer el horario
    horario, profesores = extraerHorario(driver)
        
    # Si hubo un error al extraer el horario...
    if not horario:
        return None
        
    printInfo(f"Horario extraído.")

    # Cambiar de vuelta a la ventana del SIGA, y asegurarse de estar en el frame3
    printInfo(f"Cambiando a la ventana del SIGA...")
    driver.switch_to.window(ventanaSiga)
    driver.switch_to.default_content()
    driver.switch_to.frame("frame3")

    return horario, profesores

# Función que maneja la actualización de la base de datos
def actualizarBaseDatos(periodo, campus, jornada):
    
    global chromeDriverService
    global opcionesChromeDriver
    global configuracionGlobal
    global baseDatosGlobal
    global urlSiga
    
    global ultimoCampus
    global ultimoSemestre
    
    usuarioSiga = configuracionGlobal["usuarioSiga"]
    passwordSiga = configuracionGlobal["passwordSiga"]
    timeoutWeb = configuracionGlobal["timeoutWeb"]
    
    # Iniciar ChromeDriver
    try:
       print(f"")
       printInfo("Iniciando ChromeDriver ...")
       driver = webdriver.Chrome(service = chromeDriverService, options = opcionesChromeDriver)
       driver.maximize_window()
        
    except Exception as e:
        printInfo(f"Error al iniciar ChromeDriver: {e}", "error")
        driver.quit()
        return False
    
    # Comenzar a medir el tiempo
    inicioTiempo = time.time()
    
    # Crear una copia de seguridad de la base actual
    guardarBaseDatosBackup()
    
    try:
        printInfo("Comenzando scraping (tiempo estimado ~2h 20m)...")
        print(f"")
        
        # Navegar hacia la dirección web del SIGA
        driver.get(urlSiga)

        # Esperar un momento para que la página cargue completamente
        time.sleep(timeoutWeb)
        
        # Bypass manual para el CAPTCHA en caso de estar rate-limited (toma de ramos, etc)
        # printInfo("Por favor, resuelva el CAPTCHA de forma manual en la ventana del navegador.")
        # printInfo("Una vez resuelto, presione enter para comenzar la actualización para la base de datos.")
        # input("")

        # Encontrar los campos de usuario y contraseña y el botón de inicio de sesión
        printInfo(f"Buscando elementos de inicio de sesión ...")
        botonUsername = driver.find_element(By.NAME, 'login')
        botonPassword = driver.find_element(By.NAME, 'passwd')
        botonLogin = driver.find_element(By.XPATH, "//a[@href='javascript:ValidaLogin(document.Formulario)']")
        
        # Introducir las credenciales y hacer clic en el botón de inicio de sesión
        printInfo(f"Iniciando Sesión {usuarioSiga} ...")
        botonUsername.send_keys(usuarioSiga)
        botonPassword.send_keys(passwordSiga)
        botonLogin.click()

        # Cambiar a menu.jsp
        printInfo(f"Cambiando a menu.jsp ...")
        urlMenu = "https://siga.usm.cl/pag/menu.jsp"
        driver.get(urlMenu)
        time.sleep(timeoutWeb)

        # Hacer clic en el enlace para ejecutar la función JavaScript
        printInfo(f"Ingresando a Horario Asignaturas ...")
        botonHorarioAsignatura = driver.find_element(By.XPATH, "//a[@href=\"javascript:Enviar('sistinsc/insc_procesos.jsp',0,0,0,2,'_parent')\"]")
        botonHorarioAsignatura.click()

        # Esperar un momento para asegurar que la página se cargue
        time.sleep(timeoutWeb)

        # Cambiar al frame del periodo, jornada y campus
        printInfo(f"Cambiando a frame1 ...")
        driver.switch_to.frame("frame1")
        time.sleep(timeoutWeb)

        # Periodo
        nombrePeriodo = f"{periodo[:4]}-{periodo[4:]}"
        printInfo(f"Seleccionando {nombrePeriodo} ...")
        periodoSelect = Select(driver.find_element(By.NAME, "periodo"))
        periodoSelect.select_by_value(periodo)
        time.sleep(timeoutWeb)

        # Jornada
        if jornada == "1":
            nombreJornada = "Diurno"
        else:
            nombreJornada = "Vespertino"
        
        printInfo(f"Seleccionando {nombreJornada} ...")
        jornadaSelect = Select(driver.find_element(By.NAME, "jornada"))
        jornadaSelect.select_by_value(jornada)
        time.sleep(timeoutWeb)

        # Campus
        if campus == "1":
            nombreCampus = "Casa Central"
        
        elif campus == "4":
            nombreCampus = "Concepción"

        elif campus == "7":
            nombreCampus = "Santiago San Joaquín"

        elif campus == "2":
            nombreCampus = "Santiago Vitacura"

        elif campus == "3":
            nombreCampus = "Viña del Mar"        
        
        printInfo(f"Seleccionando Campus/Sede {nombreCampus} ...")
        campusSelect = Select(driver.find_element(By.NAME, "sede"))
        campusSelect.select_by_value(campus)

        # Esperar un momento para asegurar que la página se cargue
        time.sleep(timeoutWeb)

        # Cambiar al frame de selección de asignaturas
        printInfo(f"Cambiando a frame5 ...")
        driver.switch_to.default_content()
        driver.switch_to.frame("frame5")
        time.sleep(timeoutWeb)

        # Interactuar con el dropdown "Buscar por"
        printInfo(f"Seleccionando Todas las asignaturas ...")
        buscarPorDropdown = Select(driver.find_element(By.NAME, "op"))
        buscarPorDropdown.select_by_value("1")  # Seleccionar "Todas las asignaturas"
        time.sleep(timeoutWeb)

        # Interactuar con el dropdown "Orden"
        printInfo(f"Seleccionando Orden por Nombre ...")
        orden_dropdown = Select(driver.find_element(By.NAME, "op_asig"))
        orden_dropdown.select_by_value("1")  # Seleccionar "Nombre"
        time.sleep(timeoutWeb)

        # Enviar el formulario
        printInfo(f"Enviando el formulario form_f1 ...")
        form_f1 = driver.find_element(By.NAME, "form_f1")
        form_f1.submit()

        # Esperar a que se procese el formulario y se genere la tabla de asignaturas
        time.sleep(timeoutWeb)

        # Cambiar al frame que contiene la tabla de asignaturas
        printInfo(f"Cambiando a frame3 ...")
        driver.switch_to.default_content()
        driver.switch_to.frame("frame3")
        time.sleep(5)

        # Encontrar la tabla y extraer datos
        filas = driver.find_elements(By.XPATH, "//table[@class='Celda01']/tbody/tr")

        # Inicializar el diccionario para almacenar las asignaturas
        baseDatosTemp = {}
        baseDatosTemp[nombreCampus] = {}
        baseDatosTemp[nombreCampus][periodo] = {}
        
        ultimaSigla = None
        ultimoNombre = None
        ultimoDepto = None

        baseDatosNueva = baseDatosTemp[nombreCampus][periodo]
        
        # Si la base de datos general está vacía, crearla
        if not baseDatosGlobal:
            baseDatosGlobal = {}
        
        # Iterar sobre las filas y extraer datos
        contador = 0
        for fila in filas:
            # Cuando se cambia de asignatura, hay un divisor en la tabla que se ve así en HTML:
            #
            # <tr>
            #   <td colspan="7" >
            #       <hr size = "1" align="center" width="100%">
            #   </td>
            # </tr>
            #
            # En caso de que haya un divisor en la tabla, saltárselo, y continuar leyendo la asignatura siguiente.
            if fila.find_elements(By.TAG_NAME, 'td') and fila.find_element(By.TAG_NAME, 'td').get_attribute('colspan') == '7':
                continue

            try:
                cells = fila.find_elements(By.TAG_NAME, "td")
                if len(cells) > 0:
                    # Extraer la información de la asignatura
                    sigla = cells[0].text.strip()
                    nombre = cells[1].text.strip()
                    departamento = cells[2].text.strip()
                    paralelo = cells[3].text.strip()
                    profesor = cells[4].text.strip()
                    cupos = cells[5].text.strip()
                    
                    # Si la sigla no es vacía, entonces declararlo como un nuevo ramo
                    if sigla:
                        if sigla not in baseDatosNueva:
                            baseDatosNueva[sigla] = []
                        
                        baseDatosNueva[sigla].append({
                            'Nombre': nombre,
                            'Departamento': departamento,
                            'Paralelo': paralelo,
                            'Profesores': [],
                            'Cupos': cupos,
                            'Horario': []
                        })
                        
                        # Añadir el horario y la lista de profesores
                        print(f"")
                        printInfo(f"ID {contador}")
                        printInfo(f"Nombre: {nombre}")
                        printInfo(f"Sigla: {sigla}, Paralelo: {paralelo}")
                        printInfo(f"Departamento: {departamento}")
                        printInfo(f"Profesor: {profesor}")

                        baseDatosNueva[sigla][0]['Horario'], baseDatosNueva[sigla][0]['Profesores'] = agregarHorario(contador, fila, driver)
                        
                        # En caso de que haya ocurrido un error al extraer el horario
                        if baseDatosNueva[sigla][0]['Horario'] == None:
                            return False
                        
                        # Actualizar la sigla de la última asignatura válida
                        ultimaSigla = sigla
                        ultimoNombre = nombre
                        ultimoDepto = departamento
                    
                    # Ahora, en caso de que la sigla es vacía, entonces se trata de otro paralelo
                    else:
                        if ultimaSigla:
                            baseDatosNueva[ultimaSigla].append({
                                'Nombre': ultimoNombre,
                                'Departamento': ultimoDepto,
                                'Paralelo': paralelo,
                                'Profesores': [],
                                'Cupos': cupos,
                                'Horario': []
                            })
                        
                        # Añadir el horario
                        printInfo(f"Asignatura: {ultimaSigla}, Paralelo: {paralelo}")
                        baseDatosNueva[ultimaSigla][len(baseDatosNueva[ultimaSigla]) - 1]['Horario'], baseDatosNueva[ultimaSigla][len(baseDatosNueva[ultimaSigla]) - 1]['Profesores'] = agregarHorario(contador, fila, driver)

                        # En caso de que haya ocurrido un error al extraer el horario
                        if baseDatosNueva[ultimaSigla][len(baseDatosNueva[ultimaSigla]) - 1]['Horario'] == None:
                            return False
                            
                # Guardar la base de datos en el archivo correspondiente
                if not nombreCampus in baseDatosGlobal:
                    baseDatosGlobal[nombreCampus] = {}
                
                baseDatosGlobal[nombreCampus][periodo] = baseDatosNueva
                baseGuardada = guardarBaseDatos()
                
                # En caso de que no se haya podido guardar la base de datos
                if not baseGuardada:
                    print(f"")
                    printInfo(f"Ha ocurrido un error al obtener asignaturas desde SIGA. No se pudo guardar la base de datos.", "error")
                    return False
                
                # Aumentar el contador para el formulario del horario
                contador += 1

                if contador == 3:
                    break

            except Exception as e:
                printInfo(f"Error al procesar fila: {e}", "error")
                print(f"")
                return False        

    except Exception as e:
        printInfo(f"Error al generar base de datos: {e}", "error")
        print(f"")
        return False
        
    finally:
        # Cerrar el navegador
        driver.quit()

    # Dejar de medir el tiempo y calcular el tiempo transcurrido
    finTiempo = time.time()
    duracionScraping = finTiempo - inicioTiempo
    minutos, segundos = segundosAMinutos(duracionScraping)
    
    # Dejar como activo el ultimo campus y semestre
    ultimoCampus = nombreCampus
    ultimoSemestre = periodo

    # Mostrar el mensaje final de éxito, y salir
    print(f"")
    printInfo(f"Base de datos de asignaturas actualizada. Se guardaron un total de {contador + 1} asignaturas/paralelos en {nombreCampus}.")
    printInfo(f"Tiempo transcurrido: {minutos} minutos y {math.floor(segundos)} segundos.")
    printInfo(f"Presiona enter para volver al menú principal...")
    input("")
    return True

# Función que pregunta por los parámetros para hacer scraping
def prepararScraping():
    
    # Mostrar logo
    limpiarPantalla()
    mostrarLogo()
    
    # Periodo
    while True:
        try:
            printInfo(f"Periodo / Semestre: (ej: 2024-2): ")
            nombrePeriodo = input("> ")
            periodo = nombrePeriodo.replace("-", "")
            
            if not periodo or int(periodo) < 20151:
                print(f"")
                printInfo(f"Periodo inválido.")
            else:
                break
                
        except ValueError:
            print(f"")
            printInfo(f"Periodo inválido.")

    # Campus
    print(f"")
    print(f"1) Casa Central")
    print(f"2) Concepción")
    print(f"3) Santiago San Joaquín")
    print(f"4) Santiago Vitacura")
    print(f"5) Viña del Mar")
    print(f"")
    
    while True:
        printInfo(f"Campus/Sede: ")
        campus = input("> ")
        
        if campus not in ["1", "2", "3", "4", "5"]:
            print(f"")
            printInfo(f"Campus inválido.")
        
        else:
            # Transformar el valor del campus al índice arbitrario que usa el SIGA...
            # Concepción
            if campus == "2":
                campus = "4"
            
            # Santiago San Joaquín
            elif campus == "3":
                campus = "7"
            
            # Santiago Vitacura
            elif campus == "4":
                campus = "2"

            # Viña del Mar
            elif campus == "5":
                campus = "3"
            
            break
    
    # Jornada
    print(f"")
    print(f"1) Diurno")
    print(f"2) Vespertino")
    print(f"")
    
    while True:
        
        printInfo(f"Jornada: ")
        jornada = input("> ")
    
        if jornada not in ["1", "2"]:
            print(f"")
            printInfo(f"Jornada inválida.")
        
        else:
            break
    
    # Actualizar la base de datos con los parámetros especificados
    baseDatosActualizada = actualizarBaseDatos(periodo, campus, jornada)
    
    # Si falló la actualización
    if not baseDatosActualizada:
        return False
    
    # Si tuvo éxito
    else:
        return True

########################################################################################################
#                                     MANEJO DE ARCHIVOS                                               #

# Función que carga el archivo de configuración
def cargarConfig():
    
    global archivoConfiguracion
    
    try:
        # Leer el contenido del archivo JSON
        with open(archivoConfiguracion, "r", encoding = "utf-8") as archivo:
            configuracion = json.load(archivo)
        
        printInfo(f"Configuración cargada con éxito.")
        time.sleep(2)
    
    except FileNotFoundError:
        printInfo(f"El archivo de configuración no se encontró.", "error")
        return None
        
    except json.JSONDecodeError:
        printInfo(f"Error al decodificar el archivo JSON de configuración.", "error")
        return None
        
    except UnicodeDecodeError as e:
        printInfo(f"Error al decodificar el archivo {archivoConfiguracion}: {e}", "error")
        return None

    return configuracion

# Función que guarda el archivo de configuración
def guardarConfig():
    
    global archivoConfiguracion
    global configuracionGlobal
    
    # Crear un diccionario con las configuraciones
    configuracion = {
        "usuarioSiga": configuracionGlobal["usuarioSiga"],
        "passwordSiga": configuracionGlobal["passwordSiga"],
        "timeoutWeb": configuracionGlobal["timeoutWeb"],
        "driverHeadless": configuracionGlobal["driverHeadless"],
        "campusActual": configuracionGlobal["campusActual"],
        "semestreActual": configuracionGlobal["semestreActual"],
    }
    
    try:
        # Guardar el diccionario en un archivo JSON
        with open(archivoConfiguracion, "w", encoding = "utf-8") as archivo:
            json.dump(configuracion, archivo, indent = 4)
        
        printInfo(f"Configuración guardada con éxito en {archivoConfiguracion}.")
        time.sleep(2)

    except IOError as e:
        printInfo(f"Error al intentar guardar el archivo de configuración en {archivoConfiguracion}: {e}", "error")
        return False
        
    except json.JSONEncodeError as e:
        printInfo(f"Error al codificar la configuración en JSON: {e}", "error")
        return False
    
    except UnicodeEncodeError as e:
        printInfo(f"Error al intentar guardar el archivo de configuración: {e}", "error")
        return False
    
    except Exception as e:
        printInfo(f"Se produjo un error inesperado: {e}", "error")
        return False

    return True
    
# Función que carga una base de datos
def cargarBaseDatos():
    
    global archivoBaseDatos
    
    # Intentar cargar la base de datos
    try:
        with open(archivoBaseDatos, "r", encoding = "utf-8") as archivo:
            baseDatosAsignaturas = json.load(archivo)

        printInfo(f"Base de datos cargada exitosamente.")
        time.sleep(2)

    except FileNotFoundError:
        printInfo(f"Archivo de base de datos no encontrado: {archivoBaseDatos}", "error")
        return None
        
    except json.JSONDecodeError:
        printInfo(f"Error al decodificar el archivo JSON de la base de datos {archivoBaseDatos}", "error")
        return None

    except UnicodeDecodeError as e:
        printInfo(f"Error al decodificar el archivo {archivoBaseDatos}: {e}", "error")
        return None
        
    return baseDatosAsignaturas

# Función que guarda una base de datos
def guardarBaseDatos():
    
    global archivoBaseDatos
    global baseDatosGlobal
    
    try:
        with open(archivoBaseDatos, "w", encoding = "utf-8") as archivo:
            json.dump(baseDatosGlobal, archivo, indent = 4, ensure_ascii = False)
            
        printInfo(f"Base de datos guardada exitosamente en {archivoBaseDatos}.")
        time.sleep(2)
        
    except IOError as e:
        printInfo(f"Error al intentar guardar la base de datos en {archivoBaseDatos}: {e}", "error")
        return False
        
    except json.JSONDecodeError as e:
        printInfo(f"Error al codificar la base de datos en JSON: {e}", "error")
        return False
        
    except UnicodeEncodeError as e:
        printInfo(f"Error al codificar la base de datos en JSON: {e}", "error")
        return False
        
    except Exception as e:
        printInfo(f"Se produjo un error inesperado: {e}", "error")
        return False

    return True
    
# Función que guarda una copia de seguridad de la base de datos
def guardarBaseDatosBackup():
    
    global archivoBaseDatosBackup
    global baseDatosGlobal
    
    try:
        with open(archivoBaseDatosBackup, "w", encoding = "utf-8") as archivo:
            json.dump(baseDatosGlobal, archivo, indent = 4, ensure_ascii = False)

        time.sleep(1)
        
    except IOError as e:
        printInfo(f"Error al intentar guardar la base de datos en {archivoBaseDatosBackup}: {e}", "error")
        return False
        
    except json.JSONDecodeError as e:
        printInfo(f"Error al codificar la base de datos en JSON: {e}", "error")
        return False
        
    except UnicodeEncodeError as e:
        printInfo(f"Error al codificar la base de datos en JSON: {e}", "error")
        return False
        
    except Exception as e:
        printInfo(f"Se produjo un error inesperado: {e}", "error")
        return False

    return True

########################################################################################################
#                                           UTILIDADES                                                 #

# Función que pregunta por las credenciales del SIGA
def obtenerCredencialesSiga():
    print(f"")
    usuarioSiga = input("Usuario SIGA (@usm.cl): ")
    passwordSiga = getpass.getpass("Contraseña SIGA: ")
    print(f"")
    return usuarioSiga, passwordSiga

# Función que imprime un mensaje con colores y por defecto con un [+]
def printInfo(mensaje, color = "info", caja = True):
    
    colores = {
        "normal": Fore.WHITE,
        "info": Fore.LIGHTWHITE_EX,
        "error": Fore.RED,
        "advertencia": Fore.YELLOW,
        "exito": Fore.GREEN,
    }
    
    # Obtener el código de color del diccionario
    color = colores.get(color.lower(), Fore.WHITE)
    
    # Imprimir el mensaje con el color especificado
    if caja:
        print(f"{Fore.GREEN}[+]{color} {mensaje}{Style.RESET_ALL}")
    else:
        print(f"{color}{mensaje}{Style.RESET_ALL}")
        
    return

# Función que limpia la pantalla
def limpiarPantalla():
    # Para Windows
    if platform.system() == 'Windows':
        os.system('cls')
        
    # Para Linux, macOS (Unix)
    else:
        os.system('clear')
    return

# Función que cambia el título de la ventana
def cambiarTituloConsola(titulo):
    # Para Windows
    if platform.system() == 'Windows':
        os.system(f"title {titulo}")
        
    # Para Linux, macOS (Unix)
    else:
        sys.stdout.write(f"\033]0;{titulo}\007")
        sys.stdout.flush()
    return

# Función que transforma segundos a minutos
def segundosAMinutos(segundos):
    minutos = segundos // 60
    segundosRestantes = segundos % 60 
    return minutos, segundosRestantes

# Función que muestra el logo de Sedona
def mostrarLogo():
    printInfo(r"              _                   ", "advertencia", False)
    printInfo(r"             | |                  ", "advertencia", False)
    printInfo(r" ___  ___  __| | ___  _ __   __ _ ", "advertencia", False)
    printInfo(r"/ __|/ _ \/ _` |/ _ \| '_ \ / _` |", "advertencia", False)
    printInfo(r"\__ \  __/ (_| | (_) | | | | (_| |", "advertencia", False)
    printInfo(r"|___/\___|\__,_|\___/|_| |_|\__,_|", "advertencia", False)
    printInfo(r"                                  ", "advertencia", False)
    printInfo(f"Web-Scraper para el SIGA de la UTFSM", "info", False)
    print(f"")
    
    return

# Función que determina el semestre actual
def determinarSemestreActual():
    # Obtener la fecha actual
    fechaActual = datetime.now()
    
    # Extraer el año y el mes actuales
    año = fechaActual.year
    mes = fechaActual.month
    
    # Determinar el semestre
    if 1 <= mes <= 7:
        semestre = '1'
    else:
        semestre = '2'
    
    # Formar el código de semestre
    semestreRecomendado = f"{año}{semestre}"
    
    return semestreRecomendado
    
########################################################################################################
#                                             BÚSQUEDA                                                 #

# Función que muestra el horario de un paralelo
def mostrarHorario(horario):
    
    # Horas estáticas
    horasEstaticas = [ "8:15 - 9:25", "9:40 - 10:50", "11:05 - 12:15", "12:30 - 13:40", "14:40 - 15:50",
                        "16:05 - 17:15", "17:30 - 18:40", "18:50 - 20:00", "20:15 - 21:25", "21:40 - 22:50"
                     ]
    
    bloques = [f"{i}-{i+1}" for i in range(1, 20, 2)]
    
    # Crear la tabla con los bloques y las horas
    headers = ['Bloque', 'Hora'] + ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    table = []
    
    for i, (bloque, hora) in enumerate(zip(bloques, horasEstaticas)):
        if i < len(horario):
            row = [bloque, hora] + horario[i]
        else:
            row = [bloque, hora] + ['' for _ in range(7)]
        table.append(row)
    
    # Mostrar la tabla usando tabulate
    print(tabulate(table, headers = headers, tablefmt = 'grid'))

# Función que muestra la información de una asignatura
def mostrarInfoAsignatura(criterioBusqueda):
    global baseDatosGlobal
    global configuracionGlobal
    
    campusActual = configuracionGlobal["campusActual"]
    semestreActual = configuracionGlobal["semestreActual"]
    
    baseDatosAsignaturas = baseDatosGlobal[campusActual][semestreActual]
    
    encontrado = False
    paraleloBusqueda = None
    
    # Manejo de paralelos
    if "-" in criterioBusqueda:
        criterioBusqueda, paraleloBusqueda = criterioBusqueda.split('-')
    
    for sigla, detallesLista in baseDatosAsignaturas.items():
        for detalles in detallesLista:
            criterioBusquedaUpper = unidecode(criterioBusqueda.upper())
            nombreUpper = unidecode(detalles["Nombre"].upper())
            profesoresUpper = [unidecode(profesor.upper()) for profesor in detalles["Profesores"]]
            
            if (criterioBusquedaUpper in sigla.upper() or 
                criterioBusquedaUpper in nombreUpper or
                any(criterioBusquedaUpper in profesor for profesor in profesoresUpper)):

                if paraleloBusqueda is None or paraleloBusqueda == detalles["Paralelo"]:
                    encontrado = True
                    print(f"")
                    print(f"Sigla: {sigla}")
                    print(f"Nombre: {detalles['Nombre']}")
                    print(f"Departamento: {detalles['Departamento']}")
                    print(f"Paralelo: {detalles['Paralelo']}")
                    
                    profesoresStr = " | ".join(detalles["Profesores"])
                    print(f"Profesores: {profesoresStr}")
                    
                    print(f"Cupos: {detalles['Cupos']}")
                    print("Horario:")
                    print(f"")
                    mostrarHorario(detalles["Horario"])
    
    if not encontrado:
        print(f"")
        printInfo(f"No se encontraron resultados para '{criterioBusqueda}'.")
        
    return

# Función que pregunta que asignatura debería buscarse
def buscarAsignatura():
    
    # Mostrar el logo
    limpiarPantalla()
    mostrarLogo()
    
    printInfo(f"Advertencia: No todos los bloques de ayudantía/laboratorio están públicos en SIGA.", "advertencia")
    printInfo(f"Se recomienda usar la terminal en pantalla completa para que el horario renderice correctamente.", "advertencia")
    printInfo(f"Se utilizan los nuevos bloques de horas con descansos de 15 minutos.")
    print("")
    printInfo(f"Nombre/sigla/profesor de la asignatura a buscar (ej. INF155, MAT023-203): ")
    nombreSiglaAsignatura = unidecode(input("> ")).lower()
    
    # Buscar la asignatura
    mostrarInfoAsignatura(nombreSiglaAsignatura)

    printInfo(f"Presiona enter para volver al menú...")
    input()

    return
    
# Función que elimina el prefijo "Sala" de la asignatura
def normalizarNombreSala(nombreSala):
    if nombreSala.lower().startswith("sala "):
        return nombreSala[5:]  # Remover el prefijo "Sala "
    return nombreSala

# Función para buscar salas que coincidan con el término ingresado
def enumerarSalas(terminoBusqueda):
    
    global baseDatosGlobal
    global configuracionGlobal
    
    campusActual = configuracionGlobal["campusActual"]
    semestreActual = configuracionGlobal["semestreActual"]
    
    baseDatosAsignaturas = baseDatosGlobal[campusActual][semestreActual]    
    
    disponibilidadSalas = {}

    # Inicializar el diccionario con las salas encontradas
    for asignatura, detalles in baseDatosAsignaturas.items():
        for detalle in detalles:
            horario = detalle["Horario"]
            paralelo = detalle["Paralelo"]
            # Iterar sobre los días de la semana
            for diaIdx in range(7):
                # Iterar sobre los bloques de tiempo
                for bloqueIdx in range(10):
                    sala = horario[bloqueIdx][diaIdx]
                    # Solo considerar celdas no vacías
                    if sala:
                        salaNormalizada = normalizarNombreSala(sala)
                        if salaNormalizada not in disponibilidadSalas:
                            disponibilidadSalas[salaNormalizada] = {
                                (bloqueIdx, diaIdx): None for bloqueIdx in range(10) for diaIdx in range(7)
                            }
                        # Marcar la celda correspondiente con el código de la asignatura y el paralelo
                        disponibilidadSalas[salaNormalizada][(bloqueIdx, diaIdx)] = f"{asignatura} {paralelo}"

    # Si no hay término de búsqueda, asumimos que no se necesitan las salas encontradas
    if not terminoBusqueda:
        return disponibilidadSalas

    # Buscar las salas que contienen el término de búsqueda
    salasEncontradas = []
    terminoBusqueda = terminoBusqueda.lower()
    for sala in disponibilidadSalas.keys():
        if terminoBusqueda in sala.lower():
            salasEncontradas.append(sala)

    return salasEncontradas, disponibilidadSalas

# Función que muestra la disponibilidad de una sala en formato de tabla
def mostrarDisponibilidadSala(sala, disponibilidad):
    
    horasEstaticas = [ "8:15 - 9:25", "9:40 - 10:50", "11:05 - 12:15", "12:30 - 13:40", "14:40 - 15:50",
                        "16:05 - 17:15", "17:30 - 18:40", "18:50 - 20:00", "20:15 - 21:25", "21:40 - 22:50"
                     ]
    
    # Ajustar los bloques para que sean 1-2, 3-4, ..., 19-20
    bloques = [f"{i}-{i+1}" for i in range(1, 20, 2)]
    
    headers = ["Bloque", "Hora"] + ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    table = []
    
    for bloqueIdx in range(10):
        row = [bloques[bloqueIdx], horasEstaticas[bloqueIdx]]
        for diaIdx in range(7):
            ocupacion = disponibilidad[(bloqueIdx, diaIdx)]
            if ocupacion:
                row.append(ocupacion)  # Mostrar el código de la asignatura y el paralelo
            else:
                row.append(" ")  # Indicar que está vacío
        table.append(row)
    
    # Mostrar la tabla usando tabulate
    print(f"")
    printInfo(f"Bloques en uso de la sala {sala}:")
    print(tabulate(table, headers = headers, tablefmt = "grid"))
    
    return
    
# Función que pregunta que sala debería buscarse
def buscarSala():

    # Mostrar el logo
    limpiarPantalla()
    mostrarLogo()

    global baseDatosGlobal
    global configuracionGlobal
    
    campusActual = configuracionGlobal["campusActual"]
    semestreActual = configuracionGlobal["semestreActual"]
    
    baseDatosAsignaturas = baseDatosGlobal[campusActual][semestreActual]
    
    printInfo("Advertencia: No se muestran horarios de certámenes/ayudantías no incluídos en SIGA.", "advertencia")
    printInfo("También se debe considerar que actividades extraprogramáticas (asambleas, etc) que no están en SIGA.", "advertencia")
    print(f"")

    while True:
        
        # Pedir al usuario el término de búsqueda
        printInfo(f"Ingrese el nombre o parte del nombre de la sala a buscar: ")
        busquedaSala = unidecode(input("> ").lower())
        
        if not busquedaSala:
            print(f"")
            printInfo(f"Sala inválida.")
            print(f"")
            
        else:
            break

    # Buscar salas y obtener la disponibilidad
    salasEncontradas, disponibilidadSalas = enumerarSalas(busquedaSala)
    
    if salasEncontradas:
        print(f"")
        printInfo(f"Salas encontradas para '{busquedaSala}':")
        for sala in salasEncontradas:
            mostrarDisponibilidadSala(sala, disponibilidadSalas[sala])
            
    else:
        print(f"")
        printInfo(f"No se encontraron salas que coincidan con '{busquedaSala}'.")
    
    print(f"")
    printInfo(f"Presiona enter para volver al menú...")
    input()

    return    

# Función para determinar si una sala está disponible para un número específico de bloques consecutivos en un día
def salaDisponibleEnBloquesConsecutivos(disponibilidadSalas, sala, dia, bloqueInicio, bloquesNecesarios):
    for i in range(bloquesNecesarios):
        # Si algún bloque está ocupado...
        if disponibilidadSalas[sala].get((bloqueInicio + i, dia)):
            return False
    return True

# Función para determinar las salas disponibles en un día y bloques consecutivos específicos
def encontrarSalasDisponiblesEnDiaHora(dia, bloqueInicio, bloquesNecesarios):
    # Obtener la disponibilidad de todas las salas
    disponibilidadSalas = enumerarSalas(None)
    
    # Conjunto de todas las posibles salas
    salas = set(disponibilidadSalas.keys())
    
    # Calcular las salas ocupadas en los bloques consecutivos especificados
    salasDisponibles = {sala for sala in salas if salaDisponibleEnBloquesConsecutivos(disponibilidadSalas, sala, dia, bloqueInicio, bloquesNecesarios)}
    
    # Calcular las salas ocupadas
    salasOcupadas = salas - salasDisponibles

    return salasOcupadas, salasDisponibles

# Función que pregunta los parámetros de en donde buscar la sala
def buscarBloque():
    
    # Mostrar el logo
    limpiarPantalla()
    mostrarLogo()
    
    printInfo(f"Advertencia: No todas las salas del campus están listadas en SIGA.", "advertencia")
    
    # Diccionario para mapear días de la semana
    dias = {
        "lunes": 0, "martes": 1, "miercoles": 2,
        "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6
    }

    while True:
        print(f"")
        printInfo(f"Día de la semana (Lunes, Martes, ..., Domingo): ")
        d = input("> ")
        dia = unidecode(d.lower())

        # Buscar el día en el diccionario
        diaEnviar = dias.get(dia)
        
        if diaEnviar is not None:
            break
            
        else:
            print(f"")
            printInfo(f"Día inválido.")

    # Diccionario para mapear bloques a valores
    bloques = {
        "1-2": 0, "3-4": 1, "5-6": 2, "7-8": 3, "9-10": 4,
        "11-12": 5, "13-14": 6, "15-16": 7, "17-18": 8, "19-20": 9
    }

    while True:
        print(f"")
        printInfo(f"Bloque inicial (1-2, 3-4, ..., 19-20): ")
        b = input("> ")
        bloque = unidecode(b.lower())

        # Buscar el bloque en el diccionario
        bloqueEnviar = bloques.get(bloque)
        
        if bloqueEnviar is not None:
            break
            
        else:
            print(f"")
            printInfo(f"Bloque inválido.")
    
    while True:
        print(f"")
        printInfo(f"Cantidad de bloques libres consecutivos? (incluyendo {b}): ")
        try:
            bloquesNecesarios = int(input("> "))
            if bloquesNecesarios > 0:
                break
            else:
                print(f"")
                printInfo(f"Número inválido.")
                
        except ValueError:
            print(f"")
            printInfo(f"Número inválido.")
    
    # Obtener las salas ocupadas y disponibles para los bloques consecutivos
    salasOcupadas, salasDisponibles = encontrarSalasDisponiblesEnDiaHora(diaEnviar, bloqueEnviar, bloquesNecesarios)
    
    print(f"")
    printInfo(f"Salas ocupadas en {d} y {b} (para {bloquesNecesarios} bloques consecutivos):")
    
    if len(salasOcupadas) == 0:
        print(f"No hay salas ocupadas.")
    else:
        print(f"")
        print(tabulate([[sala] for sala in salasOcupadas], headers = ["Salas Ocupadas"], tablefmt = "grid"))
    
    print(f"")
    printInfo(f"Salas disponibles en {d} y {b} (para {bloquesNecesarios} bloques consecutivos):")
    
    if len(salasDisponibles) == 0:
        print(f"No hay salas disponibles.")
    else:
        print(f"")
        print(tabulate([[sala] for sala in salasDisponibles], headers = ["Salas Disponibles"], tablefmt = "grid"))
    
    print(f"")
    printInfo(f"Presione enter para volver al menú...")
    input()
    return

########################################################################################################

# Función que muestra el menú de configuración
def menuConfiguracion(): 
    
    global sedonaVersion
    global sedonaBuild
    global sedonaTag
    global archivoConfiguracion
    global baseDatosGlobal
    global configuracionGlobal
    
    campusActual = configuracionGlobal["campusActual"]
    semestreActual = configuracionGlobal["semestreActual"]

    ### Ciclo del menú configuración ###
    while True:
        
        # Mostrar logo
        limpiarPantalla()
        mostrarLogo()

        nombreSemestre = f"{semestreActual[:4]}-{semestreActual[4:]}"
        
        printInfo(f"Versión {sedonaVersion} | Build {sedonaBuild}-{sedonaTag}")
        print(f"")
        
        print(f"1) Cambiar campus/periodo actual ({campusActual} {nombreSemestre})")
        print(f"2) Cambiar las credenciales de ingreso ({configuracionGlobal["usuarioSiga"]})")
        print(f"3) Cambiar el tiempo de espera entre acciones ({configuracionGlobal["timeoutWeb"]} [s])")
        print(f"4) Activar modo headless para el driver actual ({configuracionGlobal["driverHeadless"]})")
        print(f"5) Volver al menú principal")
        print(f"")
        printInfo(f"Los cambios se efectuarán cuando se seleccione la opción 5")
        print(f"")
        
        seleccion = input(f"> ")
        
        # Cambiar campus/periodo
        if seleccion == "1":
            try:
                
                listaCampus = []
                
                print(f"")
                printInfo(f"Campus disponibles en la base de datos:")
                for campus in baseDatosGlobal:
                    listaCampus.append(unidecode(campus).lower())
                    print(campus)

                while True:

                    print(f"")
                    printInfo("Seleccionar campus:")
                    nuevoCampus = unidecode(input("> ")).lower()
                    
                    if nuevoCampus in listaCampus:

                        if nuevoCampus == "casa central":
                            configuracionGlobal["campusActual"] = "Casa Central"
                            campusActual = "Casa Central"
                        elif nuevoCampus == "concepcion":
                            configuracionGlobal["campusActual"] = "Concepción"
                            campusActual = "Concepción"
                        elif nuevoCampus == "santiago san joaquin":
                            configuracionGlobal["campusActual"] = "Santiago San Joaquín"
                            campusActual = "Santiago San Joaquín"
                        elif nuevoCampus == "santiago vitacura":
                            configuracionGlobal["campusActual"] = "Santiago Vitacura"
                            campusActual = "Santiago Vitacura"
                        elif nuevoCampus == "vina del mar":
                            configuracionGlobal["campusActual"] = "Viña del Mar"
                            campusActual = "Viña del Mar"
                        
                        break
                        
                    else:
                        print(f"")
                        printInfo(f"Campus inválido.")
                    
            except ValueError:
                print(f"")
                printInfo(f"Entrada inválida.")
                
            try:
                print(f"")
                printInfo(f"Semestres disponibles en la base de datos para {campusActual}:")
                for semestre in baseDatosGlobal[campusActual]:
                    print(f"{semestre[:4]}-{semestre[4:]}")
                
                while True:
                
                    print(f"")
                    printInfo("Seleccionar semestre:")
                    nuevoSemestre = unidecode(input("> ")).lower().replace("-", "")
                    
                    if nuevoSemestre in baseDatosGlobal[campusActual]:
                        configuracionGlobal["semestreActual"] = nuevoSemestre
                        semestreActual = nuevoSemestre
                        break
                        
                    else:
                        print(f"")
                        printInfo(f"Semestre inválido.")
                    
            except ValueError:
                print(f"")
                printInfo(f"Entrada inválida.")
                
            pass
            
        # Cambiar credenciales de ingreso
        elif seleccion == "2":
            configuracionGlobal["usuarioSiga"], configuracionGlobal["passwordSiga"] = obtenerCredencialesSiga()
            
            printInfo(f"Se ha cambiado el usuario actual.")
            time.sleep(2)
            pass
        
        # Cambiar el tiempo de espera entre acciones
        elif seleccion == "3":
            
            print(f"")
            printInfo(f"El tiempo de espera se refiere a cuántos segundos debe esperar entre acciones al acceder al SIGA.")
            printInfo(f"Un valor bajo hará que tome una cantidad menor de tiempo obtener las bases de datos, pero puede causar errores.")
            printInfo(f"Un valor alto (> 5) se recomienda para conexiones y computadores lentos. (default: 2)")

            while True:

                try:
                    # Intentar convertir la entrada a entero
                    configuracionGlobal["timeoutWeb"] = int(input("> "))
                    
                    # Validar que el tiempo sea un número positivo
                    if configuracionGlobal["timeoutWeb"] < 0:
                        printInfo(f"Valor inválido.")
                        continue
                        
                    break

                except ValueError:
                    printInfo(f"Valor inválido.")
                    
            pass
             
        # Activar modo headless
        elif seleccion == "4":
            print(f"")
            
            if (configuracionGlobal["driverHeadless"] == True):
                printInfo("Advertencia: desactivar el modo headless provoca que al momento de actualizar la base de datos se vea la ventana de Chrome.", "advertencia")
                printInfo("             Esto provoca que esté enfocada en todo momento, evitando que se puedan hacer otras acciones. (default: no, requiere reinicio)", "advertencia")
                print(f"")
                printInfo("Deseas continuar? (si/no)")
                seleccionHeadless = input("> ")
                
                if unidecode(seleccionHeadless.lower()) == "si":
                    configuracionGlobal["driverHeadless"] = False
                
                elif seleccionHeadless.lower() == "no":
                    configuracionGlobal["driverHeadless"] = True
                    
                else:
                    configuracionGlobal["driverHeadless"] = True
            
            else:
                configuracionGlobal["driverHeadless"] = True
            pass
            
        # Volver al menú principal
        elif seleccion == "5":
            print(f"")
            guardarConfig()
            time.sleep(2)
            return
        
        # Comando inválido
        else:
            pass
            
    return

def inicializar():
    
    # Cambiar el título de la consola
    cambiarTituloConsola("Sedona")
    
    # Mostrar logo
    limpiarPantalla()
    mostrarLogo()
    
    # Buscar actualizaciones
    try:
        printInfo("Buscando actualizaciones...")
        actualizacionStatus = buscarActualizaciones()
        
    except Exception:
        printInfo("No hay conexión a internet.")
    
    if not actualizacionStatus:
        printInfo("No se ha podido buscar actualizaciones.")
        print(f"")
        time.sleep(2)
    
    else:
        printInfo("No hay actualizaciones disponibles.")
        print(f"")
        time.sleep(1)
    
    # Intentar cargar archivo de configuración
    global configuracionGlobal
    configuracionGlobal = cargarConfig()
    
    # Variables default para las credenciales
    usuarioSiga = ""
    passwordSiga = ""
    
    if configuracionGlobal:
        usuarioSiga = configuracionGlobal.get("usuarioSiga")
        passwordSiga = configuracionGlobal.get("passwordSiga")
        timeoutWeb = configuracionGlobal.get("timeoutWeb")
        driverHeadless = configuracionGlobal.get("driverHeadless")
        campusActual = configuracionGlobal.get("campusActual")
        semestreActual = configuracionGlobal.get("semestreActual")
        
     # En caso de que la configuración esté vacía
    if not usuarioSiga and not passwordSiga:
        
        # Reestablecer variables default
        timeoutWeb = 2
        driverHeadless = True
        campusActual = "Santiago San Joaquín"
        semestreActual = determinarSemestreActual()

        # Obtener credenciales
        printInfo("Usuario y contraseña del SIGA inválida/no definida.")
        time.sleep(2)
        usuarioSiga, passwordSiga = obtenerCredencialesSiga()
        
        # Intentar guardar la configuración
        configuracionGlobal = {"usuarioSiga": usuarioSiga, "passwordSiga": passwordSiga, "timeoutWeb": timeoutWeb,
                                "driverHeadless": driverHeadless, "campusActual": campusActual, "semestreActual": semestreActual}

        configGuardadaFlag = guardarConfig()
     
        if not configGuardadaFlag:
            printInfo(f"Ha ocurrido un error que no permite continuar al programa.")
            printInfo(f"Presione enter para salir del programa...")
            input("")
            printInfo(f"Saliendo...")
            exit()       
    
    # Inicializar ChromeDriver
    global chromeDriverService
    global opcionesChromeDriver
    global errorChromeDriver
    
    errorChromeDriver = False
    
    try:
        chromeDriverService = Service(executable_path = ChromeDriverManager().install())
        opcionesChromeDriver = Options()
        opcionesChromeDriver.add_argument("--no-sandbox")
        opcionesChromeDriver.add_argument("--disable-dev-shm-usage")
        opcionesChromeDriver.add_argument("--log-level=3")
        opcionesChromeDriver.add_argument("--silent")
    
    except Exception as e:
        printInfo(f"Error iniciando ChromeDriver: {e}", "error")
        printInfo(f"No se podrá actualizar la base de datos en este momento.", "advertencia")
        print(f"")
        errorChromeDriver = True
        time.sleep(2)
    
    # Si se tiene activo driverHeadless
    if driverHeadless:
        opcionesChromeDriver.add_argument("--headless")
    
    # Intentar cargar la base de datos
    global baseDatosGlobal
    global ultimoCampus
    global ultimoSemestre
    baseDatosGlobal = cargarBaseDatos()

    # Si hubo un error con ChromeDriver y no hay base de datos...
    if not baseDatosGlobal and errorChromeDriver:
        printInfo(f"No hay conexión a internet ni una base de datos disponible.")
        printInfo(f"Sedona no puede continuar.")
        printInfo(f"Presione enter para salir del programa...")
        input("")
        printInfo(f"Saliendo...")
        return        

    # Si no hay base de datos presente
    if not baseDatosGlobal:
        time.sleep(1)
        print(f"")
        printInfo(f"No se ha encontrado ninguna base de datos.")
        printInfo(f"Presiona enter para actualizar la base de datos...")
        input("")
        
        baseCargada = prepararScraping()
        
        if not baseCargada:
            printInfo(f"Ha ocurrido un error grave que no le permite a Sedona funcionar.")
            printInfo(f"Revisa tu conexión, credenciales y el estado del SIGA e intenta más tarde.")
            printInfo(f"Presione enter para salir del programa...")
            input("")
            printInfo(f"Saliendo...")
            return
        
        else:
            baseDatosGlobal = cargarBaseDatos()
            configuracionGlobal["campusActual"] = ultimoCampus
            configuracionGlobal["semestreActual"] = ultimoSemestre
            
            semestreActual = configuracionGlobal["semestreActual"]
            campusActual = configuracionGlobal["campusActual"]
            
            guardarConfig()

    # Si todo salió bien, ir al menú principal
    menuPrincipal()
    return

def menuPrincipal():

    global errorChromeDriver
    global configuracionGlobal
    global ultimoCampus
    global ultimoSemestre
        
    ### Ciclo principal del menú ###
    while True:
        
        campusActual = configuracionGlobal["campusActual"]
        semestreActual = configuracionGlobal["semestreActual"]
        usuarioActual = configuracionGlobal["usuarioSiga"]
        
        # Mostrar el logo
        limpiarPantalla()
        mostrarLogo()
        
        # Opciones
        nombreSemestre = f"{semestreActual[:4]}-{semestreActual[4:]}"
        
        printInfo(f"Usuario actual: {usuarioActual} | Campus {campusActual} {nombreSemestre} ")
        print(f"")

        print(f"1) Buscar asignatura")
        print(f"2) Horarios salas")
        print(f"3) Salas disponibles en bloque")
        print(f"4) Actualizar base de datos de asignaturas")
        print(f"5) Configuración")
        print(f"6) Salir")
        print(f"")
        
        seleccion = input(f"> ")
        print(f"")
        
        # Buscar asignatura
        if seleccion == "1":
            buscarAsignatura()
            pass
            
        # Horarios salas
        elif seleccion == "2":
            buscarSala()
            pass
            
        # Salas disponibles en bloque
        elif seleccion == "3":
            buscarBloque()
            pass
            
        # Actualizar base de datos
        elif seleccion == "4":
            
            # Verificar si ChromeDriver está disponible
            if not errorChromeDriver:
            
                baseActualizada = prepararScraping()
                
                if not baseActualizada:
                    printInfo(f"No se ha podido actualizar la base de datos.")
                    printInfo(f"Revisa tu conexión, credenciales y el estado del SIGA e intenta más tarde.")
                    printInfo(f"Presione enter para volver al menú...")
                    input("")
                    pass
                
                else:
                    baseDatosGlobal = cargarBaseDatos()
                    configuracionGlobal["campusActual"] = ultimoCampus
                    configuracionGlobal["semestreActual"] = ultimoSemestre
                    
                    semestreActual = configuracionGlobal["semestreActual"]
                    campusActual = configuracionGlobal["campusActual"]
                    guardarConfig()
                    pass
                    
            else:
                printInfo(f"Sedona no puede actualizar la base de datos debido a un error de ChromeDriver.")
                printInfo(f"Revisa tu conexión y reinicia el programa.")
                printInfo(f"Presiona enter para volver...")
                input("")
                pass

        # Configuración
        elif seleccion == "5":
            menuConfiguracion()
            configuracionGlobal = cargarConfig()
            pass
            
        # Salir
        elif seleccion == "6":
            printInfo(f"Saliendo...")
            return
    
        # Comando inválido
        else:
            pass
        
    return

################################################################

# Inicializar colorama
init(autoreset = True)

# URL del SIGA
urlSiga = "https://siga.usm.cl/pag/home.jsp"

# Archivos de configuración y base de datos
archivoConfiguracion = "config.json"
archivoBaseDatos = "bdd_general.json"
archivoBaseDatosBackup = "bdd_general.json.bak"

# Variables globales
configuracionGlobal = None
baseDatosGlobal = None
chromeDriverService = None
opcionesChromeDriver = None
errorChromeDriver = None
ultimoSemestre = None
ultimoCampus = None

# Versión y build
sedonaVersion = "v1.4-sedona2"
sedonaBuild = "20240907"
sedonaTag = "master"

if __name__ == "__main__":
    try:
        inicializar()
    
    # Si se presiona CTRL-C
    except KeyboardInterrupt:
        print(f"")
        printInfo(f"Saliendo...")
        exit()