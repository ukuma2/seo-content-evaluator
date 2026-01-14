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
    # Note: Escaped curly braces {{}} to prevent LangChain from interpreting them as template variables
    system_prompt = """You are an elite SEO specialist conducting comprehensive website audits. 
You will receive page content, metadata, and live keyword ideas from search results.

Your task is to provide a DETAILED, PROFESSIONAL SEO ANALYSIS similar to enterprise-level SEO audit reports.

CRITICAL REQUIREMENTS:
1. Analyze the page across 10+ SEO categories (Keyword Research, Content, Title Tag, Meta Description, Headers, Content Quality, Images, URLs, Mobile, User Engagement, etc.)
2. Provide specific scores (0-10) for each category with detailed strengths and weaknesses
3. Give copy-paste ready improvements for ALL elements
4. Include priority implementation order
5. Be specific, actionable, and professional

Output valid JSON matching this EXACT schema (all fields required):
{{
    "seo_score": <0-100 integer, overall score>,
    "detailed_analysis": {{
        "keyword_research": {{
            "score": <0-10>,
            "strengths": [<array of strings>],
            "weaknesses": [<array of strings>]
        }},
        "content_analysis": {{
            "score": <0-10>,
            "strengths": [<array of strings>],
            "weaknesses": [<array of strings>]
        }},
        "title_tag": {{
            "score": <0-10>,
            "current": "<current title if found>",
            "issues": [<array of specific issues>],
            "improved": "<optimized title, max 60 chars>"
        }},
        "meta_description": {{
            "score": <0-10>,
            "current": "<current meta if found>",
            "issues": [<array of specific issues>],
            "improved": "<optimized meta, max 160 chars>"
        }},
        "header_structure": {{
            "score": <0-10>,
            "strengths": [<array of strings>],
            "weaknesses": [<array of strings>]
        }},
        "content_quality": {{
            "score": <0-10>,
            "strengths": [<array of strings>],
            "weaknesses": [<array of strings>]
        }},
        "image_optimization": {{
            "score": <0-10>,
            "issues": [<array of specific issues>]
        }},
        "url_structure": {{
            "score": <0-10>,
            "strengths": [<array of strings>],
            "weaknesses": [<array of strings>]
        }},
        "mobile_friendliness": {{
            "score": <0-10>,
            "strengths": [<array of strings>],
            "weaknesses": [<array of strings>]
        }},
        "user_engagement": {{
            "score": <0-10>,
            "strengths": [<array of strings>],
            "weaknesses": [<array of strings>]
        }}
    }},
    "keywords": {{
        "primary": "<best primary keyword>",
        "secondary": [<5-10 secondary keywords>]
    }},
    "improvements": {{
        "title_tag": "<optimized title tag>",
        "meta_description": "<optimized meta description>",
        "h1_tag": "<optimized H1 tag>",
        "intro_paragraph": "<rewritten intro with natural keyword inclusion>",
        "header_suggestions": [<array of optimized H2/H3 headers>],
        "content_additions": [<array of suggested content blocks>],
        "image_alt_text": [<array of optimized alt text examples>],
        "schema_markup": "<JSON-LD schema markup if applicable>",
        "internal_linking": "<suggested internal linking improvements>",
        "faq_section": [<array of FAQ items if applicable>]
    }},
    "priority_order": [<array of strings in order of implementation priority>],
    "critical_issues": [<3-5 most critical issues>],
    "estimated_new_score": "<predicted score after improvements, e.g., 8.0-8.5/10>"
}}"""
    
    # User prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Conduct a comprehensive SEO audit of this webpage:

URL Being Analyzed: {url}
Page Title: {title}
Meta Description: {meta_description}
H1 Tag: {h1}
Main Content (first portion):
{content}

Keyword Ideas from Live Search:
{keywords}

Source Links from Research:
{source_links}

