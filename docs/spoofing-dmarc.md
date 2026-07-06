# Spoofing y DMARC

## Resumen

Dentro del laboratorio PhisDefense se realizaron pruebas controladas de spoofing para validar la política DMARC del dominio.

El objetivo fue comprobar que mensajes externos que intentaban usar identidad del dominio phisdefense.com fueran rechazados por la política DMARC configurada en modo p=reject.

## Objetivo técnico

Validar que el dominio estaba protegido frente a intentos de suplantación mediante:

- SPF
- DKIM
- DMARC
- OpenDMARC
- Postfix
- evidencias en syslog

## Política DMARC

El proyecto aplicó una política DMARC progresiva hasta llegar a:

```text
p=reject
```

Esto permite rechazar mensajes que no superen las comprobaciones de autenticación y alineación de dominio.

## Pruebas externas

Se realizaron pruebas desde servicios externos de envío para simular mensajes que intentaban usar identidad del dominio.

El objetivo no era entregar el mensaje, sino verificar que el servidor lo rechazaba correctamente.

## Evidencia esperada

Una prueba se consideró válida cuando aparecían evidencias como:

```text
milter-reject
5.7.1 rejected by DMARC policy for phisdefense.com
```

## Resultado

El servidor registró eventos de rechazo DMARC reales mediante Postfix y OpenDMARC.

Estos eventos quedaron clasificados en el CSV SOC como:

```text
spoofing_reject
```

## Ejemplo de evidencia sanitizada

```text
postfix/cleanup: milter-reject: END-OF-MESSAGE from unknown[[IP_REDACTED]]:
5.7.1 rejected by DMARC policy for phisdefense.com;
to=<dmarc@phisdefense.com>
```

## Conclusión

Las pruebas demostraron que la política DMARC configurada en el dominio era capaz de rechazar intentos externos de spoofing.

Este caso sirve como evidencia defensiva dentro del portfolio, ya que combina:

- configuración de controles de correo;
- validación real;
- análisis de logs;
- clasificación SOC;
- documentación de evidencias.

