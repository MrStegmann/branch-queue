# Quickstart Validation Guide: Design Notes (`DESIGN.md`)

**Feature Branch**: `002-design-notes`  
**Date**: 2026-11-08  
**Target Document**: `./DESIGN.md`  

---

## 1. Overview

This guide provides runnable verification commands and inspection checklists to validate that `DESIGN.md` meets all functional requirements and acceptance criteria defined in [spec.md](spec.md) and [contracts/design-document-contract.md](contracts/design-document-contract.md).

---

## 2. Prerequisites

- Python 3.11+ installed and accessible in the system path.
- Existing repository cloned and on branch `002-design-notes`.
- Root document `./DESIGN.md` created.

---

## 3. Verification Scenarios

### Scenario 1: File Existence and Location

**Command (PowerShell)**:
```powershell
Test-Path -Path "DESIGN.md"
```

**Expected Outcome**:
`True` — Confirms that `DESIGN.md` resides directly at the project root.

---

### Scenario 2: Full Spanish Language Verification

**Command (PowerShell)**:
```powershell
# Check for common Spanish language keywords that must appear in the design note
$keywords = @("eficiencia", "cola", "concurrencia", "mutación", "servicio", "bloqueo", "atómica")
$content = Get-Content -Raw -Path "DESIGN.md"
$missing = $keywords | Where-Object { $content -notmatch $_ }
if ($missing.Count -eq 0) { Write-Output "PASS: Spanish keywords validated." } else { Write-Error "FAIL: Missing keywords: $missing" }
```

**Expected Outcome**:
`PASS: Spanish keywords validated.`

---

### Scenario 3: Algorithmic Efficiency Assertions

**Command (PowerShell)**:
```powershell
$content = Get-Content -Raw -Path "DESIGN.md"
$hasO1 = $content -match "O\(1\)"
$hasON = $content -match "O\(N\)"
$hasComparison = $content -match "(compartida|única)" -and $content -match "(independiente|separada|por servicio)"

if ($hasO1 -and $hasON -and $hasComparison) {
    Write-Output "PASS: Algorithmic complexity comparison (O(1) vs O(N)) present."
} else {
    Write-Error "FAIL: Missing complexity comparison."
}
```

**Expected Outcome**:
`PASS: Algorithmic complexity comparison (O(1) vs O(N)) present.`

---

### Scenario 4: Concurrency and Race Condition Assertions

**Command (PowerShell)**:
```powershell
$content = Get-Content -Raw -Path "DESIGN.md"
$hasRace = $content -match "(carrera|Check-Then-Act|TOCTOU|simultáne)"
$hasLock = $content -match "(lock|bloqueo|exclusión mutua|sincroniz)"

if ($hasRace -and $hasLock) {
    Write-Output "PASS: Concurrency hazard and synchronization mechanics present."
} else {
    Write-Error "FAIL: Concurrency explanation incomplete."
}
```

**Expected Outcome**:
`PASS: Concurrency hazard and synchronization mechanics present.`

---

### Scenario 5: State Mutation Order Assertion

**Command (PowerShell)**:
```powershell
$content = Get-Content -Raw -Path "DESIGN.md"
$hasMutationQuestion = $content -match "mutación" -and $content -match "(primero|inicial|inmediata)"
$hasExtraction = $content -match "(popleft|extracción|eliminación|desencolar)"

if ($hasMutationQuestion -and $hasExtraction) {
    Write-Output "PASS: State mutation ordering and atomic extraction answer present."
} else {
    Write-Error "FAIL: State mutation ordering answer incomplete."
}
```

**Expected Outcome**:
`PASS: State mutation ordering and atomic extraction answer present.`

---

## 4. Automated Verification Script

To run all checks in a single automated step:

```powershell
python -c @"
import sys, re

with open('DESIGN.md', 'r', encoding='utf-8') as f:
    text = f.read()

checks = {
    'Spanish content present': bool(re.search(r'(eficiencia|concurrencia|mutación|servicio)', text, re.I)),
    'O(1) complexity cited': 'O(1)' in text,
    'O(N) complexity cited': 'O(N)' in text,
    'call_next analyzed': 'call_next' in text,
    'Race condition described': bool(re.search(r'(carrera|simultáne|Check-Then-Act)', text, re.I)),
    'Atomic extraction identified': bool(re.search(r'(popleft|extracción atómica|desencolar)', text, re.I)),
}

failed = [desc for desc, passed in checks.items() if not passed]
if failed:
    print('FAILED checks:', failed)
    sys.exit(1)
else:
    print('ALL DESIGN.md VALIDATION CHECKS PASSED!')
"@
```

