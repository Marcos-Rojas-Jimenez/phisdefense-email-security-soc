# PhisDefense SOC & Email Security Lab

Proyecto práctico de ciberseguridad orientado a Blue Team, SOC y seguridad de correo electrónico.

Este proyecto nació como TFM y fue desarrollado como un laboratorio defensivo real para validar controles de seguridad de correo, analizar eventos de seguridad y construir un dashboard SOC propio.

## Objetivo

Construir un entorno defensivo para validar y monitorizar controles como:

- SPF
- DKIM
- DMARC p=reject
- STARTTLS SMTP
- IMAPS TLS
- SMTP AUTH
- detección de spoofing
- dominios lookalike
- análisis de logs de Postfix, OpenDMARC y OpenDKIM

## Resultados principales

- Dashboard SOC desarrollado en Python/Dash
- 270 pruebas totales agregadas en el dashboard
- 190 eventos SOC procesados y categorizados
- Pruebas reales de SMTP, TLS, DKIM, SPF y spoofing
- Evidencias técnicas conservadas
- Automatización de procesamiento de logs
- Visualización de métricas defensivas

## Métricas SOC finales

- recipient_unknown: 58
- auth_fail: 55
- tls_starttls_smtp: 19
- tls_imaps: 14
- dkim_absent: 8
- dkim_broken: 8
- spf_fail: 8
- lookalike_domain: 7
- dkim_rotation: 6
- open_relay_test: 3
- spoofing_reject: 3
- smtp_auth_success: 1

## Skills demostradas

- Linux administration
- Email security
- SPF, DKIM, DMARC
- Postfix, OpenDMARC y OpenDKIM
- Python
- Dash y Plotly
- Log analysis
- SOC monitoring
- Blue Team methodology
- Evidence handling
- Security documentation

## Estructura del repositorio

docs/
- arquitectura.md
- metodologia.md
- pruebas-soc.md
- spoofing-dmarc.md
- metricas-soc.md
- privacidad.md

data-samples/
- bateria_pruebas_soc_sample.csv

screenshots/
- capturas del dashboard

scripts-sanitized/
- ejemplos de scripts anonimizados

evidence-samples/
- evidencias públicas anonimizadas

## Dataset público

El archivo data-samples/bateria_pruebas_soc_sample.csv contiene una versión sanitizada del CSV SOC original.

Se han anonimizado IPs, rutas internas, sesiones, direcciones externas e información sensible.

## Nota

El servidor original utilizado durante el TFM puede no estar activo en el futuro. Este repositorio conserva una versión documentada, sanitizada y orientada a portfolio profesional del proyecto.

