"""Base research prompts for Gemini Deep Research."""

DEFAULT_BASE_PROMPT = """You are a senior technology analyst conducting deep research on {client_name}.

Produce a comprehensive report covering:

1. **Company Overview**: Industry, size, key products/services, recent news
2. **Digital Maturity Assessment**: Current technology stack, cloud adoption, data infrastructure
3. **AI/ML Footprint**: Any existing AI initiatives, published case studies, job postings mentioning AI/ML
4. **Strategic Goals**: Publicly stated digital transformation goals, earnings call insights, press releases
5. **Technology Partnerships**: Current vendors, cloud providers, consulting relationships
6. **Pain Points & Opportunities**: Areas where AI/ML could drive significant value

For every claim, provide the source URL.

{additional_focus}
"""

VERTICAL_CLASSIFICATION_PROMPT = """Based on the following research report, classify the client into:

1. **Vertical**: The primary industry vertical (e.g., Healthcare, Financial Services, Manufacturing, Retail, etc.)
2. **Domain**: The specific sub-domain (e.g., Commercial Banking, Specialty Pharma, Discrete Manufacturing, etc.)
3. **Digital Maturity Level**: Rate 1-5 (1=Legacy, 2=Emerging, 3=Developing, 4=Advanced, 5=Leading)

Research Report:
{report}

Respond in JSON format:
{{"vertical": "...", "domain": "...", "maturity_level": N, "maturity_summary": "..."}}
"""

HISTORY_SYNTHESIS_PROMPT = """You are analyzing a client's past sales history to identify technical gaps and opportunities.

Client: {client_name}
Vertical: {vertical}

Past Sales History:
{sales_history}

Identify:
1. **What they bought**: List all products/services purchased
2. **Technical gaps**: What's missing from their stack? (e.g., "Bought storage but no compute → ML modernization play")
3. **Maturity indicators**: What does their buying pattern tell us about their technical sophistication?
4. **Upsell opportunities**: Natural next steps based on what they already have

Be specific and actionable. Think like a solutions architect who needs to find the next deal.
"""
