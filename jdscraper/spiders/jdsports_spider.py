import scrapy

class JDSportsSpider(scrapy.Spider):
    name = "jdsports"
    start_urls = ["https://www.jdsports.it/saldi/"]

    def parse(self, response):
        for product in response.css("span.itemContainer"):
            name = product.css("span.itemTitle a::text").get()
            priceWasText = product.css("span.was span::text").get()
            priceIsText = product.css("span.now span::text").get()

            if not priceWasText or not priceIsText:
                continue

            try:
                priceWas = float(priceWasText.replace("€", "").replace(",", ".").strip())
                priceIs = float(priceIsText.replace("€", "").replace(",", ".").strip())
            except ValueError:
                continue

            discount = round((priceWas - priceIs) * 100 / priceWas, 0)
            difference = priceWas - priceIs
            link = response.urljoin(product.css("a.itemImage").attrib.get("href", ""))
            image = response.urljoin(product.css("img.thumbnail").attrib.get("src", ""))

            yield {
                "name": name,
                "priceWas": priceWas,
                "priceIs": priceIs,
                "difference": difference,
                "discount": discount,
                "link": link,
                "image": image,
            }

        next_page = response.css("a.btn.btn-default.pageNav[rel='next']::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)
