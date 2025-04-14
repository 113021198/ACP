import scrapy
import datetime
import re
import json

class GithubSpider(scrapy.Spider):
    name = 'github'
    allowed_domains = ['github.com']
    start_urls = ['https://github.com/DitoNewJeans?tab=repositories']
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'LOG_LEVEL': 'DEBUG'
    }

    def start_requests(self):
        self.logger.info(f"Starting crawl with URL: {self.start_urls[0]}")
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Debug information
        self.logger.info(f"Response URL: {response.url}")
        self.logger.info(f"Response status: {response.status}")
        
        repos_found = False
        
        #sel 1
        repos = response.css('div[id="user-repositories-list"] li')
        if repos:
            self.logger.info(f"Found {len(repos)} repositories with selector 1")
            repos_found = True
            
            for repo in repos:
                name_element = repo.css('h3 a::text').get()
                if name_element:
                    name = name_element.strip()
                    url = response.urljoin(repo.css('h3 a::attr(href)').get())
                    
                    about = None
                    about_selectors = [
                        'p.color-fg-muted.mb-0::text',
                        'p.color-text-secondary.mb-0::text',
                        'p[itemprop="description"]::text',
                        'div.py-1 p::text',
                        'p.wb-break-word.text-small.mt-2.mb-0::text'
                    ]
                    
                    for selector in about_selectors:
                        about = repo.css(selector).get()
                        if about:
                            about = about.strip()
                            break
                    
                    if not about:
                        about = "No description"
                    
                    last_updated = repo.css('relative-time::attr(datetime)').get()
                    if last_updated:
                        last_updated = datetime.datetime.fromisoformat(last_updated.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                    else:
                        last_updated = "Not specified"
                        
                    is_empty = 'test empty repo' in repo.get()
                    
                    self.logger.info(f"Found repository: {name}")
                    
                    #page details
                    repo_data = {
                        'name': name,
                        'url': url,
                        'about': about,
                        'last_updated': last_updated,
                        'is_empty': is_empty
                    }
                    
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_repository_details,
                        meta={'repo_data': repo_data}
                    )
        
        #sel 2
        if not repos_found:
            repos = response.css('div[class*="repo-list"] div[class*="repo-list-item"]')
            if repos:
                self.logger.info(f"Found {len(repos)} repositories with selector 2")
                repos_found = True
                
                for repo in repos:
                    name_element = repo.css('a[itemprop="name codeRepository"]::text').get()
                    if name_element:
                        name = name_element.strip()
                        url = response.urljoin(repo.css('a[itemprop="name codeRepository"]::attr(href)').get())
                        
                        about = None
                        about_selectors = [
                            'p[itemprop="description"]::text',
                            'div.py-1 p::text',
                            'p.wb-break-word::text',
                            'p.color-fg-muted::text',
                            'p.color-text-secondary::text'
                        ]
                        
                        for selector in about_selectors:
                            about = repo.css(selector).get()
                            if about:
                                about = about.strip()
                                break
                        
                        if not about:
                            about = "No description"
                        
                        self.logger.info(f"Found repository: {name}")
                        
                        repo_data = {
                            'name': name,
                            'url': url,
                            'about': about,
                            'last_updated': 'Not specified',
                            'is_empty': False
                        }
                        
                        yield scrapy.Request(
                            url=url,
                            callback=self.parse_repository_details,
                            meta={'repo_data': repo_data}
                        )
        
        #handle no repo
        if not repos_found:
            self.logger.warning("no repositories found with any selector")
            page_sample = response.css('body').extract_first()
            if page_sample and "doesn't have any public repositories yet" in page_sample:
                self.logger.info("no public repo")
                yield {
                    'message': "github acc no repo"
                }
        
        next_page = response.css('a.next_page::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)

    def parse_repository_details(self, response):
        repo_data = response.meta['repo_data']
        
        #check repo
        is_empty = 'This repository is empty' in response.text
        repo_data['is_empty'] = is_empty
        
        if is_empty:
            repo_data['languages'] = None
            repo_data['commits'] = None
            self.logger.info(f"Empty repository: {repo_data['name']}")
            
            standardized_output = {
                'name': repo_data['name'],
                'url': repo_data['url'],
                'about': repo_data['about'],
                'last_updated': repo_data['last_updated'],
                'languages': None,
                'commits': None
            }
            
            self.logger.info(f"Repository {repo_data['name']} is empty - settings languages and commits to None")
            yield standardized_output
            return
        
        #langs format
        langs = []
        language_elements = response.css('div.repository-lang-stats-graph span.language-color::attr(aria-label)').getall()
        
        for lang_text in language_elements:
            if lang_text and " " in lang_text:
                lang_name = lang_text.split(" ")[0]
                langs.append(lang_name)
        
        #lg
        if not langs:
            lang_elements = response.css('a[href*="search?l="] span::text').getall()
            langs = [lang.strip() for lang in lang_elements if lang.strip()]
        
        languages = ", ".join(langs) if langs else "None"
        repo_data['languages'] = languages
        
        #commit
        commits = None
        commit_texts = response.css('a[href*="commits"] span::text').getall()
        for text in commit_texts:
            match = re.search(r'\d+', text)
            if match:
                commits = match.group(0)
                break
        
        repo_data['commits'] = commits if commits else '0'
        
        #output
        standardized_output = {
            'name': repo_data['name'],
            'url': repo_data['url'],
            'about': repo_data['about'],
            'last_updated': repo_data['last_updated'],
            'languages': repo_data['languages'],
            'commits': repo_data['commits']
        }
        
        self.logger.info(f"Repository details: {repo_data['name']}")
        yield standardized_output