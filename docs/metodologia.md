# Metodología

## Enfoque del proyecto

La metodología del proyecto se basó en pruebas defensivas controladas, análisis de logs reales y validación técnica de controles de seguridad de correo.

El objetivo no fue generar volumen artificial, sino registrar únicamente eventos que pudieran justificarse mediante evidencias reales.

## Principios de trabajo

- No inflar métricas manualmente.
- Diferenciar pruebas intentadas de pruebas validadas.
- Registrar eventos solo cuando existía evidencia técnica.
- Mantener backups antes de cambios relevantes.
- Documentar rollback cuando se modificaba el dashboard.
- Conservar evidencias para auditoría y defensa técnica.

## Fuentes de evidencia

Las principales fuentes de evidencia fueron:

- respuestas SMTP reales;
- negociación TLS real;
- registros de `/var/log/syslog`;
- eventos de Postfix;
- validaciones de OpenDMARC;
- validaciones de OpenDKIM;
- consultas DNS;
- transcripts de pruebas;
- CSV SOC generado automáticamente.

## Criterio de validación

Una prueba se consideró válida cuando cumplía al menos uno de estos criterios:

- respuesta SMTP concluyente;
- registro en syslog;
- rechazo explícito por política DMARC;
- validación TLS con cipher negociado;
- validación SPF/DKIM mediante herramienta o consulta;
- evidencia de rechazo o bloqueo por el servidor.

## Tipos de pruebas realizadas

Se trabajó con diferentes familias de pruebas:

- abuso SMTP;
- autenticación fallida;
- destinatarios inexistentes;
- validaciones TLS;
- SPF fail;
- DKIM roto;
- DKIM ausente;
- rotación DKIM;
- dominios lookalike;
- spoofing rechazado por DMARC.

## Tratamiento de datos

Para el portfolio público se creó una versión sanitizada del dataset original.

Se anonimizaron:

- IPs;
- rutas internas;
- sesiones;
- direcciones externas;
- información sensible.

## Resultado

El resultado final fue un dashboard SOC con 270 pruebas totales agregadas y 190 eventos SOC procesados, acompañado de evidencias técnicas y documentación orientada a portfolio profesional.