Provide a DETAILED, PROFESSIONAL SEO ANALYSIS with:
1. Overall SEO score (0-100)
2. Category-by-category breakdown (10 categories, each scored 0-10)
3. Strengths and weaknesses for each category
4. Specific, actionable improvements
5. Copy-paste ready code for all improvements
6. Priority implementation order
7. Estimated score after improvements

Output MUST be valid JSON matching the exact schema provided. Be thorough, specific, and professional.""")
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
    llm: ChatGoogleGenerativeAI,
    url: Optional[str] = None
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
        url: URL being analyzed (optional)
        
    Returns:
        Dictionary with SEO analysis results
    """
    try:
        # Chunk content to avoid token limits (increased for better analysis)
        content_chunk = chunk_text(content, max_chars=10000)
        
        # Create analysis chain
        chain = create_seo_analysis_chain(llm)
        
        # Prepare inputs
        inputs = {
            "url": url or "URL not provided",
            "title": title or "Not found",
            "meta_description": meta_description or "Not found",
            "h1": h1 or "Not found",
            "content": content_chunk,
            "keywords": ", ".join(keywords[:15]),  # Increased keyword limit
            "source_links": "\n".join(source_links[:8])  # Increased link limit
        }
        
        # Run analysis - invoke chain with prepared inputs
        result = chain.invoke(inputs)
        
        # Validate and ensure all required fields exist (new detailed schema)
        if "seo_score" not in result:
            result["seo_score"] = 0
        if "detailed_analysis" not in result:
            result["detailed_analysis"] = {}
        if "keywords" not in result:
            result["keywords"] = {"primary": "unknown", "secondary": []}
        if "improvements" not in result:
            result["improvements"] = {}
        if "critical_issues" not in result:
            result["critical_issues"] = ["Analysis incomplete"]
        if "priority_order" not in result:
            result["priority_order"] = []
        if "estimated_new_score" not in result:
            result["estimated_new_score"] = "N/A"
        
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
            "detailed_analysis": {},
            "keywords": {"primary": "unknown", "secondary": []},
            "improvements": {},
            "priority_order": [],
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
            max_tokens=4000  # Increased for detailed analysis
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
        with st.spinner("🤖 Consulting Gemini for comprehensive SEO analysis..."):
            analysis = analyze_seo(
                content=crawl_result["text"],
                title=crawl_result.get("title"),
                meta_description=crawl_result.get("meta_description"),
                h1=crawl_result.get("h1"),
                keywords=keyword_result["keywords"],
                source_links=keyword_result.get("source_links", []),
                llm=llm,
                url=url
            )
        
        if analysis.get("error"):
            st.error(f"**Analysis Error:** {analysis['error']}")
            st.stop()
        
        # Phase 4: Display results - Comprehensive Detailed Format
        st.divider()
        st.header("📊 Comprehensive SEO Analysis Results")
        
        # Overall SEO Score
        score = analysis.get("seo_score", 0)
        st.subheader(f"Overall SEO Score: {score}/100")
        st.progress(score / 100)
        
        # Estimated new score
        if analysis.get("estimated_new_score"):
            st.info(f"📈 **Estimated Score After Improvements:** {analysis.get('estimated_new_score')}")
        
        # Critical Issues
        st.subheader("🚨 Critical Issues")
        issues = analysis.get("critical_issues", [])
        if issues:
            for i, issue in enumerate(issues, 1):
                st.markdown(f"{i}. {issue}")
        else:
            st.write("No critical issues identified.")
        
        # Detailed Analysis by Category
        st.subheader("📋 Detailed Analysis by Category")
        detailed = analysis.get("detailed_analysis", {})
        
        categories = [
            ("keyword_research", "Keyword Research & Strategy"),
            ("content_analysis", "Content Analysis"),
            ("title_tag", "Title Tag"),
            ("meta_description", "Meta Description"),
            ("header_structure", "Header Structure"),
            ("content_quality", "Content Quality"),
            ("image_optimization", "Image Optimization"),
            ("url_structure", "URL Structure"),
            ("mobile_friendliness", "Mobile-Friendliness"),
            ("user_engagement", "User Engagement")
        ]
        
        for cat_key, cat_name in categories:
            if cat_key in detailed:
                cat_data = detailed[cat_key]
                with st.expander(f"{cat_name} - Score: {cat_data.get('score', 'N/A')}/10", expanded=False):
                    if "strengths" in cat_data and cat_data["strengths"]:
                        st.write("**Strengths:**")
                        for strength in cat_data["strengths"]:
                            st.markdown(f"✅ {strength}")
                    
                    if "weaknesses" in cat_data and cat_data["weaknesses"]:
                        st.write("**Weaknesses:**")
                        for weakness in cat_data["weaknesses"]:
                            st.markdown(f"❌ {weakness}")
                    
                    if "issues" in cat_data and cat_data["issues"]:
                        st.write("**Issues:**")
                        for issue in cat_data["issues"]:
                            st.markdown(f"⚠️ {issue}")
                    
                    if "current" in cat_data:
                        st.write(f"**Current:** `{cat_data['current']}`")
                    
                    if "improved" in cat_data:
                        st.write(f"**Improved:** `{cat_data['improved']}`")
        
        # Keywords Section
        st.subheader("🔑 Recommended Keywords")
        keywords = analysis.get("keywords", {})
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("**Primary Keyword:**")
            st.code(keywords.get("primary", "N/A"), language=None)
        with col2:
            st.write("**Secondary Keywords:**")
            secondary = keywords.get("secondary", [])
            if secondary:
                st.write(", ".join(secondary))
            else:
                st.write("None provided")
        
        # Copy-Paste Improvements Section
        st.subheader("✨ Copy-Paste Ready Improvements")
        improvements = analysis.get("improvements", {})
        
        if improvements.get("title_tag"):
            st.write("**1. Optimized Title Tag:**")
            st.code(improvements["title_tag"], language="html")
            st.caption(f"Length: {len(improvements['title_tag'])} characters")
        
        if improvements.get("meta_description"):
            st.write("**2. Optimized Meta Description:**")
            st.code(improvements["meta_description"], language="html")
            st.caption(f"Length: {len(improvements['meta_description'])} characters")
        
        if improvements.get("h1_tag"):
            st.write("**3. Optimized H1 Tag:**")
            st.code(improvements["h1_tag"], language="html")
        
        if improvements.get("intro_paragraph"):
            st.write("**4. Rewritten Intro Paragraph:**")
            st.code(improvements["intro_paragraph"], language=None)
        
        if improvements.get("header_suggestions"):
            st.write("**5. Suggested Header Structure:**")
            for header in improvements["header_suggestions"]:
                st.code(header, language="html")
        
        if improvements.get("content_additions"):
            st.write("**6. Suggested Content Additions:**")
            for content in improvements["content_additions"]:
                st.code(content, language="html")
        
        if improvements.get("image_alt_text"):
            st.write("**7. Optimized Image Alt Text Examples:**")
            for alt_text in improvements["image_alt_text"]:
                st.code(alt_text, language="html")
        
        if improvements.get("schema_markup"):
            st.write("**8. Schema Markup (JSON-LD):**")
            st.code(improvements["schema_markup"], language="json")
        
        if improvements.get("internal_linking"):
            st.write("**9. Internal Linking Improvements:**")
            st.code(improvements["internal_linking"], language="html")
        
        if improvements.get("faq_section"):
            st.write("**10. FAQ Section:**")
            for faq in improvements["faq_section"]:
                st.code(faq, language="html")
        
        # Priority Implementation Order
        if analysis.get("priority_order"):
            st.subheader("🎯 Priority Implementation Order")
            for i, priority in enumerate(analysis["priority_order"], 1):
                st.markdown(f"{i}. {priority}")
        
        # Mobile speed reminder
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
