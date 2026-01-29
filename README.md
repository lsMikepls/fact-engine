
# High-Fidelity Fact Adjudication Engine

A verification system that extracts and rigorously validates claims from unstructured text using orthogonal evidence sources. Solves the "Stochastic Parrot" problem by forcing independent cross-examination across multiple data modalities.

## Core Principle: Orthogonal Evidence Topology

Facts are trusted only when independent sources with different error modes agree:
- **Dynamic Web** (news, press releases)
- **Static DB** (knowledge graphs, APIs)
- **Semantic LLM** (logical consistency, domain knowledge)

## Architecture: 5 Agent System

### 1. Leader & Planner (Fact Decomposer)
Breaks unstructured claims into atomic, verifiable units.
- **Input:** "Tesla's Q3 revenue grew by 5%"
- **Output:** `{Entity: Tesla, Attribute: Q3 Revenue, Value: +5%}`

### 2. Internet Search Agent (Unstructured Verifier)
Validates against dynamic corpora (news, policy changes, sentiment).

### 3. Database Query Agent (Structured Verifier)
Queries authoritative sources (Bloomberg, PubMed, court records, standards).

### 4. LLM Query Agent (Semantic Verifier)
Checks logical consistency, terminology alignment, and causal plausibility.

### 5. Reasoner & Synthesizer (Adjudicator)
Aggregates evidence streams with source-aware confidence scoring.

## Adjudication Logic

- **All agree** → High confidence
- **DB ≠ Web** (numbers) → Trust DB
- **LLM ≠ Web** (news) → Trust Web
- **Conflicts** → Calibrated confidence with source hierarchy

## Workflow

1. **Extract** atomic claims
2. **Triangulate** across three evidence sources
3. **Adjudicate** with weighted verdict
