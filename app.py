"""
Advanced SEO Content Evaluator
===============================
A Streamlit app that crawls URLs, researches keywords via DuckDuckGo,
and uses Google Gemini to analyze and improve SEO content.

Tech Stack:
- Streamlit: UI framework
- LangChain: LLM orchestration (LCEL)
- Google Gemini: Content analysis
- WebBaseLoader: URL content extraction
- DuckDuckGoSearchRun: Live keyword research

Author: Senior Python Developer
"""

import streamlit as st
import json
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from html import unescape

# LangChain imports
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough


# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

# Page configuration
st.set_page_config(
    page_title="Advanced SEO Content Evaluator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for caching
if "crawl_cache" not in st.session_state:
    st.session_state.crawl_cache = {}
if "search_cache" not in st.session_state:
    st.session_state.search_cache = {}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_url(url: str) -> bool:
    """
    Validate URL format (must be http or https).
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ["http", "https"], result.netloc])
    except Exception:
        return False


def extract_html_metadata(html_content: str) -> Dict[str, Optional[str]]:
    """
    Extract title, meta description, and H1 from HTML content.
    Uses regex patterns for basic parsing (best effort approach).
    
    Args:
        html_content: Raw HTML string
        
    Returns:
        Dictionary with 'title', 'meta_description', and 'h1' keys
    """
    metadata = {
        "title": None,
        "meta_description": None,
        "h1": None
    }
    
    # Extract title tag
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if title_match:
        metadata["title"] = unescape(title_match.group(1).strip())
    
    # Extract meta description
    meta_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']',
        html_content,
        re.IGNORECASE
    )
    if meta_match:
        metadata["meta_description"] = unescape(meta_match.group(1).strip())
    
    # Extract first H1 tag
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE | re.DOTALL)
    if h1_match:
        metadata["h1"] = unescape(re.sub(r'<[^>]+>', '', h1_match.group(1)).strip())
    
    return metadata


def chunk_text(text: str, max_chars: int = 10000) -> str:
    """
    Truncate text to avoid excessive token usage.
    Keeps first max_chars characters and adds truncation notice.
    
    Args:
        text: Text to chunk
        max_chars: Maximum characters to keep
        
    Returns:
        Truncated text with notice if needed
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[Content truncated for analysis...]"


# ============================================================================
# PHASE 1: CRAWL URL CONTENT
# ============================================================================

@st.cache_data(show_spinner=False)
def crawl_url(url: str) -> Dict[str, Any]:
    """
    Crawl URL and extract content using WebBaseLoader.
    Cached per URL to avoid redundant requests.
    
    Args:
        url: URL to crawl
        
    Returns:
        Dictionary with 'text', 'title', 'meta_description', 'h1', and 'error'
    """
    result = {
        "text": "",
        "title": None,
        "meta_description": None,
        "h1": None,
        "error": None
    }
    
    try:
        # Set realistic User-Agent to avoid blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Load page content
        loader = WebBaseLoader(
            web_paths=[url],
            header_template=headers
        )
        documents = loader.load()
        
        if not documents or not documents[0].page_content:
            result["error"] = "No content extracted from page. The page may be empty or require JavaScript rendering."
            return result
        
        # Extract main text content
        result["text"] = documents[0].page_content.strip()
        
        # Try to extract HTML metadata if available
        if hasattr(documents[0], 'metadata') and 'source' in documents[0].metadata:
            # WebBaseLoader may store raw HTML in metadata or we can access it differently
            # For now, we'll parse from page_content if HTML tags are present
            if "<" in result["text"] and ">" in result["text"]:
                metadata = extract_html_metadata(result["text"])
                result.update(metadata)
        
        # If no text extracted, set error
        if not result["text"]:
            result["error"] = "Empty content extracted. The page may be blocked or require authentication."
            
    except Exception as e:
        error_msg = str(e).lower()
        if "403" in error_msg or "forbidden" in error_msg:
            result["error"] = "403 Forbidden: Access denied. The website blocked our request."
        elif "timeout" in error_msg or "timed out" in error_msg:
            result["error"] = "Request timeout: The website took too long to respond."
        elif "404" in error_msg or "not found" in error_msg:
            result["error"] = "404 Not Found: The URL does not exist."
        else:
            result["error"] = f"Crawl error: {str(e)}"
    
    return result


# ============================================================================
# PHASE 2: RESEARCH KEYWORDS (LIVE SEARCH)
# ============================================================================

@st.cache_data(show_spinner=False)
def get_topic_summary(content: str, llm: ChatGoogleGenerativeAI) -> str:
    """
    Use Gemini to summarize page topic into 3-6 words.
    Cached per content hash to avoid redundant calls.
    
    Args:
        content: Page content (first 500 chars)
        llm: Initialized Gemini LLM instance
        
    Returns:
        Topic summary string
    """
    try:
        prompt = f"""Summarize the main topic of this webpage content in 3-6 words.
        
Content preview:
{content[:500]}

Topic (3-6 words only):"""
        
        response = llm.invoke(prompt)
        topic = response.content.strip().strip('"').strip("'")
        return topic[:50]  # Safety limit
    except Exception as e:
        return "web content"  # Fallback


@st.cache_data(show_spinner=False)
def research_keywords(topic: str) -> Dict[str, Any]:
    """
    Research keywords using DuckDuckGo search.
    This produces SERP-derived keyword ideas, not authoritative keyword volume data.
    Cached per topic to avoid redundant searches.
    
    Args:
        topic: Topic string to research
        
    Returns:
        Dictionary with 'keywords' list and 'source_links' list
    """
    result = {
        "keywords": [],
        "source_links": []
    }
    
    try:
        search = DuckDuckGoSearchRun()
        
        # Build search queries for keyword discovery
        queries = [
            f"primary keyword for {topic}",
            f"{topic} best practices 2026",
            f"people also ask {topic}",
            f"{topic} SEO tips",
            f"how to optimize {topic}"
        ]
        
        keywords_set = set()
        links_set = set()
        
        for query in queries:
            try:
                search_result = search.run(query)
                
                # Extract potential keywords from search results
                # DuckDuckGo returns text snippets that may contain keywords
                if search_result:
                    # Simple extraction: look for quoted phrases or common patterns
                    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', search_result)
                    keywords_set.update([w.lower() for w in words if len(w.split()) <= 3])
                    
                    # Try to extract URLs if present in result
                    url_pattern = r'https?://[^\s]+'
                    found_urls = re.findall(url_pattern, search_result)
                    links_set.update(found_urls[:3])  # Limit per query
                    
            except Exception as e:
                # Continue with next query if one fails
                continue
        
        # Add the topic itself as primary keyword candidate
        keywords_set.add(topic.lower())
        
        result["keywords"] = list(keywords_set)[:15]  # Limit to 15 unique keywords
        result["source_links"] = list(links_set)[:10]  # Limit to 10 links
        
    except Exception as e:
        # If search fails, return topic as fallback keyword
        result["keywords"] = [topic.lower()]
        result["error"] = f"Search error: {str(e)}"
    
    return result


# ============================================================================
# PHASE 3: GEMINI ANALYSIS
# ============================================================================

def create_seo_analysis_chain(llm: ChatGoogleGenerativeAI) -> Any:
    """
    Create LangChain LCEL chain for SEO analysis with structured JSON output.
    
    Args:
        llm: Initialized Gemini LLM instance
        
    Returns:
        LangChain Runnable chain
    """
    # Define output schema
    output_parser = JsonOutputParser()
    
    # System prompt for Gemini
    system_prompt = """You are an elite SEO specialist using modern ranking factors. 
You will receive page content and live keyword ideas from search results. 

Your task:
1. Pick the best primary keyword from the provided keyword ideas
2. Verify keyword placement in Title/H1/first 100 words
3. Target 1-2% keyword density (natural, not stuffed)
4. Improve readability and user experience
5. Output exact replacements for Title, Meta Description, and intro paragraph
6. Remind the user to check mobile speed via PageSpeed Insights

Output valid JSON matching this exact schema:
{
    "seo_score": <0-100 integer>,
    "critical_issues": [<3 strings describing issues>],
    "primary_keyword": "<string>",
    "secondary_keywords": [<5 strings>],
    "new_title": "<string, max 60 chars>",
    "new_meta_description": "<string, max 160 chars>",
    "rewritten_intro": "<string, natural paragraph with keyword inclusion>",
    "suggested_h1": "<string, optional if H1 is missing/weak>",
    "mobile_speed_reminder": "<string reminder>"
}"""
    
    # User prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Analyze this webpage for SEO:

Page Title: {title}
Meta Description: {meta_description}
H1: {h1}
Main Content (first portion):
{content}

Keyword Ideas from Live Search:
{keywords}

Source Links:
{source_links}

Provide SEO analysis and improvements in the required JSON format.""")
    ])
    
    # Create chain with LCEL
    # Note: We'll invoke with dict inputs directly, so no need for RunnablePassthrough
    chain = prompt_template | llm | output_parser
    
    return chain


def analyze_seo(
    content: str,
    title: Optional[str],
    meta_description: Optional[str],
    h1: Optional[str],
    keywords: List[str],
    source_links: List[str],
    llm: ChatGoogleGenerativeAI
) -> Dict[str, Any]:
    """
    Run SEO analysis using Gemini via LangChain chain.
    
    Args:
        content: Page content text
        title: Page title (if available)
        meta_description: Meta description (if available)
        h1: H1 tag content (if available)
        keywords: List of keyword candidates
        source_links: List of source URLs
        llm: Initialized Gemini LLM instance
        
    Returns:
        Dictionary with SEO analysis results
    """
    try:
        # Chunk content to avoid token limits
        content_chunk = chunk_text(content, max_chars=8000)
        
        # Create analysis chain
        chain = create_seo_analysis_chain(llm)
        
        # Prepare inputs
        inputs = {
            "title": title or "Not found",
            "meta_description": meta_description or "Not found",
            "h1": h1 or "Not found",
            "content": content_chunk,
            "keywords": ", ".join(keywords[:10]),  # Limit keywords in prompt
            "source_links": "\n".join(source_links[:5])  # Limit links in prompt
        }
        
        # Run analysis - invoke chain with prepared inputs
        result = chain.invoke(inputs)
        
        # Validate and ensure all required fields exist
        required_fields = [
            "seo_score", "critical_issues", "primary_keyword",
            "secondary_keywords", "new_title", "new_meta_description",
            "rewritten_intro"
        ]
        
        for field in required_fields:
            if field not in result:
                result[field] = "Not provided" if field != "seo_score" else 0
                if field == "critical_issues":
                    result[field] = ["Analysis incomplete"]
                elif field == "secondary_keywords":
                    result[field] = []
        
        return result
        
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors - Gemini might return malformed JSON
        return {
            "seo_score": 0,
            "critical_issues": [f"JSON parsing error: {str(e)}. The AI response may not have been valid JSON."],
            "primary_keyword": "unknown",
            "secondary_keywords": [],
            "new_title": "Error during analysis - invalid JSON response",
            "new_meta_description": "Error during analysis - invalid JSON response",
            "rewritten_intro": "Error during analysis - invalid JSON response",
            "error": f"JSON parsing failed: {str(e)}"
        }
    except Exception as e:
        # Return error structure for other exceptions
        error_msg = str(e)
        return {
            "seo_score": 0,
            "critical_issues": [f"Analysis error: {error_msg}"],
            "primary_keyword": "unknown",
            "secondary_keywords": [],
            "new_title": "Error during analysis",
            "new_meta_description": "Error during analysis",
            "rewritten_intro": "Error during analysis",
            "error": error_msg
        }


# ============================================================================
# STREAMLIT UI
# ============================================================================

def main():
    """Main Streamlit app function."""
    
    # Header
    st.title("🔍 Advanced SEO Content Evaluator")
    st.markdown("""
    **Analyze and improve your webpage's SEO** using AI-powered content evaluation.
    
    This tool will:
    1. 🕷️ Crawl your URL and extract content
    2. 🔎 Research live keyword ideas via search
    3. 🤖 Analyze content with Google Gemini
    4. ✨ Provide copy-paste improvements
    """)
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Model selection
    model_options = {
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-3-flash-preview": "gemini-3-flash-preview",
        "gemini-3-pro-preview": "gemini-3-pro-preview"
    }
    
    selected_model = st.sidebar.selectbox(
        "Gemini Model",
        options=list(model_options.keys()),
        index=0,
        help="Select the Gemini model to use for analysis"
    )
    
    model_name = model_options[selected_model]
    
    # API Key check - works for both local and Streamlit Cloud
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except KeyError:
        st.error("""
        ⚠️ **API Key Missing**
        
        **For Local Development:**
        Create a `.streamlit/secrets.toml` file with:
        ```toml
        GOOGLE_API_KEY = "your-api-key-here"
        ```
        
        **For Streamlit Cloud:**
        Go to your app settings → Secrets → Add secret:
        - Key: `GOOGLE_API_KEY`
        - Value: `your-api-key-here`
        
        **Get your Google API Key:**
        Visit [Google AI Studio](https://makersuite.google.com/app/apikey) to create an API key.
        """)
        st.stop()
    
    # Initialize LLM
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.3,  # Lower temperature for more consistent analysis
            max_tokens=2000
        )
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {str(e)}")
        st.stop()
    
    # URL input
    st.divider()
    url = st.text_input(
        "🌐 Enter URL to Analyze",
        placeholder="https://example.com/page",
        help="Enter a valid HTTP or HTTPS URL"
    )
    
    if not url:
        st.info("👆 Enter a URL above to get started")
        st.stop()
    
    # Validate URL
    if not validate_url(url):
        st.error("❌ Invalid URL. Please enter a valid HTTP or HTTPS URL.")
        st.stop()
    
    # Process button
    if st.button("🚀 Analyze SEO", type="primary", use_container_width=True):
        
        # Phase 1: Crawl
        with st.spinner("🕷️ Crawling website..."):
            crawl_result = crawl_url(url)
        
        if crawl_result.get("error"):
            st.error(f"**Crawl Error:** {crawl_result['error']}")
            st.info("💡 **Tips:**\n- Check if the URL is accessible\n- Some sites block automated crawlers\n- Try a different page or contact support")
            st.stop()
        
        if not crawl_result.get("text"):
            st.warning("⚠️ No text content extracted. The page may require JavaScript rendering.")
            st.stop()
        
        # Display crawl results
        with st.expander("📄 Extracted Content Preview", expanded=False):
            st.text_area("Page Text", crawl_result["text"][:1000], height=200, disabled=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Title", crawl_result.get("title") or "Not found")
            with col2:
                st.metric("Meta Description", crawl_result.get("meta_description") or "Not found")
            with col3:
                st.metric("H1", crawl_result.get("h1") or "Not found")
        
        # Phase 2: Research keywords
        with st.spinner("🔎 Researching keywords via DuckDuckGo..."):
            # Get topic summary
            topic = get_topic_summary(crawl_result["text"][:500], llm)
            
            # Research keywords
            keyword_result = research_keywords(topic)
        
        if keyword_result.get("error"):
            st.warning(f"⚠️ Keyword research warning: {keyword_result['error']}")
        
        # Display keyword research
        with st.expander("🔑 Keyword Research Results", expanded=False):
            st.write(f"**Topic:** {topic}")
            st.write(f"**Found {len(keyword_result['keywords'])} keyword candidates**")
            st.write(", ".join(keyword_result["keywords"][:10]))
            if keyword_result.get("source_links"):
                st.write("**Source Links:**")
                for link in keyword_result["source_links"][:5]:
                    st.write(f"- {link}")
        
        # Phase 3: Gemini analysis
        with st.spinner("🤖 Consulting Gemini for SEO analysis..."):
            analysis = analyze_seo(
                content=crawl_result["text"],
                title=crawl_result.get("title"),
                meta_description=crawl_result.get("meta_description"),
                h1=crawl_result.get("h1"),
                keywords=keyword_result["keywords"],
                source_links=keyword_result.get("source_links", []),
                llm=llm
            )
        
        if analysis.get("error"):
            st.error(f"**Analysis Error:** {analysis['error']}")
            st.stop()
        
        # Phase 4: Display results
        st.divider()
        st.header("📊 SEO Analysis Results")
        
        # SEO Score
        score = analysis.get("seo_score", 0)
        st.subheader(f"SEO Score: {score}/100")
        st.progress(score / 100)
        
        # Critical Issues
        st.subheader("🚨 Critical Issues")
        issues = analysis.get("critical_issues", [])
        for i, issue in enumerate(issues, 1):
            st.markdown(f"{i}. {issue}")
        
        # Keywords
        st.subheader("🔑 Recommended Keywords")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("**Primary Keyword:**")
            st.code(analysis.get("primary_keyword", "N/A"), language=None)
        with col2:
            st.write("**Secondary Keywords:**")
            secondary = analysis.get("secondary_keywords", [])
            if secondary:
                st.write(", ".join(secondary))
            else:
                st.write("None provided")
        
        # Copy-paste improvements
        st.subheader("✨ Copy-Paste Improvements")
        
        st.write("**New Title Tag** (≤60 chars):")
        new_title = analysis.get("new_title", "Not provided")
        st.code(new_title, language=None)
        st.caption(f"Length: {len(new_title)} characters")
        
        st.write("**New Meta Description** (≤160 chars):")
        new_meta = analysis.get("new_meta_description", "Not provided")
        st.code(new_meta, language=None)
        st.caption(f"Length: {len(new_meta)} characters")
        
        st.write("**Rewritten Intro Paragraph:**")
        rewritten_intro = analysis.get("rewritten_intro", "Not provided")
        st.code(rewritten_intro, language=None)
        
        if analysis.get("suggested_h1"):
            st.write("**Suggested H1:**")
            st.code(analysis.get("suggested_h1"), language=None)
        
        # Mobile speed reminder
        if analysis.get("mobile_speed_reminder"):
            st.info(f"💡 **Reminder:** {analysis.get('mobile_speed_reminder')}")
        else:
            st.info("💡 **Reminder:** Check mobile page speed via [PageSpeed Insights](https://pagespeed.web.dev/)")
        
        # Source links
        if keyword_result.get("source_links"):
            st.subheader("🔗 Source Links from Research")
            for link in keyword_result["source_links"][:10]:
                st.markdown(f"- [{link}]({link})")
        
        # Raw JSON (optional)
        with st.expander("📋 Raw Analysis JSON", expanded=False):
            st.json(analysis)


if __name__ == "__main__":
    main()
