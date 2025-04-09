# Sedona

### ¿Qué es Sedona?

Me gusta llamarlo un **“Administrador de Ramos”** para el SIGA de la UTFSM. Es un script que permite resolver un problema real del sistema: su incapacidad de mostrar el horario de las salas.

La idea nació cuando un amigo me preguntó si había alguna forma de encontrar salas vacías para estudiar. Me quedé pensando por un momento, hasta que decidí que sería un desafío interesante para perder el tiempo.

Me tomó cerca de una semana crear algo medianamente usable, luego de días de investigación y por sobre todo, mucho ensayo y error.

Cabe destacar que este proyecto es completamente personal, y no forma parte de ninguna asignatura o tarea.

### Características principales

- Automatiza la extracción de datos por SIGA utilizando Selenium y ChromeDriver.
- Extrae y organiza los horarios de asignaturas por campus, semestre y sala.
- Permite encontrar salas vacías en base a los horarios recopilados.
- Guarda la información localmente como un diccionario indexado.
- Permite la búsqueda de asignaturas por profesor, paralelo, sigla o nombre.
- Es software libre y completamente auditable.

### Instalación/Uso

Se requiere Python 3 instalado. Instalar las librerías requeridas con:

```python
pip install -r requirements.txt
```

Y ejecutar en Windows con:

```python
py sedona.py
```

o en Unix(-like):

```python
python3 sedona.py
```

Debería funcionar en Windows, Linux y Mac (aún no probado completamente en este último)

### Limitaciones
Aunque Sedona funciona bastante bien, tiene limitaciones importantes, por lo cual podría considerarse poco confiable:

- No todas las actividades están en SIGA: asambleas, ayudantías, reuniones, defensas, etc. Esto puede hacer que Sedona marque una sala como vacía cuando no lo está.

- Los horarios cambian frecuentemente al inicio del semestre, así que no es buena idea scrapear justo en esa fecha. (Lamentablemente no hay una fecha ideal para scrapear, yo recomiendo un mes desde el inicio de semestre)

---

## ¿Qué es SIGA?

SIGA (Sistema de Información y Gestión Académica) es la plataforma oficial utilizada por la Universidad Técnica Federico Santa María (UTFSM) para gestionar información académica de alumnos y docentes. A través de esta, los estudiantes pueden inscribir asignaturas, revisar notas, ver horarios, etc.

Sin embargo, no permite consultar los horarios detallados de uso de salas, lo que Sedona busca solucionar.

### ¿Cómo se obtiene la información de asignaturas?

SIGA, comprensiblemente, no posee una API pública (y probablemente tampoco una privada, aunque eso es especulación). Debido a esto, tuve que investigar cómo se presenta la información al usuario en el navegador, y cómo automatizar la extracción de datos desde allí de forma ordenada.

### Cómo (yo creo) que funciona SIGA

No tengo acceso al backend ni a la base de datos de SIGA, y no me interesa tanto. Lo que importa es cómo presenta la información en el navegador. Pasé algunos días entendiendo cómo funcionaban los *frames*, y noté que se utiliza JavaServer Pages como framework, cargando múltiples frames simultáneamente.

Obviamente, inspeccioné el código fuente visible a través de “Inspeccionar elemento” y analicé cómo interactúan los distintos componentes de la interfaz.

---

## Ahora, ¿Cómo se hace el scraping?

Utilizo **Selenium**, una herramienta multiplataforma muy conocida para automatizar navegadores. En este caso, opté por **ChromeDriver** por ser compatible con Google Chrome.

El script inicia “a ciegas”, buscando elementos por su XPath, nombre de frame, o nombre de etiqueta. Existen múltiples "inconsistencias" que dificultan el proceso, como:

- El nombre de la sala puede o no incluir la palabra "Sala".
- A veces aparece el nombre de la carrera o del profesor antes.
- Las filas del horario tienen encabezados numéricos arbitrarios, lo cual debe ser mapeado manualmente.

Y estas son sólamente **algunos** de los obstáculos que encontré al estudiar el frontend de SIGA.

### ¿Por qué es tan lento el scraping?

Selenium **navega manualmente** por SIGA, lo que incluye:

1. Acceder a SIGA.
2. Navegar a la sección de “Horario Asignaturas”.
3. Leer todas las asignaturas listadas (900+).
4. Para cada una:
   - Cargar su horario.
   - Cambiar de ventana
   - Extraer la información.
   - Volver a la lista de asignaturas.

