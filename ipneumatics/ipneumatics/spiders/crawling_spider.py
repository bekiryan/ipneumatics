from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy import Request
import requests


class CrawlingSpider(CrawlSpider):
    name = "mycrawler"
    allowed_domains = ["ipneumatics.com"]
    start_urls = ["https://www.ipneumatics.com/IW-1--4INCH_c_836.html"]

    rules = (
        Rule(LinkExtractor(allow="https://www.ipneumatics.com/IW-1--4INCH_c_836.html"), callback="parse_page"),
    )

    def parse_page(self, response):
        product_links = response.xpath("//input[@type='button']//../../../../../../..//a/@href").getall()
        for product_link in product_links:
            yield response.follow(product_link, callback=self.parse_item)

        next_page = response.xpath('//a[contains(text(), "Next Page")]/@href').get()
        if next_page:
            next_page_url = response.urljoin(next_page)
            yield Request(next_page_url, callback=self.parse_page)

    def parse_item(self, response):
        item_name = response.css("h1::text").get()
        price = str(response.css(".price::text").get()).replace("\n", "")
        image_link = self.get_image_link(response)
        description = self.get_description(response)
        serial_number = response.css("#product_id::text").get()
        print("serial_number", serial_number)

        if image_link:
            yield Request(image_link, callback=self.download_image, cb_kwargs={"image_name": serial_number})

        yield {
            "item_name": item_name,
            "price": price,
            "description": description,
            "serial_number": serial_number,
            "image_link": image_link,
            "item_link": response.request.url
        }
    # def download_image(self, response, link, image_name):
    #     img_data = response.xpath("//*[@id='listing_main_image_link']/@href")
    #     with open(f'/home/ubuntu/PycharmProjects/scrap_web/ipneumatics/images/{image_name}.jpg', 'wb') as handler:
    #         handler.write(img_data)

    def download_image(self, response, image_name):
        if response.status == 200:
            file_path = f'/home/ubuntu/PycharmProjects/scrap_web/ipneumatics/images/{image_name}.jpg'  # Replace with the actual file path
            with open(file_path, 'wb') as file:
                file.write(response.body)

    def get_image_link(self, response):
        try:
            return "https://www.ipneumatics.com/" + response.xpath("//*[@id='listing_main_image_link']/@href").get()
        except Exception:
            return None
    def get_description(self, response):
        try:
            description_table = response.xpath("//td[contains(text(),' Description')]/../../tr")[-3]
        except Exception:
            description_table = None

        try:
            SMC_talbe = response.xpath("//td[contains(text(),' Description')]/../../tr")[-2].xpath(
                ".//td[@class=\"item\"]/text()").getall()
        except Exception:
            SMC_talbe = None

        if SMC_talbe is not None:
            if len(SMC_talbe) == 0:
                SMC_talbe = [None] * 7

        if description_table or SMC_talbe:
            return {
                "description": description_table.xpath(".//div[@itemprop=\"description\"]/p/text()").get(),
                "items": description_table.xpath(".//div[@itemprop=\"description\"]/ul/li/text()").getall(),
                "part_description": SMC_talbe[1],
                "products_line": SMC_talbe[2],
                "family": SMC_talbe[3],
                "family_code": SMC_talbe[4],
                "class_description": SMC_talbe[5],
                "weight": SMC_talbe[6],

            }
        return None

