"""Unit and assertion tests for the architectural design document (DESIGN.md).

Validates document existence, markdown structure, Spanish linguistic compliance,
algorithmic efficiency explanations (O(1) vs O(N)), concurrency / TOCTOU analysis,
and atomic state mutation ordering.
"""

from pathlib import Path
import re
import pytest

DOC_PATH = Path(__file__).resolve().parents[2] / "DESIGN.md"


@pytest.fixture(scope="module")
def design_doc_text() -> str:
    """Reads DESIGN.md from repository root."""
    assert DOC_PATH.exists(), f"Expected {DOC_PATH} to exist at repository root."
    return DOC_PATH.read_text(encoding="utf-8")


def test_design_document_exists():
    """Verify that DESIGN.md exists at repository root."""
    assert DOC_PATH.exists()
    assert DOC_PATH.is_file()


def test_mandatory_headers_structure(design_doc_text: str):
    """Verify that all mandatory section and subsection headers defined in the contract are present."""
    required_headers = [
        "# Notas de Diseño Arquitectónico: Sistema de Colas de Sucursal (`BranchQueueManager`)",
        "## 1. Eficiencia Algorítmica: Cola por Servicio vs. Cola Única Compartida",
        "### 1.1 Contexto y Modelado de Datos",
        "### 1.2 Análisis de Complejidad Temporal: O(1) vs. O(N)",
        "### 1.3 Eliminación de Elementos y Sobrecarga de Filtrado",
        "### 1.4 Granularidad de Bloqueos y Contención (Lock Contention)",
        "## 2. Concurrencia y Sincronización en `call_next`",
        "### 2.1 Escenario de Colisión Concurrente (Dos Agentes en Paralelo)",
        "### 2.2 Anatomía de la Condición de Carrera: Check-Then-Act (TOCTOU)",
        "### 2.3 Visualización del Fallo de Concurrencia",
        "## 3. Orden Crítico de Mutación de Estado",
        "### 3.1 Respuesta a la Pregunta Central: Mutación Mandatoria Inicial",
        "### 3.2 Justificación de la Extracción Atómica (`popleft`) dentro de la Sección Crítica",
        "### 3.3 Comportamiento en Casos Borde (Cliente Único, Cola Vacía, Falla del Agente)",
        "## 4. Alineación con los Principios de la Constitución",
        "### 4.1 Principio II: Despacho Justo FIFO",
        "### 4.2 Principio IV: Desacoplamiento de Agentes y Ventanillas",
        "### 4.3 Principio V: Estructuras de Datos Canónicas en Python",
    ]

    for header in required_headers:
        assert header in design_doc_text, f"Missing required header: {header}"


def test_architectural_references_and_entities(design_doc_text: str):
    """Verify core domain entities and architectural terms are referenced in DESIGN.md."""
    core_terms = [
        "BranchQueueManager",
        "ServiceType",
        "Banco Meridional",
        "Constitución",
        "deposit",
        "withdrawal",
        "account_management",
    ]
    for term in core_terms:
        assert term in design_doc_text, f"Missing core architectural term: {term}"


def test_user_story_1_algorithmic_efficiency(design_doc_text: str):
    """US1: Verify presence of O(1) vs O(N) complexity analysis, data modeling, removal overhead, and lock contention."""
    # Big-O complexity assertions
    assert "O(1)" in design_doc_text, "Missing O(1) complexity notation."
    assert "O(N)" in design_doc_text, "Missing O(N) complexity notation."

    # Section 1.1 & 1.2 content checks
    sec1_match = re.search(
        r"## 1\. Eficiencia Algorítmica:.*?(?=## 2\. Concurrencia|$)",
        design_doc_text,
        re.DOTALL,
    )
    assert sec1_match, "Section 1 not found."
    sec1_text = sec1_match.group(0)

    # Data modeling and complexity assertions
    assert "deque" in sec1_text, "Section 1 must reference collections.deque."
    assert "popleft" in sec1_text, "Section 1 must reference popleft operation."
    assert re.search(r"cola.*(única|compartida)", sec1_text, re.I), (
        "Section 1 must analyze a single shared queue alternative."
    )
    assert re.search(r"búsqueda|escaneo|recorrido", sec1_text, re.I), (
        "Section 1 must explain linear scanning / searching overhead."
    )

    # Section 1.3 & 1.4 removal overhead and lock contention
    assert re.search(r"(desplazamiento|shifting|eliminación)", sec1_text, re.I), (
        "Section 1.3 must discuss element removal / shifting overhead."
    )
    assert re.search(r"(contención|particionamiento|bloqueo|lock)", sec1_text, re.I), (
        "Section 1.4 must discuss lock contention and granular concurrency."
    )


