import requests
import xml.etree.ElementTree as ET
from latex2mathml.converter import convert
import re
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def get_latest_papers(author_name, max_results=5):
    url = f'http://export.arxiv.org/api/query?search_query=au:"{author_name}"&max_results={max_results}'
    
    # Set up retry strategy
    retry_strategy = Retry(
        total=5,  # Total number of retries
        backoff_factor=1,  # Wait time between retries: 1, 2, 4, 8, 16 seconds
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
        allowed_methods=["HEAD", "GET", "OPTIONS"]  # Retry for these HTTP methods
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    
    response = http.get(url)
    response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
    
    root = ET.fromstring(response.content)
    papers = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = ' '.join(entry.find('{http://www.w3.org/2005/Atom}title').text.strip().replace('\n', ' ').split())
        abstract = ' '.join(entry.find('{http://www.w3.org/2005/Atom}summary').text.strip().replace('\n', ' ').split())
        authors = [author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')]
        
        # Check for exact match of author name
        if author_name in authors:
            papers.append({'title': title, 'abstract': abstract})
    
    return papers

def update_html_with_papers(html_file, papers):
    with open(html_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    insertion_point = content.find('</div>', content.find('<article id="publications">'))
    if insertion_point == -1:
        raise ValueError("Couldn't find the insertion point in the HTML file.")
    
    insertion_point += len('</div>')  # Move the insertion point to after the </div> tag
    
    new_content = ""
    for paper in papers:
        if paper['title'] not in content:
            title_tag = f"\n\n\t\t\t\t<h3>{paper['title']}</h3>"
            abstract_with_mathml = convert_latex_to_mathml(paper['abstract'])
            abstract_tag = f"\n\t\t\t\t<p>{abstract_with_mathml}</p>"
            new_content += f"{title_tag}{abstract_tag}\n"
    
    if not new_content:
        return False  # No new papers found
    
    updated_content = content[:insertion_point] + new_content + content[insertion_point:]
    
    with open(html_file, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    return True  # New papers were added

def convert_latex_to_mathml(text):
    # This function removes LaTeX $ delimiters in the text and converts LaTeX to MathML
    math_pattern = re.compile(r'\$([^$]+)\$')
    converted_text = text
    for match in math_pattern.findall(text):
        mathml = convert(f'${match}$').replace('$', '').strip()
        converted_text = converted_text.replace(f'${match}$', mathml)
    return converted_text

def main():
    author_name = 'Thomas K. Waters'  # Ensure to use the exact name format as it appears on ArXiv
    html_file = '/Users/waterstk/Documents/GitHub/thomas-k-waters.github.io.backup/index.html'  # Update with your actual path
    
    papers = get_latest_papers(author_name, max_results=100)  # Get a large number to ensure all papers are fetched
    if update_html_with_papers(html_file, papers):
        # Create a flag file to indicate new papers were added
        with open('/tmp/new_papers_added.flag', 'w') as flag_file:
            flag_file.write('New papers were added.')

if __name__ == '__main__':
    main()
