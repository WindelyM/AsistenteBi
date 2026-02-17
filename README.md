# Asistente BI - Dashboard con IA

---

## Requisito Crítico: Clave de API

Para que las funciones de Inteligencia Artificial (traducción de lenguaje natural a SQL) operen correctamente, **es obligatorio contar con una API Key de Google Gemini**.

1.  Obtenga su clave gratuita en: [Google AI Studio](https://aistudio.google.com/app/apikey)
2.  Cree un archivo llamado `.env` en la raíz del proyecto basándose en el archivo `.env.example`.
3.  Pegue su clave en la variable: `APP_GOOGLE_API_KEY=su_clave_aqui`

*Sin esta clave, el sistema de contenedores iniciará pero el asistente de chat devolverá errores de conexión.*

---

## Instrucciones de Ejecución Rápida

Este proyecto está pre-configurado para funcionar mediante contenedores.

1.  **Requisito:** Tener Docker y Docker Compose instalados.
2.  **Preparación:** Asegúrese de haber creado su archivo `.env` con la API Key.
3.  **Ejecución:** En la raíz del proyecto, ejecute en su terminal:
    ```bash
    sudo docker-compose up --build -d
    ```
4.  **Acceso:** Una vez finalizada la construcción, acceda a: **http://localhost**

---

## Resumen del Proyecto

Proyecto de Business Intelligence con asistente de IA integrado, dashboard interactivo (GraphicWalker) y arquitectura de microservicios gestionada por Docker y Nginx.

---

## Arquitectura del Sistema

El proyecto utiliza una estructura de microservicios para garantizar la escalabilidad y seguridad:

1.  **Nginx (Gateway):** Actúa como proxy reverso exponiendo el puerto 80.
    *   http://localhost/ -> Frontend (React + Vite)
    *   http://localhost/api/ -> Backend (FastAPI)
    *   http://localhost/docs -> Documentación de API (Swagger UI)
    *   http://localhost/health -> Estado del sistema

2.  **Frontend:** Contenedor Nginx Alpine sirviendo la build optimizada de React.

3.  **API:** Microservicio desarrollado en Python con FastAPI. Gestiona la comunicación con Google Gemini.

4.  **Base de Datos:** PostgreSQL 15. Incluye auto-población automática con 10,000 registros para pruebas inmediatas.

---

## Configuración de Variables de Entorno

El archivo `.env` es fundamental para el despliegue. Asegúrese de configurar los siguientes valores:

*   `POSTGRES_USER`: Usuario de la base de datos (por defecto: postgres).
*   `POSTGRES_PASSWORD`: Contraseña de la base de datos.
*   `APP_GOOGLE_API_KEY`: Su clave de Google Gemini (Requerido).
*   `APP_DEBUG`: Establecer en False para entornos de demo/producción.

---

## Seguridad y Persistencia

*   **Aislamiento de Red:** Los servicios internos no exponen puertos al host, centralizando todo el tráfico a través de Nginx.
*   **Persistencia de Datos:** Utiliza volúmenes de Docker para asegurar que los 10,000 registros generados no se borren al reiniciar los contenedores.
*   **Gestión de Claves:** El archivo `.env` está incluido en el .gitignore para evitar filtraciones accidentales de credenciales.

---

## Estructura del Proyecto

*   `/src`: Código fuente del Backend (FastAPI).
*   `/frontend-bi`: Código fuente del Frontend (React).
*   `/nginx`: Configuración del Proxy Reverso.
*   `docker-compose.yml`: Orquestación de servicios.
*   `manual_usuario.md`: Documentación utilizada por la IA para el contexto de consultas.