def test_user_story_2_concurrency_and_state_mutation(design_doc_text: str):
    """US2: Verify concurrency collision, Check-Then-Act TOCTOU race condition, and atomic popleft state mutation ordering."""
    # Section 2 extraction & verification
    sec2_match = re.search(
        r"## 2\. Concurrencia y Sincronización.*?(?=## 3\. Orden Crítico|$)",
        design_doc_text,
        re.DOTALL,
    )
    assert sec2_match, "Section 2 not found."
    sec2_text = sec2_match.group(0)

    # Concurrency collision and race condition checks
    assert re.search(r"(dos agentes|dos ventanillas|agente a.*agente b)", sec2_text, re.I), (
        "Section 2 must explain simultaneous call_next by two agents."
    )
    assert re.search(r"(Check-Then-Act|TOCTOU|condición de carrera)", sec2_text, re.I), (
        "Section 2 must diagnose Check-Then-Act (TOCTOU) race condition."
    )
    assert re.search(r"```(text|mermaid)?.*?```", sec2_text, re.DOTALL), (
        "Section 2 must include a timeline or diagram showing concurrency failure/flow."
    )

    # Section 3 extraction & verification
    sec3_match = re.search(
        r"## 3\. Orden Crítico de Mutación de Estado.*?(?=## 4\. Alineación|$)",
        design_doc_text,
        re.DOTALL,
    )
    assert sec3_match, "Section 3 not found."
    sec3_text = sec3_match.group(0)

    # Central question and mandatory first mutation answer
    assert re.search(
        r"¿qué mutación de estado debe ocurrir primero.*?\?",
        sec3_text,
        re.I,
    ), "Section 3 must formulate the exact central state mutation question."

    assert re.search(
        r"(extracción atómica|popleft|desencolado|eliminación.*cola)",
        sec3_text,
        re.I,
    ), "Section 3 must designate atomic extraction (popleft) as the mandatory first mutation."
    assert re.search(r"(exclusión mutua|sección crítica|lock)", sec3_text, re.I), (
        "Section 3 must specify execution within mutual exclusion critical section."
    )

    # Edge cases in Section 3.3
    assert re.search(r"cliente único|un solo cliente", sec3_text, re.I), (
        "Section 3.3 must cover single client in queue edge case."
    )
    assert re.search(r"cola vacía|EmptyQueueError", sec3_text, re.I), (
        "Section 3.3 must cover empty queue edge case."
    )
    assert re.search(r"falla del agente|desconexión|caída", sec3_text, re.I), (
        "Section 3.3 must cover agent crash/failure edge case."
    )


def test_user_story_3_spanish_compliance_and_constitution(design_doc_text: str):
    """US3: Verify full Spanish language compliance, absence of English prose, and Constitution alignment in Section 4."""
    # Section 4 extraction & verification
    sec4_match = re.search(
        r"## 4\. Alineación con los Principios de la Constitución.*",
        design_doc_text,
        re.DOTALL,
    )
    assert sec4_match, "Section 4 not found."
    sec4_text = sec4_match.group(0)

    # Principle II: Fair Service Dispatch FIFO
    assert re.search(r"Principio II.*?Despacho Justo FIFO", sec4_text, re.I), (
        "Section 4.1 must reference Principle II: Despacho Justo FIFO."
    )
    # Principle IV: Independent Agent & Counter Decoupling
    assert re.search(r"Principio IV.*?Desacoplamiento de Agentes", sec4_text, re.I), (
        "Section 4.2 must reference Principle IV: Desacoplamiento de Agentes."
    )
    # Principle V: Idiomatic Python & Clean Domain Data Structures
    assert re.search(r"Principio V.*?Estructuras de Datos Canónicas", sec4_text, re.I), (
        "Section 4.3 must reference Principle V: Estructuras de Datos Canónicas en Python."
    )

    # Content length and depth check for Section 4
    assert len(sec4_text.strip()) > 500, (
        "Section 4 must contain complete technical analysis prose, not just empty headers."
    )
    assert re.search(r"invariante|inanición|starvation|autónom|portabilidad", sec4_text, re.I), (
        "Section 4 must provide comprehensive discussion of constitutional principles."
    )


    # Spanish language keywords throughout the document
    spanish_keywords = [
        "eficiencia",
        "complejidad",
        "concurrencia",
        "mutación",
        "servicio",
        "bloqueo",
        "atómica",
        "despacho",
        "garantiza",
    ]
    for kw in spanish_keywords:
        assert re.search(rf"\b{kw}\b", design_doc_text, re.I), (
            f"Expected Spanish keyword '{kw}' in DESIGN.md"
        )

    # Forbidden English narrative phrases (excluding standard technical code tokens in backticks)
    forbidden_english_phrases = [
        r"\bIn this document\b",
        r"\bAs we can see\b",
        r"\bThe following table shows\b",
        r"\bThis means that\b",
        r"\bWe must consider\b",
        r"\bIt is important to note that\b",
    ]
    for pattern in forbidden_english_phrases:
        assert not re.search(pattern, design_doc_text, re.I), (
            f"Detected English narrative pattern '{pattern}' in DESIGN.md"
        )