Todo esto puede tardar **más de 10 segundos por asignatura**, por lo que el scraping completo puede tomar horas.

Claramente no es un proceso muy eficiente. Hay formas de mejorarlo? Por supuesto. Yo no conozco mucho de Selenium más que lo justo y necesario para hacer que este script funcione, por lo que de seguro debe haber una mejor forma de hacerlo.

## ¿Por qué no usar paralelización/multithreading?

Buena pregunta. Obviamente, el scraping sería mucho más rápido si pudiera usar múltiples hilos, pero lamentablemente **Selenium no se lleva bien con la multihilación**.

Cada instancia de navegador es pesada, difícil de sincronizar, y puede entrar en conflicto con las demás. Aunque se podría pensar en usar semáforos o colas, la sobrecarga de coordinación complica demasiado el proceso.

### Rate-limiting y sobrecarga

Como cualquier servidor web, SIGA debe soportar la carga miles de estudiantes. Ahora imagina este escenario un tanto extremo:

- 100 personas usando Sedona al mismo tiempo.
- Cada una tiene un procesador de 8 núcleos, por lo que **idealmente** cada una corre 8 instancias de scraping en paralelo.

Eso son 800 sesiones golpeando SIGA simultáneamente con solicitudes.

Ahora, esto no suena como mucho, pero recuerda por un segundo las tomas de ramos. En ese sistema, una cola virtual debe ser incluida para evitar que todo el sistema colapse ante los +10.000 alumnos que intentan acceder (sin contar las multicuentas, ni el hecho de que cada campus tiene días distintos para inscribir asignaturas!).

Se entiende la magnitud del problema ahora? Imagina esas 10.000 personas haciendo scraping con Sedona, cada una con 8 instancias.

**Y eso no es todo!** No todas las personas entienden este problema, por lo que apenas las asignaturas se publiquen, probablemente intentarían scrapear al mismo tiempo. **Caos total!**

### Centralización

La solución ideal sería un servidor centralizado que haga el scraping periódicamente, y Sedona se limite a consultar una base de datos remota ya actualizada.

La versión actual implementa algo similar, pero limitado al **Campus San Joaquín**, ya que cada campus/sede tiene sus asignaturas distintas, por lo que tendría que extraer los datos todo el día, lo cual no creo que a la Universidad le agrade.

Cabe destacar que el servidor centralizado actualiza su base de datos ocasionalmente (cuando tenga tiempo realmente, lo cual es bastante raro).

---

## ¿Cómo se guarda la base de datos?

La "base de datos" es en realidad un **diccionario** en Python con la siguiente estructura:

```python
datos[campus][semestre][asignatura]
```
Cada asignatura contiene sus propios atributos como nombre, profesores, y una matriz simple con su horario.

Gracias a que Python usa tablas hash para sus diccionarios, la búsqueda promedio es de **O(1)**, ideal para manejar las más de 900 asignaturas.

¿Es lo óptimo? No. Usar una base de datos real como SQLite sería más escalable, pero también más complejo.

## Que viene ahora?  
No lo sé. Tengo varias ideas sobre características nuevas para implementar, e incluso escribir un nuevo programa mucho más atractivo visualmente, que sea un verdadero gestor de horarios, con sugerencias para evitar topes, etc.

**Pero no tengo tiempo para eso**. Y lamentablemente, tampoco tengo tiempo para manejar pull requests.

# ⚠️ DISCLAIMER!

El uso de este software cae puramente bajo la responsabilidad del usuario.
Este software no pretende dañar o robar información, su propósito está destinado a fines educativos y de apoyo para los estudiantes.
El software, por defecto, sólamente obtiene información de los horarios de la UTFSM, y no modifica ni obtiene otro tipo de información.
Se debe proporcionar un usuario y contraseña de una cuenta @usm.cl de un alumno regular para que este software funcione.
Ninguno de los datos obtenidos mediante el software, o ingresados por el usuario, son utilizados con fines maliciosos ni subidos a Internet.
Ante cualquier duda, este software es open source, y su código es libremente accesible y modificable.
Este software debe considerarse en beta, y puede fallar en cualquier momento. 
Este software no fue desarrollado ni patrocinado por la Universidad Técnica Federico Santa María.

En resumen, sea responsable y recuerde las clases de Ética de su malla curricular.
