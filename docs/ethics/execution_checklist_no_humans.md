# Checklist de ejecución ética sin sujetos humanos

## Antes de cualquier prueba
- [ ] Confirmar que no se usarán destinatarios externos.
- [ ] Confirmar que no se enviarán campañas a personas reales sin autorización.
- [ ] Verificar que el modo de ejecución sea controlado (`simulated_outbox` o SMTP a cuentas propias).
- [ ] Confirmar que el contenido del template no solicite credenciales reales.
- [ ] Confirmar que la landing page tenga carácter educativo.
- [ ] Confirmar que los datos usados son propios, sintéticos o de prueba.

## Durante la prueba
- [ ] Verificar que los correos se dirijan solo a cuentas propias o buzones de prueba.
- [ ] Registrar únicamente eventos técnicos necesarios (`delivered`, `opened`, `clicked`, `reported`).
- [ ] No capturar datos sensibles.
- [ ] No desplegar el sistema fuera del entorno académico.

## Después de la prueba
- [ ] Exportar dataset analítico.
- [ ] Generar reporte descriptivo.
- [ ] Generar reporte comparativo de modelos.
- [ ] Documentar que la prueba fue técnica y controlada.
- [ ] Dejar evidencia de que no hubo participación de terceros.