<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/bd7a0f06-190b-4a8e-90ad-7a1baef7b402" />

# Asistente BI - Dashboard con IA

---

## Instrucciones de Ejecución Rápida

Este proyecto está pre-configurado para funcionar de inmediato sin necesidad de configuraciones adicionales.

1.  **Requisito:** Tener Docker y Docker Compose instalados.
2.  **Ejecución:** En la raíz del proyecto, ejecute el comando:
    ```bash
    sudo docker-compose up --build -d
    ```
3.  **Acceso:** Una vez finalizada la construcción, acceda a: **[http://localhost](http://localhost)**

---

## Resumen del Proyecto

Proyecto de Business Intelligence con asistente de IA integrado, dashboard interactivo (GraphicWalker) y arquitectura de microservicios gestionada por Docker y Nginx.

---

## Arquitectura del Sistema

El proyecto utiliza una estructura de microservicios para garantizar la escalabilidad y seguridad:

1.  **Nginx (Gateway):** Actúa como proxy reverso exponiendo el puerto 80.
    *   `http://localhost/` -> Frontend (React + Vite)
    *   `http://localhost/api/` -> Backend (FastAPI)
    *   `http://localhost/docs` -> Documentación de API (Swagger UI)
    *   `http://localhost/health` -> Estado del sistema

2.  **Frontend:** Contenedor Nginx Alpine sirviendo la build optimizada de React. No está expuesto directamente al exterior.

3.  **API:** Microservicio desarrollado en Python con FastAPI. Gestiona la comunicación con Google Gemini para la traducción de lenguaje natural a SQL.

4.  **Base de Datos:** PostgreSQL 15. Aislada en la red interna de Docker. Incluye un sistema de persistencia mediante volúmenes y auto-población automática con 10,000 registros para pruebas inmediatas.

---

## Instalación y Despliegue

1.  **Clonar el repositorio:**
    ```bash
    git clone <url-del-repositorio>
    cd AsistenteBi
    ```

2.  **Variables de Entorno:**
    El archivo `.env.example` ya contiene llaves de prueba operativas. Para entornos de producción, cree un archivo `.env` basado en este:
    ```bash
    cp .env.example .env
    ```

3.  **Despliegue de Contenedores:**
    ```bash
    sudo docker-compose up --build -d
    ```
    *El servicio de la API implementa un healthcheck que espera a que la base de datos esté completamente disponible antes de iniciar el servidor web.*

---

## Seguridad

*   Los servicios internos (Base de Datos, API, Frontend) no exponen puertos al host, centralizando todo el tráfico a través de Nginx en el puerto 80.
*   El frontend se sirve como archivos estáticos optimizados, eliminando la necesidad de servidores de desarrollo en el despliegue final.

---

## Estructura del Proyecto

*   `/src`: Código fuente del Backend (FastAPI).
*   `/frontend-bi`: Código fuente del Frontend (React).
*   `/nginx`: Configuración del Proxy Reverso.
*   `docker-compose.yml`: Orquestación de servicios.
*   `manual_usuario.md`: Documentación utilizada por la IA para el contexto de consultas.
