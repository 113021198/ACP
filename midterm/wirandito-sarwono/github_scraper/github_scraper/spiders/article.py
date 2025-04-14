import scrapy
from datetime import datetime
from urllib.parse import urljoin

class GithubSpider(scrapy.Spider):
    name = 'github_spider'
    start_urls = ['https://github.com/dimasfahrza?tab=repositories']
    
    def parse(self, response):
        repo_links = response.css('a[itemprop="name codeRepository"]::attr(href)').getall()
        
        for repo in repo_links:
            repo_url = urljoin('https://github.com', repo)
            yield scrapy.Request(repo_url, callback=self.parse_repo)
            
        next_page = response.css('a.next_page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
    
    def parse_repo(self, response):
        repo_name = response.css('strong[itemprop="name"] a::text').get().strip()
        about = response.css('p[itemprop="description"]::text').get()
        
        if not about or about.strip() == '':
            is_empty = response.css('div.BlobToolbar + div:contains("Empty repository")').get() is not None
            if not is_empty:
                about = repo_name
            else:
                about = None
        
        last_updated = response.css('relative-time::attr(datetime)').get()
        if last_updated:
            last_updated = datetime.strptime(last_updated, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
        
        languages = None
        commits_count = None
        
        is_empty = response.css('div.BlobToolbar + div:contains("Empty repository")').get() is not None
        if not is_empty:
            languages = response.css('span[itemprop="programmingLanguage"]::text').getall()
            if not languages:
                languages = response.css('a[href*="search?l="]::text').getall()
            languages = [lang.strip() for lang in languages if lang.strip()] or None
            
            commits_url = urljoin(response.url, 'commits/master')
            yield scrapy.Request(commits_url, 
                              callback=self.parse_commits,
                              meta={
                                  'repo_name': repo_name,
                                  'about': about,
                                  'last_updated': last_updated,
                                  'languages': languages
                              })
        else:
            yield {
                'url': response.url,
                'about': about,
                'last_updated': last_updated,
                'languages': None,
                'commits_count': None
            }
    
    def parse_commits(self, response):  # Fixed typo here (was parse_commits)
        commits_count = response.css('a[href*="commits"] span::text').get()
        if commits_count:
            commits_count = commits_count.strip().replace(',', '')
            try:
                commits_count = int(commits_count)
            except ValueError:
                commits_count = None
        
        yield {
            'url': response.url.replace('/commits/master', ''),
            'about': response.meta['about'],
            'last_updated': response.meta['last_updated'],
            'languages': response.meta['languages'],
            'commits_count': commits_count
        }