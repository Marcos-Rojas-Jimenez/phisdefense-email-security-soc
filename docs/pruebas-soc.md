# Pruebas SOC

## Resumen

El laboratorio PhisDefense incluye pruebas SOC orientadas a validar controles defensivos de correo electrónico y comportamiento del servidor ante eventos reales o controlados.

El objetivo fue registrar únicamente pruebas con evidencia técnica verificable.

## Volumen final

El dashboard contiene:

- 270 pruebas totales agregadas
- 190 eventos SOC procesados y categorizados

## Categorías principales

### Auth fail

Intentos de autenticación SMTP fallida.

Objetivo:

- validar detección de credenciales inválidas;
- registrar eventos SASL AUTH fallidos;
- comprobar trazabilidad en syslog.

### Recipient unknown

Pruebas contra destinatarios inexistentes.

Objetivo:

- validar rechazo de usuarios no existentes;
- comprobar respuesta SMTP;
- registrar eventos `Recipient address rejected`.

### Open relay test

Pruebas para comprobar que el servidor no actúa como relay abierto.

Objetivo:

- evitar envío no autorizado hacia dominios externos;
- validar respuesta `Relay access denied`;
- documentar bloqueo SMTP.

### STARTTLS SMTP

Validaciones de negociación STARTTLS en SMTP.

Objetivo:

- comprobar soporte TLS;
- validar cipher negociado;
- documentar transporte seguro.

### TLS IMAPS

Validaciones TLS contra IMAPS.

Objetivo:

- comprobar conexión segura en IMAPS;
- validar cipher TLS;
- documentar transporte seguro.

### SPF fail

Pruebas relacionadas con fallos SPF.

Objetivo:

- validar origen no autorizado;
- comprobar efecto sobre autenticación de dominio;
- registrar evidencia técnica.

### DKIM broken

Pruebas con firma DKIM inválida o rota.

Objetivo:

- validar detección de alteración o fallo criptográfico;
- comprobar comportamiento defensivo;
- documentar evidencia técnica.

### DKIM absent

Pruebas con ausencia de firma DKIM.

Objetivo:

- validar escenarios sin firma;
- comprobar impacto sobre autenticación de correo;
- documentar evidencia.

### DKIM rotation

Validación de rotación de selector DKIM.

Objetivo:

- confirmar publicación de nuevo selector;
- comprobar continuidad de firma;
- documentar cambio seguro.

### Lookalike domain

Pruebas con dominios visualmente parecidos.

Objetivo:

- identificar riesgo de typosquatting;
- evaluar dominios similares;
- documentar señales de posible suplantación.

### Spoofing reject

Pruebas externas de spoofing rechazadas por DMARC.

Objetivo:

- validar política DMARC `p=reject`;
- registrar `milter-reject`;
- documentar rechazo real por OpenDMARC/Postfix.

## Criterio de inclusión

Una prueba solo se incorporó al CSV SOC cuando existía evidencia verificable:

- respuesta SMTP;
- transcript técnico;
- registro syslog;
- validación TLS;
- consulta DNS;
- OpenDMARC/OpenDKIM;
- milter-reject;
- evidencia de rechazo o bloqueo.

## Conclusión

Las pruebas SOC demuestran la capacidad del laboratorio para validar controles defensivos, registrar eventos reales y visualizar resultados en un dashboard orientado a Blue Team.
``

