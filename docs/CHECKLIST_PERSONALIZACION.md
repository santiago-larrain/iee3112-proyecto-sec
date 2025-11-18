# Checklist de Personalización y Configuración

## 🔐 Información de Acceso y Credenciales

### Scraping de Distribuidoras

Para cada distribuidora que se quiera implementar, necesitas:

#### Enel Distribución
- [ ] URL de login actualizada
- [ ] Estructura HTML del portal (selectores CSS/XPath)
- [ ] Método de autenticación (usuario/password, RUT, etc.)
- [ ] Ubicación de boletas en el portal
- [ ] Formato de descarga (PDF, HTML, ambos)
- [ ] Detección de CAPTCHA y método de resolución
- [ ] Rate limiting y políticas anti-bot

#### CGE (Chilectra)
- [ ] URL de login
- [ ] Estructura del portal
- [ ] Método de autenticación
- [ ] Ubicación de boletas
- [ ] Formato de descarga

#### Saesa
- [ ] URL de login
- [ ] Estructura del portal
- [ ] Método de autenticación
- [ ] Ubicación de boletas
- [ ] Formato de descarga

#### Otras Distribuidoras
- [ ] Lista completa de distribuidoras a soportar
- [ ] Prioridad de implementación

### PESEC (Plataforma SEC)

- [ ] ¿Hay API disponible para PESEC?
- [ ] Credenciales de acceso (si aplica)
- [ ] Formato de datos que maneja
- [ ] Endpoints disponibles
- [ ] Documentación de API
- [ ] Rate limiting y cuotas

### STAR (Proceso de Información Regulatoria)

- [ ] ¿Cómo se accede a los datos STAR?
- [ ] Formato de datos
- [ ] Frecuencia de actualización
- [ ] Credenciales necesarias

## 📋 Información Normativa y Procedimientos

### Consultas con SEC

#### Manual de Reclamos 2025
- [ ] Confirmar interpretación de procedimientos
- [ ] Clarificar casos ambiguos
- [ ] Validar reglas de negocio implementadas
- [ ] Confirmar medios probatorios requeridos por tipología

#### Resolución 1952 (CNR)
- [ ] Validar cálculo de CIM (Consumo Índice Mensual)
- [ ] Confirmar períodos máximos (12 meses vs 3 meses)
- [ ] Validar medios de prueba aceptados
- [ ] Clarificar casos especiales

#### Plazos y Cumplimiento
- [ ] Confirmar plazos exactos (30 días, ¿hábiles o corridos?)
- [ ] Validar criterios de cumplimiento
- [ ] Confirmar cómo se calculan días transcurridos
- [ ] Validar excepciones a plazos

#### Medios Probatorios
- [ ] Lista completa y actualizada por tipología
- [ ] Formatos aceptados (PDF, imágenes, etc.)
- [ ] Requisitos de calidad/resolución
- [ ] Validación de medios probatorios

## 🔧 Configuración Técnica

### URLs y Endpoints

- [ ] URLs actuales de portales de distribuidoras
- [ ] URLs de APIs (si existen)
- [ ] Endpoints de PESEC
- [ ] URLs de documentación

### Estructura de Datos

#### Boletas
- [ ] Formato exacto de boletas por distribuidora
- [ ] Campos obligatorios vs opcionales
- [ ] Formatos de fecha/hora
- [ ] Formatos de montos (separadores decimales)
- [ ] Códigos de estado de pago

#### Reclamos
- [ ] Formato de entrada de reclamos
- [ ] Campos requeridos
- [ ] Validaciones necesarias
- [ ] Integración con sistemas SEC

### Base de Datos

- [ ] ¿SQLite es suficiente o se necesita PostgreSQL?
- [ ] Esquema de base de datos final
- [ ] Índices necesarios para performance
- [ ] Políticas de backup
- [ ] Retención de datos

## 🎯 Reglas de Negocio Específicas

### Facturación Excesiva
- [ ] Confirmar umbral de 2x período espejo
- [ ] Validar cálculo de período espejo (mes anterior, mismo mes, mes posterior)
- [ ] Confirmar límite máximo según potencia
- [ ] Validar árbol de decisión completo

### Facturación Provisoria
- [ ] Confirmar límite de 3x promedio mensual
- [ ] Validar detección de "lecturas inventadas"
- [ ] Confirmar requisitos de fotografías
- [ ] Validar cálculo de cuotas

### CNR
- [ ] Validar cálculo de CIM con diferentes escenarios
- [ ] Confirmar reglas de períodos máximos
- [ ] Validar medios de prueba específicos
- [ ] Confirmar casos especiales (ocupación < 3 meses)

### Cobros Indebidos
- [ ] Validar clasificación de categorías
- [ ] Confirmar requisitos de solicitud previa
- [ ] Validar reglas de interpelación para intereses
- [ ] Confirmar lista de servicios asociados actualizada

## 📊 Datos de Prueba y Validación

### Datos de Prueba Necesarios

- [ ] Reclamos reales anonimizados (mínimo 10 por tipología)
- [ ] Boletas reales anonimizadas (últimos 24 meses)
- [ ] Casos edge documentados
- [ ] Resultados esperados para validación

### Validación con SEC

- [ ] Obtener aprobación para usar datos anonimizados
- [ ] Validar resultados con analistas SEC
- [ ] Ajustar según feedback
- [ ] Documentar discrepancias y resoluciones

## 🔄 Integración y Automatización

### Flujo de Trabajo

- [ ] ¿Cómo se reciben los reclamos? (API, archivo, manual)
- [ ] ¿Cómo se entregan los resultados? (API, archivo, PESEC)
- [ ] Frecuencia de procesamiento (tiempo real, batch, diario)
- [ ] Notificaciones y alertas necesarias

### Automatización

- [ ] Programación de scraping (¿diario, semanal?)
- [ ] Procesamiento automático de reclamos
- [ ] Generación automática de reportes
- [ ] Alertas de incumplimiento

## 🛡️ Seguridad y Privacidad

- [ ] Manejo seguro de credenciales
- [ ] Encriptación de datos sensibles
- [ ] Cumplimiento con protección de datos
- [ ] Auditoría y logging de accesos
- [ ] Políticas de retención de datos

## 📈 Monitoreo y Métricas

- [ ] Métricas a monitorear (tiempo de procesamiento, tasa de éxito, etc.)
- [ ] Dashboard o reportes necesarios
- [ ] Alertas de errores
- [ ] Logs estructurados

## 🧪 Testing

- [ ] Ambiente de pruebas configurado
- [ ] Datos de prueba preparados
- [ ] Casos de prueba documentados
- [ ] Validación con usuarios finales

## 📝 Documentación

- [ ] Manual de usuario actualizado
- [ ] Documentación técnica completa
- [ ] Guías de instalación y configuración
- [ ] Documentación de APIs (si aplica)
- [ ] Runbook de operación

