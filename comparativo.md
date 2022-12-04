# Comparación entre modelos de despliegue

## Google App Engine vs Auto Scaling en Compute Engine

### Comparación de desplegar nueva versión

- Google App Engine en general es más conveniente/ergonómico:
    - No hay que preocuparse por la configuración del balanceador de carga
    - Favorece la práctica de infraestructura como código
    - La definición de escalabilidad se hace en el mismo sitio donde se define la aplicación
    - No hay que preocuparse por el mantenimiento del sistema operativo
        - No hay que preocuparse por la seguridad del sistema operativo

### Comparación de escalabilidad

- Ambas plataformas ofrecen escalabilidad horizontal
    - Auto Scaling Groups es más complejo, y en ocasiones presenta problemas con el número de IP's disponibles para las máquinas virtuales
    - Google App Engine es más sencillo, y no presenta problemas con el número de IP's disponibles para las instancias
    - Auto Scaling Groups es más flexible, ya que permite escalar verticalmente las instancias
    - Google App Engine es más limitado, ya que no permite escalar verticalmente las instancias

- Google App Engine está hecho para aplicaciones solamente Web, pues es necesario que la aplicación respondan a peticiones HTTP por parte del balanceador de carga
    - Auto Scaling Groups permite desplegar aplicaciones que no respondan a peticiones HTTP, como por ejemplo (worker)
    - Para manejar aplicaciones no web en App Engine se puede ejecutar un servidor web en paralelo, y se configura para que siempre responda ok

### Otros aspectos

- Google App Engine genera HTTPS y una url para probar la aplicación
- Desplegar nueva versión en Google App Engine es más rápido que en Auto Scaling Groups, un simple llamado por linea de comandos es suficiente
