"""
RAG Pipeline - Orchestrates retrieval and LLM generation.

Flow:
1. User asks a question
2. Retrieve relevant chunks from vector DB
3. Build context from chunks
4. Send to LLM with conversation history
5. Return answer with sources
"""
import os
import logging
from typing import List, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from ..vectorization.simple_embeddings import SimpleSentenceTransformerEmbeddings
from .prompts import get_active_prompt, get_language_name
from .query_rewriter import QueryRewriter

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    RAG pipeline for question answering over Huberman Lab transcripts.

    Supports multiple LLM providers:
    - groq: Ultra-fast free inference (llama-3.1-70b, requires API key)
    - ollama: Free, runs locally (llama3.2, mistral, etc.)
    - openai: GPT models (requires API key)
    """

    def __init__(
        self,
        collection_name: str = "huberman_transcripts",
        qdrant_url: str = "http://localhost:6333",
        llm_provider: str = "groq",  # Default to free Groq API
        model_name: Optional[str] = None,  # Auto-select based on provider
        api_key: Optional[str] = None,
        top_k: int = 6,
        retrieval_multiplier: int = 3,  # Retrieve top_k × multiplier for filtering
        similarity_threshold: float = 0.5,  # Minimum similarity score (0-1)
        temperature: float = 0.7,
        verbose_sources: int = 0,  # 0=titles only, 1=full excerpts
        query_rewriting: bool = True  # Enable multi-query rewriting for better retrieval
    ):
        """
        Initialize RAG pipeline.

        Args:
            collection_name: Qdrant collection name
            qdrant_url: Qdrant server URL
            llm_provider: LLM provider - "groq" (free, fast), "ollama" (free, local) or "openai" (paid)
            model_name: Model name (auto-selected if None)
            api_key: API key for LLM provider (needed for groq/openai, reads from GROQ_YALOM_API_KEY env if None)
            top_k: Number of final chunks to return after filtering
            retrieval_multiplier: Retrieve top_k × multiplier candidates for filtering (default: 3)
            similarity_threshold: Minimum cosine similarity score 0-1 (default: 0.5)
            temperature: LLM temperature (0-1, higher = more creative)
            verbose_sources: 0=log titles only, 1=log full transcript excerpts
            query_rewriting: Enable query rewriting (generates 2-3 optimized queries)
        """
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url
        self.top_k = top_k
        self.retrieval_multiplier = retrieval_multiplier
        self.similarity_threshold = similarity_threshold
        self.verbose_sources = verbose_sources

        # Auto-select model name based on provider
        if model_name is None:
            if llm_provider == "groq":
                model_name = "llama-3.3-70b-versatile"  # Fast, free, high quality (replaces 3.1)
            elif llm_provider == "ollama":
                model_name = "llama3.2"  # Fast, good quality
            elif llm_provider == "openai":
                model_name = "gpt-4o-mini"  # Cheap and good

        self.llm_provider = llm_provider
        self.model_name = model_name

        # Initialize embeddings (FastEmbed default)
        logger.info("Initializing embeddings...")
        self.embeddings = SimpleSentenceTransformerEmbeddings()

        # Initialize Qdrant client
        logger.info(f"Connecting to Qdrant: {qdrant_url}")
        self.qdrant_client = QdrantClient(url=qdrant_url)

        # Create vector store retriever
        # Retrieve more candidates than needed for filtering
        retrieval_k = top_k * retrieval_multiplier
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=collection_name,
            embedding=self.embeddings
        )
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": retrieval_k, "score_threshold": 0.0}  # Get all candidates, filter later
        )

        logger.info(f"Retrieval strategy: fetch {retrieval_k} candidates, filter by threshold {similarity_threshold}, return top {top_k}")

        # Initialize LLM based on provider
        logger.info(f"Initializing LLM: {llm_provider}/{model_name}")

        if llm_provider == "groq":
            # Groq - ultra-fast free inference
            if not api_key:
                api_key = os.getenv("GROQ_YALOM_API_KEY")
            if not api_key:
                raise ValueError("Groq requires api_key parameter or GROQ_YALOM_API_KEY environment variable")
            self.llm = ChatGroq(
                model=model_name,
                temperature=temperature,
                api_key=api_key
            )
            logger.info(f"Using Groq (free, ultra-fast): {model_name}")

        elif llm_provider == "ollama":
            # Free local LLM
            self.llm = ChatOllama(
                model=model_name,
                temperature=temperature,
                base_url="http://localhost:11434"  # Default Ollama port
            )
            logger.info(f"Using Ollama (free, local): {model_name}")

        elif llm_provider == "openai":
            # OpenAI API
            if not api_key:
                raise ValueError("OpenAI requires api_key parameter")
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=api_key
            )
            logger.info(f"Using OpenAI: {model_name}")

        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}. Use 'groq', 'ollama' or 'openai'")

        # Initialize query rewriter (uses same LLM)
        self.query_rewriter = QueryRewriter(llm=self.llm, enabled=query_rewriting)
        if query_rewriting:
            logger.info("Query rewriting enabled (multi-query retrieval)")

        # Store conversation history manually
        self.chat_history: List[HumanMessage | AIMessage] = []

        # Load prompt template from versioned prompts
        prompt_data = get_active_prompt()
        self.prompt_version = prompt_data["version"]
        logger.info(f"Using prompt version: {self.prompt_version}")

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system"]),
            ("human", prompt_data["human"])
        ])

        logger.info("RAG pipeline initialized successfully")

    def ask(self, question: str) -> Dict[str, any]:
        """
        Ask a question and get an answer with sources.

        Args:
            question: User's question

        Returns:
            Dictionary with:
            - answer: LLM's response
            - sources: List of source documents with metadata
            - question: Original question
        """
        logger.info(f"Processing question: {question[:100]}...")

        # 1. Detect language and translate to English for retrieval
        rewrite_result = self.query_rewriter.rewrite(question)
        queries = rewrite_result['queries']  # Already in English
        language_code = rewrite_result['language']
        english_question = rewrite_result['english_question']
        original_question = rewrite_result['original_question']
        language_name = get_language_name(language_code)

        logger.info(f"Detected language: {language_name} ({language_code})")
        if language_code != 'en':
            logger.info(f"Original: {original_question[:60]}...")
            logger.info(f"English: {english_question[:60]}...")

        # 2. Retrieve documents using English queries with similarity scores
        all_docs_with_scores = []
        seen_content = set()  # Deduplicate by content hash

        retrieval_k = self.top_k * self.retrieval_multiplier
        logger.info(f"Retrieving {retrieval_k} candidates per query for filtering...")

        for query in queries:
            # Get documents with similarity scores
            docs_with_scores = self.vector_store.similarity_search_with_score(
                query,
                k=retrieval_k
            )

            # Deduplicate and store with scores
            for doc, score in docs_with_scores:
                content_hash = hash(doc.page_content)
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    all_docs_with_scores.append((doc, score))

        # Sort by similarity score (higher is better)
        all_docs_with_scores.sort(key=lambda x: x[1], reverse=True)

        # Filter by similarity threshold
        filtered_docs = [
            (doc, score) for doc, score in all_docs_with_scores
            if score >= self.similarity_threshold
        ]

        # Log filtering stats
        total_retrieved = len(all_docs_with_scores)
        passed_threshold = len(filtered_docs)
        logger.info(f"Similarity filtering: {passed_threshold}/{total_retrieved} vectors passed threshold {self.similarity_threshold}")

        if filtered_docs:
            top_score = filtered_docs[0][1]
            lowest_score = filtered_docs[-1][1] if len(filtered_docs) > 0 else 0
            logger.info(f"Score range: {lowest_score:.3f} to {top_score:.3f}")

        # Take top_k from filtered results
        final_docs_with_scores = filtered_docs[:self.top_k]
        docs = [doc for doc, score in final_docs_with_scores]

        # Log final selection
        if not docs:
            logger.warning(f"No vectors passed similarity threshold {self.similarity_threshold}! Relaxing threshold...")
            # Fallback: take top_k regardless of threshold
            final_docs_with_scores = all_docs_with_scores[:self.top_k]
            docs = [doc for doc, score in final_docs_with_scores]
            logger.info(f"Using top {len(docs)} vectors with relaxed threshold")

        logger.info(f"Final selection: {len(docs)} documents for context")

        # Display retrieved sources with similarity scores
        if self.verbose_sources == 1:
            print("\n" + "─" * 80)
            print(f"📚 RETRIEVED {len(docs)} CHUNKS FROM VECTOR DB:")
            print("─" * 80)
            for i, (doc, score) in enumerate(final_docs_with_scores, 1):
                title = doc.metadata.get('title', 'Unknown')
                print(f"\n[{i}] {title} (similarity: {score:.3f})")
                print(f"    Content ({len(doc.page_content)} chars):")
                print(f"    {doc.page_content}")
                print()
            print("─" * 80 + "\n")

        # 3. Build context from documents
        context = "\n\n".join([
            f"From episode '{doc.metadata.get('title', 'Unknown')}':\n{doc.page_content}"
            for doc in docs
        ])

# 4. Format prompt with context and English question
        # Include chat history for follow-up questions
        messages = self.prompt.format_messages(
            context=context,
            question=english_question  # Use English for LLM
        )

        # Add previous conversation history before the new question
        if self.chat_history:
            # Insert history between system message and current question
            full_messages = [messages[0]]  # System message with context
            full_messages.extend(self.chat_history)  # Previous conversation
            full_messages.append(messages[1])  # Current question
            messages = full_messages

        # 5. Get answer from LLM (in English)
        response = self.llm.invoke(messages)
        english_answer = response.content

        # 6. Translate answer back to user's language
        if language_code != 'en':
            logger.info(f"Translating answer to {language_name}...")
            answer = self.query_rewriter.translate_answer(
                english_answer,
                language_code,
                language_name
            )
        else:
            answer = english_answer

        # 7. Update chat history (store in user's language for context)
        self.chat_history.append(HumanMessage(content=original_question))
        self.chat_history.append(AIMessage(content=answer))

        # 8. Extract source information
        sources = []
        for doc in docs:
            sources.append({
                "title": doc.metadata.get("title", "Unknown"),
                "transcript_id": doc.metadata.get("transcript_id"),
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            })

        result = {
            "answer": answer,
            "sources": sources,
            "question": question
        }

        logger.info(f"Generated answer with {len(sources)} sources")
        return result

    def chat(self, message: str) -> str:
        """
        Simple chat interface (returns just the answer string).

        Args:
            message: User's message

        Returns:
            Answer string
        """
        result = self.ask(message)
        return result["answer"]

    def reset_conversation(self):
        """Reset conversation history."""
        self.chat_history = []
        logger.info("Conversation history cleared")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history.

        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        history = []
        for msg in self.chat_history:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        return history
