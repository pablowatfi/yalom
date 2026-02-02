#!/usr/bin/env python3
"""
Streamlit Web UI for Huberman Lab AI Assistant.

Usage:
    poetry run streamlit run app/streamlit_app.py
"""
import requests
import streamlit as st
from src.config import API_BASE_URL, RAG_TOP_K
from src.rag.safety import is_prompt_injection, is_prompt_injection_in_history


# Page config
st.set_page_config(
    page_title="Huberman Lab AI Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_rag():
    """Initialize app in API mode only."""
    if not API_BASE_URL:
        st.session_state.initialized = False
        return
    st.session_state.initialized = True


def build_api_history(messages):
    history = []
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant"} and content:
            history.append({"role": role, "content": content})
    return history


def sidebar():
    """Render sidebar with settings."""
    with st.sidebar:
        st.title("⚙️ Settings")

        # Reset button at the top
        if st.button("🔄 Reset Conversation", use_container_width=True):
            if "rag" in st.session_state:
                st.session_state.rag.reset_conversation()
            st.session_state.messages = []
            st.rerun()

        st.divider()

        st.success("🌐 **API Mode**\n\nUsing deployed API endpoint.")
        if API_BASE_URL:
            st.caption(API_BASE_URL)
        else:
            st.error("API_BASE_URL is not set. This UI requires the deployed API.")

        st.divider()

        # RAG Settings
        st.subheader("🔍 Search Settings")
        st.text(f"Top K: {RAG_TOP_K}")
        st.caption("Edit src/config.py to change")

        st.divider()

        # Stats
        if "messages" in st.session_state:
            st.caption(f"💬 Messages: {len(st.session_state.messages)}")


def main():
    """Main app."""

    # Header
    st.title("🧠 Huberman Lab AI Assistant")
    st.caption("Ask questions about Andrew Huberman's podcast episodes")

    # Sidebar
    sidebar()

    # Initialize RAG
    initialize_rag()

    if not st.session_state.get("initialized", False):
        st.error("❌ API_BASE_URL is not set. This UI requires the deployed API.")
        return

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show sources if available
            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📚 Sources", expanded=False):
                    sources = message["sources"]

                    # Group by title
                    sources_by_title = {}
                    for source in sources:
                        title = source["title"]
                        if title not in sources_by_title:
                            sources_by_title[title] = []
                        sources_by_title[title].append(source)

                    for i, (title, srcs) in enumerate(sources_by_title.items(), 1):
                        st.markdown(f"**{i}. {title}**")
                        st.caption(f"{len(srcs)} excerpt{'s' if len(srcs) > 1 else ''}")

                        # Show first excerpt preview
                        if srcs:
                            st.text(srcs[0]["content"])
                        st.divider()

    # Chat input
    if prompt := st.chat_input("Ask a question about Huberman Lab podcasts..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Guard against prompt injection
        if is_prompt_injection(prompt) or is_prompt_injection_in_history(st.session_state.messages):
            refusal = "Request rejected: prompt-injection attempt detected."
            with st.chat_message("assistant"):
                st.markdown(refusal)
            st.session_state.messages.append({
                "role": "assistant",
                "content": refusal,
                "sources": [],
            })
            return

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    history = build_api_history(st.session_state.messages)
                    response = requests.post(
                        f"{API_BASE_URL.rstrip('/')}/query",
                        json={
                            "query": prompt,
                            "top_k": RAG_TOP_K,
                            "history": history,
                        },
                        timeout=60,
                    )
                    response.raise_for_status()
                    result = response.json()

                    answer = result["answer"]
                    sources = result.get("sources", [])

                    # Display answer
                    st.markdown(answer)

                    # Display sources
                    with st.expander("📚 Sources", expanded=False):
                        if sources and "title" in sources[0]:
                            # Group by title
                            sources_by_title = {}
                            for source in sources:
                                title = source["title"]
                                if title not in sources_by_title:
                                    sources_by_title[title] = []
                                sources_by_title[title].append(source)

                            for i, (title, srcs) in enumerate(sources_by_title.items(), 1):
                                st.markdown(f"**{i}. {title}**")
                                st.caption(f"{len(srcs)} excerpt{'s' if len(srcs) > 1 else ''}")

                                # Show first excerpt preview
                                if srcs:
                                    st.text(srcs[0]["content"])
                                st.divider()
                        else:
                            for i, source in enumerate(sources, 1):
                                title = source.get("episode_name") or source.get("title") or "Unknown"
                                st.markdown(f"**{i}. {title}**")
                                st.caption(f"Score: {source.get('score', 0):.3f}")
                                preview = source.get("text_preview") or source.get("content") or ""
                                if preview:
                                    st.text(preview)
                                st.divider()

                    # Add to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })

                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
