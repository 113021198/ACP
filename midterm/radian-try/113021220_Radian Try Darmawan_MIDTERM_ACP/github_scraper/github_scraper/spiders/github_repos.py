import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import datetime
import xml.dom.minidom
from xml.etree.ElementTree import Element, SubElement, tostring
import re


class GitHubSpider(scrapy.Spider):
    name = 'github_repos'
    github_username = 'radiandrmwn'

    start_urls = [f'https://github.com/{github_username}?tab=repositories']
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repositories = []

    def parse(self, response):
        repositories = response.css('li[itemprop="owns"]')
        self.logger.info(f"Found {len(repositories)} repositories")

        for repo in repositories:
            repo_url = response.urljoin(repo.css('a[itemprop="name codeRepository"]::attr(href)').get())
            repo_name = repo.css('a[itemprop="name codeRepository"]::text').get().strip()

            about = repo.css('p[itemprop="description"]::text').get()
            if about:
                about = about.strip()

            last_updated = repo.css('relative-time::attr(datetime)').get()
            if last_updated:
                last_updated = datetime.datetime.fromisoformat(
                    last_updated.replace('Z', '+00:00')
                ).strftime('%Y-%m-%d')

            is_empty = 'This repository is empty.' in repo.get()

            if not about and not is_empty:
                about = repo_name

            repo_data = {
                'url': repo_url,
                'name': repo_name,
                'about': about,
                'last_updated': last_updated,
                'is_empty': is_empty,
            }

            if not is_empty:
                yield scrapy.Request(
                    url=repo_url,
                    callback=self.parse_repository_details,
                    meta={'repo_data': repo_data}
                )
            else:
                repo_data['languages'] = None
                repo_data['commits'] = None
                self.repositories.append(repo_data)

        next_page = response.css('a.next_page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_repository_details(self, response):
        repo_data = response.meta['repo_data']

        # Languages
        lang_data = response.css('.repository-content .Layout-sidebar span[itemprop="programmingLanguage"]::text').getall()
        if not lang_data:
            lang_data = ['None']
        repo_data['languages'] = lang_data

        # Commits
        commits_text = response.css('li.Commits .d-none.d-sm-inline::text').get()
        if commits_text:
            commits = re.search(r'(\d+)', commits_text)
            repo_data['commits'] = commits.group(1) if commits else '0'
        else:
            repo_data['commits'] = '0'

        self.repositories.append(repo_data)

    def closed(self, reason):
        self.logger.info(f"Collected {len(self.repositories)} repositories")
        root = Element('repositories')

        for repo in self.repositories:
            repo_elem = SubElement(root, 'repository')

            SubElement(repo_elem, 'url').text = repo['url']
            SubElement(repo_elem, 'about').text = repo['about'] or 'None'
            SubElement(repo_elem, 'last_updated').text = repo['last_updated'] or 'None'

            langs_elem = SubElement(repo_elem, 'languages')
            if repo['languages']:
                for lang in repo['languages']:
                    lang_el = SubElement(langs_elem, 'language')
                    lang_el.text = lang

            SubElement(repo_elem, 'commits').text = repo['commits'] or 'None'

        xml_str = tostring(root, encoding='utf-8')
        pretty_xml = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")

        with open(f"{self.github_username}_repositories.xml", "w", encoding="utf-8") as f:
            f.write(pretty_xml)

        self.logger.info(f"Saved data to {self.github_username}_repositories.xml")
