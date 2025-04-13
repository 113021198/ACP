import scrapy
import datetime
import xml.dom.minidom
from xml.etree.ElementTree import Element, SubElement, tostring
import re


class GitHubSpider(scrapy.Spider):
    name = 'github_repos'
    github_username = 'radiandrmwn'

    start_urls = [f'https://github.com/{github_username}?tab=repositories']
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
        'DOWNLOAD_DELAY': 1, 
        'ROBOTSTXT_OBEY': False,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repositories = []

    def parse(self, response):
        # GitHub has different repository layouts - try multiple selectors
        repositories = response.css('li[itemprop="owns"], div[data-testid="user-repositories"] div.Box-row')
        self.logger.info(f"Found {len(repositories)} repositories")

        for repo in repositories:
            # Extract repository URL with multiple selector options
            repo_href = repo.css('a[itemprop="name codeRepository"]::attr(href)').get() or \
                        repo.css('h3 a[data-testid="repository-link"]::attr(href)').get() or \
                        repo.css('h3 a::attr(href)').get()
            
            if not repo_href:
                continue
                
            repo_url = response.urljoin(repo_href)
            
            # Extract repository name with multiple selector options
            repo_name = (repo.css('a[itemprop="name codeRepository"]::text').get() or \
                         repo.css('h3 a[data-testid="repository-link"]::text').get() or \
                         repo.css('h3 a::text').get() or '').strip()
            
            # Extract repository description with multiple selector options
            about = repo.css('p[itemprop="description"]::text').get() or \
                    repo.css('p.color-fg-muted.mb-0::text').get() or \
                    repo.css('p.color-text-secondary::text').get()
            
            if about:
                about = about.strip()
            else:
                about = repo_name
            
            # Extract last updated timestamp with multiple selector options
            last_updated = repo.css('relative-time::attr(datetime)').get() or \
                           repo.css('time-ago::attr(datetime)').get()
            
            if last_updated:
                try:
                    last_updated = datetime.datetime.fromisoformat(
                        last_updated.replace('Z', '+00:00')
                    ).strftime('%Y-%m-%d')
                except:
                    last_updated = "Unknown"
            
            # Check if repo is empty
            is_empty = 'This repository is empty' in repo.get() if repo.get() else False
            
            repo_data = {
                'url': repo_url,
                'name': repo_name,
                'about': about,
                'last_updated': last_updated,
                'is_empty': is_empty,
            }
            
            if not is_empty:
                self.logger.info(f"Following repository: {repo_url}")
                yield scrapy.Request(
                    url=repo_url,
                    callback=self.parse_repository_details,
                    meta={'repo_data': repo_data}
                )
            else:
                repo_data['languages'] = ['None']
                repo_data['commits'] = '0'
                self.repositories.append(repo_data)
        
        # Check for pagination
        next_page = response.css('a.next_page::attr(href), a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_repository_details(self, response):
        repo_data = response.meta['repo_data']
        self.logger.info(f"Parsing details for: {response.url}")
        
        # Extract languages by file extensions (simplified)
        languages = []
        file_names = response.css('span.text-mono::text').getall()
        if file_names:
            extensions = set()
        for filename in file_names:
            if '.' in filename:
                ext = filename.split('.')[-1].strip().upper()
            if ext and len(ext) <= 5:
                extensions.add(ext)
            languages = list(extensions) if extensions else ['None']
        else:
            languages = ['None']
    
            repo_data['languages'] = languages
            self.logger.info(f"Languages found: {languages}")
        
        commits_text = response.css('a[href*="commits"] span::text, span.d-none.d-sm-inline::text').get()
        if commits_text and re.search(r'\d+', commits_text):
            commit_count = re.search(r'(\d+[,\d]*)', commits_text).group(1).replace(',', '')
            repo_data['commits'] = commit_count
        else:
            repo_data['commits'] = '0'

    def closed(self, reason):
        self.logger.info(f"Collected {len(self.repositories)} repositories")
        root = Element('repositories')

        for repo in self.repositories:
            repo_elem = SubElement(root, 'repository')

            SubElement(repo_elem, 'url').text = repo.get('url') or 'None'
            SubElement(repo_elem, 'about').text = repo.get('about') or 'None'
            SubElement(repo_elem, 'last_updated').text = repo.get('last_updated') or 'None'

            langs_elem = SubElement(repo_elem, 'languages')
            languages = repo.get('languages') or ['None']
            for lang in languages:
                lang_el = SubElement(langs_elem, 'language')
                lang_el.text = lang

            SubElement(repo_elem, 'commits').text = repo.get('commits') or 'None'

        xml_str = tostring(root, encoding='utf-8')
        pretty_xml = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")

        with open(f"{self.github_username}_repositories.xml", "w", encoding="utf-8") as f:
            f.write(pretty_xml)

        self.logger.info(f"Saved data to {self.github_username}_repositories.xml")
