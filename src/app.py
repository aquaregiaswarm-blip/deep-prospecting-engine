"""Streamlit UI for the Deep Prospecting Engine."""

import streamlit as st
import logging
from pathlib import Path

from src.graph.workflow import run_prospecting
from src.prompts.base_research import DEFAULT_BASE_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Deep Prospecting Engine",
    page_icon="🜆",
    layout="wide",
)

st.title("🜆 The Deep Prospecting Engine")
st.caption("AI-powered sales intelligence by Pellera")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.info("Ensure your `.env` file contains `GEMINI_API_KEY`")

    output_dir = st.text_input("Output Directory", value="./output")

# Main form
with st.form("prospecting_form"):
    col1, col2 = st.columns(2)

    with col1:
        client_name = st.text_input(
            "🏢 Client Name",
            placeholder="e.g., Acme Corporation",
            help="The target client to research",
        )

    with col2:
        st.empty()  # Placeholder for future fields

    past_sales_history = st.text_area(
        "📋 Past Sales History",
        placeholder="e.g., 2023: Sold 500 Cloud Storage licenses. 2024: Sold 200 Compute instances...",
        height=150,
        help="Any prior sales history or relationship context",
    )

    # Editable research prompt
    with st.expander("🔬 Customize Research Prompt", expanded=False):
        default_prompt = DEFAULT_BASE_PROMPT.format(
            client_name=client_name or "[Client Name]",
            additional_focus="",
        )
        base_prompt = st.text_area(
            "Base Research Prompt",
            value=default_prompt,
            height=200,
            help="Modify this to steer the research (e.g., 'Focus on supply chain')",
        )

    submitted = st.form_submit_button("🚀 Run Deep Prospecting", type="primary")

# Execution
if submitted:
    if not client_name:
        st.error("❌ Client name is required.")
    else:
        # Progress tracking
        progress = st.progress(0, text="Initializing...")
        status = st.status("Running Deep Prospecting Engine...", expanded=True)

        try:
            with status:
                st.write("📥 Processing input...")
                progress.progress(10, text="Processing input...")

                st.write("🔍 Running deep research with Gemini...")
                progress.progress(20, text="Deep research in progress...")

                # Run the full pipeline
                result = run_prospecting(
                    client_name=client_name,
                    past_sales_history=past_sales_history,
                    base_research_prompt=base_prompt,
                )

                progress.progress(100, text="Complete!")

            # Display results
            if result.errors:
                for error in result.errors:
                    st.warning(f"⚠️ {error}")

            # Client profile
            st.header(f"📊 {result.client_name}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Vertical", result.client_vertical)
            with col2:
                st.metric("Domain", result.client_domain)
            with col3:
                st.metric("Plays Generated", len(result.refined_plays))

            # Deep Research Report
            with st.expander("🔬 Deep Research Report", expanded=False):
                st.markdown(result.deep_research_report)

            # Competitor Analysis
            if result.competitor_proofs:
                with st.expander("🏁 Competitor Analysis", expanded=False):
                    for proof in result.competitor_proofs:
                        st.markdown(
                            f"**{proof['competitor_name']}**: {proof['use_case']} → {proof['outcome']}"
                        )

            # Sales Plays
            if result.refined_plays:
                st.header("🎯 Top Sales Plays")
                for i, play in enumerate(result.refined_plays, 1):
                    with st.expander(f"Play {i}: {play['title']}", expanded=(i == 1)):
                        st.markdown(f"**Challenge:** {play['challenge']}")
                        st.markdown(f"**Solution:** {play['proposed_solution']}")
                        st.markdown(f"**Outcome:** {play['business_outcome']}")
                        if play.get("technical_stack"):
                            st.markdown(f"**Stack:** {', '.join(play['technical_stack'])}")
                        st.progress(
                            play.get("confidence_score", 0.5),
                            text=f"Confidence: {play.get('confidence_score', 0.5):.0%}",
                        )

            # One-pagers
            if result.one_pagers:
                st.header("📄 Generated One-Pagers")
                for title, content in result.one_pagers.items():
                    with st.expander(f"📄 {title}"):
                        st.markdown(content)
                        st.download_button(
                            f"⬇️ Download {title}",
                            content,
                            file_name=f"{title.lower().replace(' ', '_')}_one_pager.md",
                            mime="text/markdown",
                        )

            # Strategic Plan
            if result.strategic_plan:
                st.header("📋 Strategic Account Plan")
                with st.expander("View Full Plan", expanded=False):
                    st.markdown(result.strategic_plan)
                st.download_button(
                    "⬇️ Download Strategic Plan",
                    result.strategic_plan,
                    file_name=f"{client_name.lower().replace(' ', '_')}_strategic_plan.md",
                    mime="text/markdown",
                )

        except Exception as e:
            st.error(f"❌ Pipeline failed: {str(e)}")
            logger.exception("Pipeline error")
