# PhisDefense SOC & Email Security Lab

Portfolio técnico de ciberseguridad orientado a Blue Team, SOC y seguridad de correo electrónico.

Este proyecto fue desarrollado como TFM y convertido en una pieza de portfolio profesional para mostrar capacidades prácticas en análisis de logs, validación de controles defensivos, automatización y desarrollo de dashboards SOC.

## Resumen

PhisDefense es un laboratorio defensivo centrado en seguridad de correo electrónico.

El proyecto incluye:

- configuración y validación de SPF, DKIM y DMARC;
- política DMARC progresiva hasta p=reject;
- pruebas reales de STARTTLS SMTP e IMAPS TLS;
- detección de SMTP AUTH fallido;
- pruebas de destinatarios inexistentes;
- validación de DKIM roto, DKIM ausente y rotación DKIM;
- análisis de dominios lookalike;
- pruebas externas de spoofing rechazadas por DMARC;
- procesamiento de logs reales;
- dashboard SOC desarrollado en Python/Dash.

## Resultados principales

- 270 pruebas totales agregadas en el dashboard.
- 190 eventos SOC procesados y categorizados.
- 3 eventos spoofing_reject registrados.
- Evidencias reales conservadas y sanitizadas para portfolio.
- Dataset público anonimizado.

## Skills demostradas

- Linux administration
- Email security
- SPF, DKIM, DMARC
- Postfix
- OpenDMARC
- OpenDKIM
- Python
- Dash / Plotly
- Pandas
- Log analysis
- SOC monitoring
- Blue Team methodology
- Evidence handling
- Security documentation

## Documentación

- docs/arquitectura.md
- docs/metodologia.md
- docs/pruebas-soc.md
- docs/spoofing-dmarc.md
- docs/metricas-soc.md
- docs/privacidad.md

## Dataset público

- data-samples/bateria_pruebas_soc_sample.csv

## Evidencias públicas

Las evidencias incluidas en este repositorio están anonimizadas.

El objetivo es demostrar metodología, validación técnica y resultados sin exponer información sensible del servidor original.

## Dashboard demo

El servidor original del TFM puede no estar activo en el futuro.

La siguiente fase del portfolio será publicar una demo interactiva del dashboard usando datos estáticos y sanitizados.

## Nota final

Este repositorio forma parte de mi portfolio profesional en ciberseguridad.

El objetivo es mostrar experiencia práctica en tareas cercanas a un entorno SOC real:

- análisis de eventos;
- detección de anomalías;
- validación de controles;
- documentación de evidencias;
- automatización;
- visualización de métricas defensivas.

