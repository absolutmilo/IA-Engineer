# Logging Guide - AI Engineering Guardian

## 📋 Logging Overview

The **AI Engineering Guardian** features comprehensive structured logging that provides complete visibility into the audit process, LLM interactions, and system performance. All logs are saved in both human-readable and machine-parseable formats.

## 📁 Log Files Location

Log files are automatically created in the `logs/` directory with timestamped names:

- **Plain Text Log**: `logs/audit_YYYYMMDD_HHMMSS.log`
  - Human-readable format with timestamps and structured information
  - Includes thread information, function context, and line numbers
  - Optimized for console viewing and quick debugging

- **JSON Log**: `logs/audit_YYYYMMDD_HHMMSS.jsonl`
  - One JSON object per line for easy parsing
  - Complete context including thread, function, line, and exception details
  - Ideal for automated analysis and log aggregation systems

## 🔍 How to View Logs

### Option 1: Real-time Monitoring (Plain Text)
```bash
# PowerShell (recommended)
Get-Content -Path logs/audit_*.log -Wait

# Linux/macOS with tail
tail -f logs/audit_*.log

# Filter for specific patterns
Get-Content logs/audit_*.log | Select-String "ERROR|TIMEOUT"
```

### Option 2: Historical Analysis
```bash
# View most recent log entries
Get-Content -Path logs/audit_*.log -Tail 100

# Open log file directly in editor
code logs/audit_*.log

# Search for specific events
Select-String -Path logs/audit_*.log -Pattern "SECTION.*TIMEOUT"
```

### Option 3: JSON Log Analysis
```bash
# Using jq for JSON analysis
Get-Content logs/audit_*.jsonl | ConvertFrom-Json | Where-Object { $_.level -eq "ERROR" }

# Python for complex filtering
python -c "
import json
with open('logs/audit_*.jsonl') as f:
    for line in f:
        event = json.loads(line)
        if 'TIMEOUT' in event.get('message', ''):
            print(f'{event[\"timestamp\"]}: {event[\"message\"]}')
"
```

## 📊 Log Levels

- **DEBUG**: Detailed information for troubleshooting and development
  - Function entry/exit points
  - Variable values and state changes
  - Detailed error traces

- **INFO**: Important events and milestones
  - Section start/completion
  - Performance metrics and timing
  - Configuration and initialization

- **WARNING**: Non-critical issues and fallbacks
  - Timeouts and retries
  - Fallback mechanisms
  - Performance concerns

- **ERROR**: Critical failures and exceptions
  - Analysis failures
  - LLM connection issues
  - System errors

## 🎯 Key Log Patterns

### 1. **Detecting Timeouts and Blockages**
```
[SECTION] Starting: <section_name>
[SECTION] Waiting for result (timeout: 120s)...
[SECTION] '<section_name>' TIMEOUT after 120s
[SECTION] Using fallback response for section
```

### 2. **LLM Interaction Tracking**
```
[SECTION] Prompt for '<section_name>':
  Prompt length: XXXX characters
  First 300 chars: <prompt_preview>...
[WORKER] Called ollama.chat() with retry...
[WORKER] SUCCESS '<section_name>': Got response (XXXX chars) in X.Xs
```

### 3. **Performance Monitoring**
```
[worker] Section 'architecture' completed in 2.3s (response: 512 bytes)
AUDIT ANALYSIS COMPLETE in 15.2s
Final Grade: B | Enterprise Readiness: 65%
```

### 4. **Error Handling and Recovery**
```
[SECTION] '<section_name>' TIMEOUT after 120s
[SECTION] Worker thread still running; will be terminated as daemon
[SECTION] Using fallback response for section
[Parsing section '<section_name>'...]
  Verdict: <verdict>
  Findings: <count>
  Recommendations: <count>
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
python scripts/standalone/main.py <project_path> --debug
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
2026-02-20 10:16:05 ERROR    [SECTION] 'llm_integration' TIMEOUT after 120s
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
