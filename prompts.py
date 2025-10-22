"""
Prompt templates for RAG system
All prompts are defined here for easy customization and management
"""

# System prompts
SYSTEM_PROMPTS = {
    "default": """You are a helpful assistant that answers questions based on provided context. 
Always base your answer on the context provided. If the context doesn't contain relevant information, 
say so clearly. Be concise and accurate.""",
    
    "detailed": """You are an expert assistant that provides detailed, well-structured answers based on provided context.
Always cite the context when providing information. If the context doesn't contain relevant information,
clearly state that. Provide comprehensive answers with proper formatting.""",
    
    "concise": """You are a concise assistant that provides brief, direct answers based on provided context.
Keep answers short and to the point. If the context doesn't contain relevant information, say so.
Avoid unnecessary elaboration.""",
    
    "technical": """You are a technical expert assistant that answers questions based on provided context.
Provide accurate technical information with proper terminology. If the context doesn't contain relevant information,
clearly state that. Use code examples or technical details when appropriate.""",
    
    "educational": """You are an educational assistant that explains concepts based on provided context.
Break down complex ideas into understandable parts. If the context doesn't contain relevant information,
clearly state that. Use examples and analogies when helpful.""",
}

# Query templates
QUERY_TEMPLATES = {
    "default": """Context:
{context}

Question: {query}

Please provide a clear and concise answer based on the context above.""",
    
    "detailed": """Context:
{context}

Question: {query}

Please provide a detailed and comprehensive answer based on the context above. 
Include relevant details and examples from the context.""",
    
    "concise": """Context:
{context}

Question: {query}

Please provide a brief answer in 1-2 sentences based on the context above.""",
    
    "technical": """Context:
{context}

Question: {query}

Please provide a technical answer based on the context above. 
Include relevant technical details, specifications, or code if applicable.""",
    
    "educational": """Context:
{context}

Question: {query}

Please explain the answer in an educational manner based on the context above.
Break down complex concepts and provide examples.""",
    
    "summary": """Context:
{context}

Question: {query}

Please provide a summary-style answer based on the context above.
Highlight the key points and main ideas.""",
}

# Chunk processing prompts
CHUNK_PROCESSING_PROMPTS = {
    "summarize": """Summarize the following text in 2-3 sentences:

{text}

Summary:""",
    
    "extract_keywords": """Extract the main keywords from the following text:

{text}

Keywords:""",
    
    "classify": """Classify the following text into one of these categories: Technical, Business, Educational, News, Other

{text}

Category:""",
}

# Error handling prompts
ERROR_PROMPTS = {
    "no_context": "I don't have any relevant information in the ingested documents to answer your question. Please try a different query or ingest more relevant content.",
    
    "processing_error": "An error occurred while processing your query. Please try again later.",
    
    "invalid_query": "Your query appears to be invalid. Please provide a clear question.",
    
    "no_content": "No content has been ingested yet. Please ingest a URL first using the /ingest-url endpoint.",
}

# Validation prompts
VALIDATION_PROMPTS = {
    "url_invalid": "The provided URL is invalid. Please provide a valid URL starting with http:// or https://",
    
    "query_empty": "Query cannot be empty. Please provide a valid question.",
    
    "query_too_long": "Query is too long. Please keep it under 1000 characters.",
    
    "top_k_invalid": "top_k must be between 1 and 20.",
}

def get_system_prompt(prompt_type="default"):
    """Get system prompt by type
    
    Args:
        prompt_type: Type of system prompt (default, detailed, concise, technical, educational)
    
    Returns:
        System prompt string
    """
    return SYSTEM_PROMPTS.get(prompt_type, SYSTEM_PROMPTS["default"])

def get_query_template(template_type="default"):
    """Get query template by type
    
    Args:
        template_type: Type of query template
    
    Returns:
        Query template string
    """
    return QUERY_TEMPLATES.get(template_type, QUERY_TEMPLATES["default"])

def get_error_message(error_type="processing_error"):
    """Get error message by type
    
    Args:
        error_type: Type of error
    
    Returns:
        Error message string
    """
    return ERROR_PROMPTS.get(error_type, ERROR_PROMPTS["processing_error"])

def get_validation_message(validation_type="query_empty"):
    """Get validation message by type
    
    Args:
        validation_type: Type of validation error
    
    Returns:
        Validation message string
    """
    return VALIDATION_PROMPTS.get(validation_type, VALIDATION_PROMPTS["query_empty"])

def format_query_prompt(query, context, template_type="default"):
    """Format query prompt with context
    
    Args:
        query: User query
        context: Retrieved context
        template_type: Type of template to use
    
    Returns:
        Formatted prompt string
    """
    template = get_query_template(template_type)
    return template.format(query=query, context=context)

