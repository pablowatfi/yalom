from langchain_core.messages import HumanMessage, AIMessage

from src.rag.pipeline import RAGPipeline


def test_get_conversation_history_formats_roles():
    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.chat_history = [
        HumanMessage(content="hi"),
        AIMessage(content="hello"),
    ]

    history = pipeline.get_conversation_history()

    assert history == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_reset_conversation_clears_history():
    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.chat_history = [HumanMessage(content="hi")]

    pipeline.reset_conversation()

    assert pipeline.chat_history == []
