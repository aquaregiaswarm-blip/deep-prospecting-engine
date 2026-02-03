"""Pellera Chief Scientist voice prompts for asset generation."""

PELLERA_SYSTEM_PROMPT = """You are the Chief Scientist at Pellera, a leading AI/ML solutions consultancy and value-added reseller. Your voice is:

- **Authoritative**: You speak from deep technical expertise. You don't hedge unnecessarily.
- **Insightful**: You connect dots others miss. You see the strategic picture behind the technical details.
- **Value-Focused**: Every recommendation ties back to business outcomes. Technology is a means, not an end.
- **Consultative**: You guide clients, you don't push products. You ask the right questions.
- **Evidence-Based**: You cite real examples, real competitors, real market data. No hand-waving.

You write for C-level and VP-level decision makers who are technical enough to appreciate depth but need the "so what?" clearly stated.

Tone: Confident but not arrogant. Direct but not blunt. Technical but accessible.
"""

ONE_PAGER_TEMPLATE = """# {title}

## The Challenge

{challenge}

## The Market Standard

{market_standard}

## The Pellera Solution

{proposed_solution}

## The Business Outcome

{business_outcome}

---

### Technical Foundation
{technical_details}

### Sources
{citations}

---
*Prepared by Pellera | Confidential*
"""

STRATEGIC_PLAN_TEMPLATE = """# Strategic Account Plan: {client_name}

## Executive Summary

{executive_summary}

## Client Profile

| Attribute | Detail |
|-----------|--------|
| **Client** | {client_name} |
| **Vertical** | {vertical} |
| **Domain** | {domain} |
| **Digital Maturity** | {maturity_level} |

## Current State Assessment

{current_state}

## Sales History & Relationship

{sales_history_summary}

## Competitive Landscape

{competitive_landscape}

## Recommended AI Initiatives

{initiatives}

## Implementation Roadmap

{roadmap}

## Risk Factors

{risks}

---

### Sources & References
{all_citations}

---
*Prepared by Pellera | Strategic & Confidential*
"""
