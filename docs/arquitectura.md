# Arquitectura

## Visión general

PhisDefense SOC & Email Security Lab es un laboratorio defensivo de seguridad de correo electrónico orientado a monitorización SOC, validación de controles y análisis de evidencias.

El flujo general del proyecto fue:

Internet
→ Postfix / OpenDMARC / OpenDKIM / Dovecot
→ Syslog
→ Procesamiento SOC automatizado
→ CSV de eventos
→ Dashboard Python/Dash

## Componentes principales

### Postfix

Servidor SMTP utilizado para recibir, procesar y registrar eventos relacionados con correo electrónico.

### OpenDMARC

Componente utilizado para validar DMARC y aplicar política de rechazo en intentos de suplantación del dominio.

### OpenDKIM

Componente utilizado para gestionar firma DKIM y validar pruebas relacionadas con DKIM correcto, DKIM roto, DKIM ausente y rotación de selector.

### Dovecot

Servicio utilizado para validación IMAPS TLS.

### Syslog

Fuente principal de evidencias. Los eventos relevantes se extrajeron desde logs reales del sistema.

### Procesamiento SOC

Scripts desarrollados para transformar eventos de syslog y pruebas técnicas en registros estructurados dentro de un CSV SOC.

### Dashboard SOC

Dashboard desarrollado en Python/Dash para visualizar métricas defensivas, categorías de eventos, evidencias y resultados de pruebas.

## Flujo de datos

1. Se ejecutan pruebas controladas de seguridad de correo.
2. Los servicios de correo generan evidencias en syslog.
3. Los scripts SOC procesan esas evidencias.
4. Los eventos se almacenan en CSV.
5. El dashboard carga los CSV y genera KPIs, tablas y gráficas.
6. Las evidencias se conservan para auditoría y presentación.

## Fuentes de datos

El dashboard trabaja principalmente con:

- bateria_pruebas.csv
- bateria_pruebas_soc.csv
- bateria_pruebas_local.csv
- bateria_pruebas_metricas.csv
- bateria_pruebas_email_threats.csv

Para el portfolio público se conserva una versión sanitizada de bateria_pruebas_soc.csv.

## Métrica global

El dashboard muestra 270 pruebas totales agregando:

- 80 pruebas principales
- 190 eventos SOC

Además existen CSV auxiliares usados para otras vistas y métricas del laboratorio.

