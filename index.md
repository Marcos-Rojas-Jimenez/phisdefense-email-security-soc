\# PhisDefense SOC \& Email Security Lab



Portfolio tecnico de ciberseguridad orientado a Blue Team, SOC y seguridad de correo electronico.



Este proyecto fue desarrollado como TFM y convertido en una pieza de portfolio profesional para mostrar capacidades practicas en analisis de logs, validacion de controles defensivos, automatizacion y desarrollo de dashboards SOC.



\## Resumen



PhisDefense es un laboratorio defensivo centrado en seguridad de correo electronico.



El proyecto incluye:



\- configuracion y validacion de SPF, DKIM y DMARC;

\- politica DMARC progresiva hasta p=reject;

\- pruebas reales de STARTTLS SMTP e IMAPS TLS;

\- deteccion de SMTP AUTH fallido;

\- pruebas de destinatarios inexistentes;

\- validacion de DKIM roto, DKIM ausente y rotacion DKIM;

\- analisis de dominios lookalike;

\- pruebas externas de spoofing rechazadas por DMARC;

\- procesamiento de logs reales;

\- dashboard SOC desarrollado en Python/Dash.



\## Resultados principales



\- 270 pruebas totales agregadas en el dashboard.

\- 190 eventos SOC procesados y categorizados.

\- 3 eventos spoofing\_reject registrados.

\- Evidencias reales conservadas y sanitizadas para portfolio.

\- Dataset publico anonimizado.



\## Skills demostradas



\- Linux administration

\- Email security

\- SPF, DKIM, DMARC

\- Postfix

\- OpenDMARC

\- OpenDKIM

\- Python

\- Dash / Plotly

\- Pandas

\- Log analysis

\- SOC monitoring

\- Blue Team methodology

\- Evidence handling

\- Security documentation



\## Documentacion



\- docs/arquitectura.md

\- docs/metodologia.md

\- docs/pruebas-soc.md

\- docs/spoofing-dmarc.md

\- docs/metricas-soc.md

\- docs/privacidad.md



\## Dataset publico



\- data-samples/bateria\_pruebas\_soc\_sample.csv



\## Video demo



He preparado una demo en video mostrando el funcionamiento del dashboard SOC, las metricas principales, las pruebas SMTP, los eventos SOC y las evidencias de seguridad de correo.



Proximamente anadire aqui el enlace al video publicado.



\## Evidencias publicas



Las evidencias incluidas en este repositorio estan anonimizadas.



El objetivo es demostrar metodologia, validacion tecnica y resultados sin exponer informacion sensible del servidor original.



\## Dashboard demo



El servidor original del TFM puede no estar activo en el futuro.



La siguiente fase del portfolio sera publicar una demo interactiva del dashboard usando datos estaticos y sanitizados.



\## Nota final



Este repositorio forma parte de mi portfolio profesional en ciberseguridad.



El objetivo es mostrar experiencia practica en tareas cercanas a un entorno SOC real:



\- analisis de eventos;

\- deteccion de anomalias;

\- validacion de controles;

\- documentacion de evidencias;

\- automatizacion;

\- visualizacion de metricas defensivas.

