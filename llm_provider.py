import litellm
import logging
from config import LLM_MODEL, LLM_API_KEY, LLM_TEMPERATURE

logger = logging.getLogger(__name__)

# Configure LiteLLM
if LLM_API_KEY:
    litellm.api_key = LLM_API_KEY

def generate_answer(query, context):
    """
    Generate an answer using LLM based on query and context

    Args:
        query: User query
        context: Retrieved context from vector store

    Returns:
        Generated answer string
    """
    try:
        system_prompt = """You are a helpful assistant that answers questions based on provided context.
Always base your answer on the context provided. If the context doesn't contain relevant information,
say so clearly. Be concise and accurate."""

        user_message = f"""Context:
{context}

Question: {query}

Please provide a clear and concise answer based on the context above."""

        response = litellm.completion(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=500
        )

        answer = response.choices[0].message.content
        logger.info(f"Generated answer for query: {query[:50]}...")

        return answer

    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return f"Error generating answer: {str(e)}"

