# Logging Guide - AI Auditor

## 📋 Logging Overview

El sistema de **AI Auditor** ahora tiene logging completo y estructurado que permite ver exactamente dónde se cuelga la aplicación, qué prompts se envían al modelo, y todo el flujo de ejecución.

## 📁 Log Files Location

Los archivos de log se guardan en la carpeta `logs/` con dos formatos:

- **Plain Text Log**: `logs/audit_YYYYMMDD_HHMMSS.log`
  - Formato legible para humanos
  - Incluye timestamps, niveles, función y línea
  - Información de threads

- **JSON Log**: `logs/audit_YYYYMMDD_HHMMSS.jsonl`
  - Una línea JSON por evento
  - Fácil de parsear y analizar
  - Incluye contexto completo (thread, función, línea, excepción)

## 🔍 How to View Logs

### Opción 1: Ver logs en tiempo real (Plain Text)
```bash
# En PowerShell
Get-Content -Path logs/audit_*.log -Wait

# O usar tail si tienes WSL
tail -f logs/audit_*.log
```

### Opción 2: Ver logs completos
```bash
# Ver el log más reciente
Get-Content -Path logs/audit_*.log -Tail 100  # Últimas 100 líneas

# O en PowerShell ISE - abrir el archivo directamente
code logs/audit_*.log
```

### Opción 3: Análisis JSON (jq o Python)
```bash
# Con Python para ver eventos de timeout
Get-Content logs/audit_*.jsonl | ConvertFrom-Json | Where-Object {$_.message -like "*TIMEOUT*"}
```

## 📊 Log Levels

- `DEBUG`: Información detallada para debugging
- `INFO`: Eventos importantes (inicio secciones, tiempos, etc)
- `WARNING`: Advertencias (fallbacks, timeouts)
- `ERROR`: Errores (excepciones, fallos)

## 🔎 What to Look For

### 1. **Detectar Bloqueos**
Busca en el log:
```
[SECTION] Starting: <section_key>
[SECTION] Waiting for result (timeout: 30s)...
[SECTION] '<section_key>' TIMEOUT after 30s
```

### 2. **Ver Prompts Enviados al Modelo**
```
[SECTION] Prompt for '<section_key>':
  Prompt length: XXXX characters
  First 300 chars: <prompt_preview>...
```

### 3. **Seguir Reintentos con Exponential Backoff**
```
[WORKER] Called ollama.chat() with retry...
[WORKER] SUCCESS '<section_key>': Got response (XXXX chars)
```

### 4. **Analizar Parsing y Resultados**
```
[Parsing section '<section_key>'...]
  Verdict: <verdict>
  Findings: <count>
  Recommendations: <count>
```

## 📈 Performance Metrics

El log muestra tiempos de ejecución:
```
[worker] Section 'architecture' completed in 2.3s (response: 512 bytes)
AUDIT ANALYSIS COMPLETE in 15.2s
Final Grade: D+ | Enterprise Readiness: 35%
```

## 🚀 Running with Debug Mode

Para más detalles, ejecuta con `--debug`:
```bash
python main.py <project_path> --debug
```

Esto activa:
- Logging a nivel DEBUG en la consola
- Más detalles en los archivos de log
- Context summary completo en el log

## 📜 Example Log Entries

### Inicio del Audit
```
2026-02-20 10:15:32 INFO     ╔════════════════════════════════════════════════════════════════╗
2026-02-20 10:15:32 INFO     ║          AI ENGINEERING GUARDIAN — AUDIT SYSTEM START          ║
2026-02-20 10:15:32 INFO     ╚════════════════════════════════════════════════════════════════╝
2026-02-20 10:15:32 INFO     Target project: MyProject
2026-02-20 10:15:32 INFO     Target path: /path/to/project
```

### Procesamiento de Sección
```
2026-02-20 10:15:45 INFO     [1/12] Processing: architecture
2026-02-20 10:15:45 DEBUG    [SECTION] Prompt for 'architecture':
2026-02-20 10:15:45 DEBUG      Prompt length: 2847 characters
2026-02-20 10:15:47 INFO     [WORKER] SUCCESS 'architecture': Got response (512 chars) in 2.1s
2026-02-20 10:15:47 INFO     [1/12] Section 'architecture' completed in 2.1s
```

### Fallo y Recuperación
```
2026-02-20 10:16:05 ERROR    [SECTION] 'llm_integration' TIMEOUT after 30s
2026-02-20 10:16:05 WARNING  [SECTION] Worker thread still running; will be terminated as daemon
2026-02-20 10:16:05 DEBUG    [SECTION] Using fallback response for section
```

## 🐛 Debugging Tips

### Si el proceso se cuelga:
1. Abre el log en tiempo real con `Get-Content -Wait`
2. Busca el último `[SECTION] Starting` mes reciente
3. Si ves `[SECTION] Waiting for result` sin completarse, ese es el culpable
4. Verifica el `[WORKER]` correspondiente para error details

### Si un prompt es incorrecto:
1. Busca `[SECTION] Prompt for <section_key>`
2. Lee el `First 300 chars` para ver qué se envió
3. Verifica `Response preview` para ver qué volvió del modelo

### Si hay fallos de parsing:
1. Busca `[SECTION] Using fallback response`
2. Verifica qué verdict/findings se asignaron
3. Revisa el `raw_analysis` para ver qué recibió el parser

## 🎯 Next Steps

1. **Ejecuta el audit** con logging habilitado
2. **Revisa los logs** para entender el flujo
3. **Ajusta timeouts** si ves muchos timeouts
4. **Mejora prompts** si ves parsing errors
5. **Optimize performance** si ves secciones lentas

---

**Log files are essential for production quality. Always keep them!**
