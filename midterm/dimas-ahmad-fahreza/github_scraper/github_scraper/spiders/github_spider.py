import scrapy

class MyGithubRepoSpider(scrapy.Spider):
    name = "github_spider"
    allowed_domains = ["github.com"]
    start_urls = ["https://github.com/dimasfahrza?tab=repositories"]

    custom_settings = {
        'FEED_FORMAT': 'xml',
        'FEED_URI': 'my_github_output.xml',
        'FEED_EXPORT_ENCODING': 'utf-8',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1.5,
        'CONCURRENT_REQUESTS': 1,
    }

    def parse(self, response):
        self.logger.info(f"🔍 Looking through: {response.url}")

        repo_blocks = response.css('li[itemprop="owns"], div.Box-row, div[data-test-id="repository-list-item"]')

        for block in repo_blocks:
            repo_href = block.css('a[itemprop="name codeRepository"]::attr(href)').get() \
                        or block.css('a[data-test-id="repository-link"]::attr(href)').get()
            repo_url = response.urljoin(repo_href) if repo_href else None

            repo_name = (block.css('a[itemprop="name codeRepository"]::text').get() or
                         block.css('a[data-test-id="repository-link"]::text').get() or "").strip()

            repo_about = block.css('p[itemprop="description"]::text').get() \
                        or block.css('p[data-test-id="repository-description"]::text').get()
            repo_about = repo_about.strip() if repo_about else repo_name

            last_edit_time = block.css('relative-time::attr(datetime)').get()

            scraped_data = {
                'url': repo_url,
                'about': repo_about,
                'last_updated': last_edit_time
            }

            if repo_url:
                yield response.follow(
                    repo_url,
                    callback=self.parse_repo_details,
                    meta={'repo_data': scraped_data}
                )
            else:
                scraped_data.update({'languages': None, 'commits': None})
                yield scraped_data

    def parse_repo_details(self, response):
        repo_data = response.meta['repo_data']
        self.logger.info(f"➡️  Entering repo: {repo_data['url']}")

        is_repo_empty = bool(response.css('.blankslate, .BlankState'))

        if is_repo_empty:
            repo_data.update({'languages': None, 'commits': None})
        else:
            # Get all programming languages used
            lang_items = response.css('li.d-inline span::text').getall()
            langs = [lang.strip() for lang in lang_items if lang.strip()]
            repo_data['languages'] = langs if langs else None

            # Try to get commit count
            commit_text = response.css('a[href*="commits"] span::text').get() \
                        or response.css('strong[data-test-id="commits"]::text').get()

            if commit_text:
                commit_count = commit_text.strip().replace(",", "")
                if "Commit" not in commit_count:
                    commit_count += " Commits"
                repo_data['commits'] = commit_count
            else:
                repo_data['commits'] = "None"

        yield repo_data
