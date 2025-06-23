import scrapy

class TrackSaveCrawler(scrapy.Spider):
    name = 'track_save_crawler'

    def __init__(self, url=None, *args, **kwargs):
        super(TrackSaveCrawler, self).__init__(*args, **kwargs)
        if not url:
            raise ValueError("A URL precisa ser passada com -a url='sua_url'")
        self.start_urls = [url]
        self.target_url = url.lower()  # Facilita o uso nas condições do parse

    def parse(self, response):

        if 'amazon' in self.target_url:
            for num,r in enumerate (response.css('a.s-no-outline')):
                url = r.css('::attr(href)').get()
                txt = r.css('img::attr(alt)').get()
                preco = response.css("span.a-price span.a-offscreen::text")[num].get()
                nota = response.css('span.a-icon-alt::text')[num].get()[:3]

                yield {
                    'url': 'https://www.amazon.com.br' + url if url else '',
                    'name': txt,
                    'price': preco,
                    'rating': nota
                }

