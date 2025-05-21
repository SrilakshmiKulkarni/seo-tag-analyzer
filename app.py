import os
import logging
import requests
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
from utils.seo_analyzer import analyze_seo_tags

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze the SEO tags of a provided URL"""
    url = request.form.get('url', '')
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Add a timeout to prevent long-running requests
        response = requests.get(url, timeout=10, 
                               headers={
                                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                               })
        
        if response.status_code != 200:
            return jsonify({
                'error': f'Failed to fetch the website. Status code: {response.status_code}'
            }), 400
            
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Get base domain for relative URLs
        base_url = urlparse(url).scheme + '://' + urlparse(url).netloc
        
        # Extract meta tags
        meta_tags = {}
        
        # Title
        title_tag = soup.find('title')
        meta_tags['title'] = title_tag.text if title_tag else None
        
        # Description
        description = soup.find('meta', attrs={'name': 'description'})
        meta_tags['description'] = description['content'] if description and 'content' in description.attrs else None
        
        # Keywords
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        meta_tags['keywords'] = keywords['content'] if keywords and 'content' in keywords.attrs else None
        
        # Canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        meta_tags['canonical'] = canonical['href'] if canonical and 'href' in canonical.attrs else None
        
        # Robots
        robots = soup.find('meta', attrs={'name': 'robots'})
        meta_tags['robots'] = robots['content'] if robots and 'content' in robots.attrs else None
        
        # Viewport
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        meta_tags['viewport'] = viewport['content'] if viewport and 'content' in viewport.attrs else None
        
        # Open Graph tags
        meta_tags['og'] = {}
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        meta_tags['og']['title'] = og_title['content'] if og_title and 'content' in og_title.attrs else None
        
        og_description = soup.find('meta', attrs={'property': 'og:description'})
        meta_tags['og']['description'] = og_description['content'] if og_description and 'content' in og_description.attrs else None
        
        og_image = soup.find('meta', attrs={'property': 'og:image'})
        og_image_content = og_image['content'] if og_image and 'content' in og_image.attrs else None
        if og_image_content and not og_image_content.startswith(('http://', 'https://')):
            og_image_content = urljoin(base_url, og_image_content)
        meta_tags['og']['image'] = og_image_content
        
        og_url = soup.find('meta', attrs={'property': 'og:url'})
        meta_tags['og']['url'] = og_url['content'] if og_url and 'content' in og_url.attrs else None
        
        og_type = soup.find('meta', attrs={'property': 'og:type'})
        meta_tags['og']['type'] = og_type['content'] if og_type and 'content' in og_type.attrs else None
        
        # Twitter Card tags
        meta_tags['twitter'] = {}
        twitter_card = soup.find('meta', attrs={'name': 'twitter:card'})
        meta_tags['twitter']['card'] = twitter_card['content'] if twitter_card and 'content' in twitter_card.attrs else None
        
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        meta_tags['twitter']['title'] = twitter_title['content'] if twitter_title and 'content' in twitter_title.attrs else None
        
        twitter_description = soup.find('meta', attrs={'name': 'twitter:description'})
        meta_tags['twitter']['description'] = twitter_description['content'] if twitter_description and 'content' in twitter_description.attrs else None
        
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        twitter_image_content = twitter_image['content'] if twitter_image and 'content' in twitter_image.attrs else None
        if twitter_image_content and not twitter_image_content.startswith(('http://', 'https://')):
            twitter_image_content = urljoin(base_url, twitter_image_content)
        meta_tags['twitter']['image'] = twitter_image_content
        
        # Favicon
        favicon = None
        favicon_tag = soup.find('link', attrs={'rel': re.compile(r'(icon|shortcut icon)$', re.I)})
        if favicon_tag and 'href' in favicon_tag.attrs:
            favicon_href = favicon_tag['href']
            if not favicon_href.startswith(('http://', 'https://')):
                favicon = urljoin(base_url, favicon_href)
            else:
                favicon = favicon_href
        meta_tags['favicon'] = favicon
        
        # Analyze SEO tags and get recommendations
        analysis = analyze_seo_tags(meta_tags)
        
        # Return results
        return jsonify({
            'url': url,
            'meta_tags': meta_tags,
            'analysis': analysis
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': f'Error fetching the website: {str(e)}'
        }), 400
    except Exception as e:
        logging.error(f"Error analyzing website: {str(e)}")
        return jsonify({
            'error': f'An error occurred while analyzing the website: {str(e)}'
        }), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
