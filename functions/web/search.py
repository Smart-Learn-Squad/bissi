"""Web search and content fetching for BISSI.

Provides web search capabilities and URL content extraction.
"""
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import re


def fetch_url(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Fetch and extract content from URL.
    
    Args:
        url: Target URL
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with status, title, content, and links
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else 'No title'
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http'):
                links.append({
                    'url': href,
                    'text': link.get_text(strip=True)[:50]
                })
        
        return {
            'success': True,
            'url': url,
            'status_code': response.status_code,
            'title': title_text,
            'content': text[:5000],  # Limit content
            'links': links[:10],  # Limit links
            'content_type': response.headers.get('content-type', 'unknown')
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'url': url,
            'error': str(e)
        }


def search_web(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Search web for query (placeholder - requires search API).
    
    This is a placeholder that returns mock results.
    For real search, integrate with Google Custom Search API, Bing API, etc.
    
    Args:
        query: Search query
        num_results: Number of results to return
        
    Returns:
        List of search results
    """
    # Note: Real web search requires API keys
    # This is a mock implementation for demonstration
    
    return [
        {
            'title': f'Search results for "{query}"',
            'url': 'https://example.com',
            'snippet': 'Web search requires API integration. Please configure Google Custom Search or similar service.'
        }
    ]


def extract_article(url: str) -> Dict[str, Any]:
    """Extract article content from URL (news, blog posts).
    
    Args:
        url: Article URL
        
    Returns:
        Article content with metadata
    """
    result = fetch_url(url)
    
    if not result['success']:
        return result
    
    # Try to extract article-specific content
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for article content
        article_selectors = [
            'article', '[role="main"]', '.article-content', '.post-content',
            '.entry-content', 'main', '#content'
        ]
        
        article_text = ''
        for selector in article_selectors:
            element = soup.select_one(selector)
            if element:
                # Remove non-content elements
                for tag in element.find_all(['script', 'style', 'nav', 'aside', 'footer']):
                    tag.decompose()
                article_text = element.get_text(separator='\n', strip=True)
                break
        
        if article_text:
            result['article_content'] = article_text[:8000]
        
        # Extract metadata
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            result['description'] = meta_desc.get('content', '')
        
        og_image = soup.find('meta', property='og:image')
        if og_image:
            result['image'] = og_image.get('content', '')
        
    except Exception:
        pass
    
    return result


def download_file(url: str, 
                  save_path: Union[str, Path],
                  chunk_size: int = 8192) -> Dict[str, Any]:
    """Download file from URL.
    
    Args:
        url: File URL
        save_path: Local path to save file
        chunk_size: Download chunk size
        
    Returns:
        Download result with file info
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        total_size = 0
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        return {
            'success': True,
            'url': url,
            'file_path': str(save_path),
            'file_size': total_size,
            'content_type': response.headers.get('content-type', 'unknown')
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'url': url,
            'error': str(e)
        }


def is_valid_url(url: str) -> bool:
    """Check if string is valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL
    """
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(pattern.match(url))


def extract_domain(url: str) -> str:
    """Extract domain from URL.
    
    Args:
        url: Full URL
        
    Returns:
        Domain name
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return url
