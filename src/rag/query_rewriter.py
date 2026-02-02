"""
Query Rewriting Module - Improves retrieval by rewriting user queries.

Generates multiple optimized search queries from a single user question
to improve coverage and relevance of retrieved documents.
"""
import logging
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)


QUERY_REWRITE_PROMPT = """You are an expert at converting user questions into optimal search queries for a database of Andrew Huberman's podcast transcripts.

Given a user question, generate 2-3 different search queries that will retrieve the most relevant information. These queries should:
- Use different phrasings and terminology
- Cover different aspects of the question
- Include scientific terms when appropriate
- Be concise (10-20 words each)

Examples:

User Question: "sleep stuff"
Search Queries:
1. sleep optimization protocols and sleep hygiene recommendations
2. circadian rhythm and sleep quality improvement strategies
3. sleep supplements and evening routines for better rest

User Question: "What does Huberman say about focus?"
Search Queries:
1. focus and concentration enhancement protocols
2. dopamine and attention improvement strategies
3. cognitive performance and mental clarity techniques

User Question: "best supplements for anxiety"
Search Queries:
1. anxiety reduction supplements and dosage recommendations
2. stress management and calming supplement protocols
3. GABA L-theanine ashwagandha for anxiety relief

Now generate search queries for this question:

User Question: {question}
Search Queries:"""

TRANSLATE_TO_ENGLISH_PROMPT = """Translate the following text to English. Only output the translation, nothing else.

Text: {text}
Translation:"""

TRANSLATE_FROM_ENGLISH_PROMPT = """Translate the following English text to {language}. Only output the translation, nothing else.

English text: {text}
Translation to {language}:"""


class QueryRewriter:
    """
    Rewrites user queries into multiple optimized search queries.

    This improves retrieval by:
    - Using varied terminology (e.g., "focus" → "concentration", "cognitive performance")
    - Adding scientific context (e.g., "sleep" → "circadian rhythm", "sleep architecture")
    - Covering multiple aspects of complex questions
    """

    def __init__(self, llm: BaseChatModel, enabled: bool = True):
        """
        Initialize query rewriter.

        Args:
            llm: Language model for query generation
            enabled: Whether to enable query rewriting (False = passthrough)
        """
        self.llm = llm
        self.enabled = enabled
        self.prompt = ChatPromptTemplate.from_messages([
            ("user", QUERY_REWRITE_PROMPT)
        ])
        self.translate_to_en_prompt = ChatPromptTemplate.from_messages([
            ("user", TRANSLATE_TO_ENGLISH_PROMPT)
        ])
        self.translate_from_en_prompt = ChatPromptTemplate.from_messages([
            ("user", TRANSLATE_FROM_ENGLISH_PROMPT)
        ])

    def _detect_language(self, text: str) -> str:
        """
        Detect the language of the input text.

        Args:
            text: Input text to detect language

        Returns:
            ISO 639-1 language code (e.g., 'en', 'es', 'fr') or 'en' as default
        """
        try:
            from langdetect import detect, LangDetectException
        except Exception as e:
            logger.warning(f"Language detection unavailable: {e}. Defaulting to English.")
            return 'en'

        try:
            lang_code = detect(text)
            logger.debug(f"Detected language: {lang_code}")
            return lang_code
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}. Defaulting to English.")
            return 'en'

    def _translate_to_english(self, text: str, source_lang: str) -> str:
        """
        Translate text to English.

        Args:
            text: Text to translate
            source_lang: Source language code

        Returns:
            Translated text in English
        """
        # If already English, return as-is
        if source_lang == 'en':
            return text

        try:
            messages = self.translate_to_en_prompt.format_messages(text=text)
            response = self.llm.invoke(messages)
            translation = response.content.strip()
            logger.info(f"Translated '{text[:50]}...' to English: '{translation[:50]}...'")
            return translation
        except Exception as e:
            logger.error(f"Translation to English failed: {e}")
            logger.info("Using original text")
            return text

    def translate_answer(self, text: str, target_lang: str, language_name: str) -> str:
        """
        Translate English text to target language.

        Args:
            text: English text to translate
            target_lang: Target language code (e.g., 'es', 'fr')
            language_name: Target language name (e.g., 'Spanish', 'French')

        Returns:
            Translated text
        """
        # If target is English, return as-is
        if target_lang == 'en':
            return text

        try:
            messages = self.translate_from_en_prompt.format_messages(
                text=text,
                language=language_name
            )
            response = self.llm.invoke(messages)
            translation = response.content.strip()
            logger.info(f"Translated answer to {language_name}")
            return translation
        except Exception as e:
            logger.error(f"Translation to {language_name} failed: {e}")
            logger.info("Returning English text")
            return text

    def rewrite(self, question: str) -> Dict[str, any]:
        """
        Rewrite a user question into multiple optimized search queries and detect language.

        Args:
            question: Original user question

        Returns:
            Dictionary with:
            - queries: List of 2-3 optimized search queries (in English)
            - language: ISO 639-1 language code (e.g., 'en', 'es', 'fr')
            - original_question: Original question in user's language
            - english_question: Translated question in English
        """
        # Detect language first
        detected_language = self._detect_language(question)

        # Translate to English for retrieval (vectors are in English)
        english_question = self._translate_to_english(question, detected_language)

        if not self.enabled:
            logger.debug("Query rewriting disabled - using translated question")
            return {
                'queries': [english_question],
                'language': detected_language,
                'original_question': question,
                'english_question': english_question
            }

        try:
            logger.info(f"Rewriting query: {english_question[:80]}...")

            # Generate rewritten queries in English
            messages = self.prompt.format_messages(question=english_question)
            response = self.llm.invoke(messages)

            # Parse response into list of queries
            queries = self._parse_queries(response.content)

            # Always include English question as fallback
            if english_question not in queries:
                queries.insert(0, english_question)

            logger.info(f"Generated {len(queries)} search queries in English (detected language: {detected_language}):")
            for i, q in enumerate(queries, 1):
                logger.info(f"  {i}. {q}")

            return {
                'queries': queries,
                'language': detected_language,
                'original_question': question,
                'english_question': english_question
            }

        except Exception as e:
            logger.error(f"Query rewriting failed: {e}")
            logger.info("Falling back to English question")
            return {
                'queries': [english_question],
                'language': detected_language,
                'original_question': question,
                'english_question': english_question
            }

    def _parse_queries(self, response: str) -> List[str]:
        """
        Parse LLM response into list of queries.

        Expected format:
        1. query one
        2. query two
        3. query three

        Args:
            response: LLM response text

        Returns:
            List of parsed queries
        """
        queries = []

        for line in response.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            # Skip lines that are just explanation/headers
            if line.lower().startswith(('here are', 'search queries:', 'user question:', 'these queries')):
                continue

            # Remove numbering (1. 2. 3. or 1) 2) 3) etc.)
            line = line.lstrip('0123456789.)- \t')

            # Only include substantial queries (>10 chars)
            if line and len(line) > 10:
                queries.append(line)

        # Limit to 3 queries max
        return queries[:3]
