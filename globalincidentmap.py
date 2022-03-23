import requests
from scrapy.http import HtmlResponse
from datetime import datetime
from dateutil import parser
import json
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem


def get_useragent():
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=1000)
    return user_agent_rotator.get_random_user_agent()


class crawler:

    def map_severity(self, severity):
        svr = {"unknown": "0", "fair": "1", "moderate": "2", "severe": "3"}
        return svr[severity.lower()]

    def get_data(self, limit, since_date, until_date, geotag_url=None):
        dataa = list()
        try:
            results = dict()
            results["section"] = 'News'
            results["Links"] = list()
            payload = {}
            headers = {
                'User-Agent': get_useragent()
            }

            urls = ["http://human.globalincidentmap.com/", "http://drugs.globalincidentmap.com/",
                    "http://border.globalincidentmap.com/", "http://outbreaks.globalincidentmap.com/",
                    "http://hazmat.globalincidentmap.com/home.php"]
            for url in urls:
                request = requests.request("GET", url)
                response = HtmlResponse(url=url, body=request.content)
                dates = response.xpath('//*[@class="tdline"]/a/..//preceding-sibling::td/text()').getall()
                links = response.xpath('//*[@class="tdline"]/a/@href').getall()

                for date, link in zip(dates, links):
                    main_link = url.split(".com")[0] + ".com/" + link
                    date = date
                    article_date = parser.parse(date)
                    if article_date <= until_date and since_date <= article_date:
                        results["Links"].append(main_link)
                        request = requests.request("GET", main_link, headers=headers, data=payload)
                        response = HtmlResponse(url=main_link, body=request.content)

                        date = response.xpath("//*[contains(text(),'Date Time')]/..//following-sibling::td/text()").extract_first(default="")
                        lat = response.xpath("//*[contains(text(),'Latitude')]/..//following-sibling::td/text()").extract_first(default='')
                        long = response.xpath("//*[contains(text(),'Longitude')]/..//following-sibling::td/text()").extract_first(default="")
                        city = response.xpath("//*[contains(text(),'City')]/..//following-sibling::td/text()").extract_first(default="").strip()
                        eveent_type = response.xpath("//*[contains(text(),'Event Type')]/..//following-sibling::td/text()").extract_first(default="")
                        country = response.xpath("//*[contains(text(),'Country')]/..//following-sibling::td/text()").extract_first(default="")
                        eventName = city + "," + country + " - " + eveent_type
                        try:Severity = self.map_severity(response.xpath("//*[contains(text(),'Severity')]/..//following-sibling::td/text()").extract_first(default="").strip())
                        except:Severity = ""

                        final_data = {}
                        final_data['eventId'] = main_link.split("ID=")[-1]
                        final_data['eventName'] = eventName
                        final_data['eventDescription'] = "".join(
                            response.xpath('//*[@class="tdtext"]//text()').extract())
                        final_data['eventDate'] = str(date).strip().replace(' ', 'T') + 'Z'
                        final_data['newsUrl'] = response.xpath("//*[contains(text(),'URL')]/..//following-sibling::td/a/@href").extract_first()
                        final_data['Source'] = "GLOBALINCIDENTMAP"
                        final_data['severity'] = Severity
                        final_data['location'] = []
                        location = {}
                        location['geo:lat'] = lat
                        location['geo:long'] = long
                        final_data['location'].append(location)

                        final_data['locationTags'] = list()
                        final_data['locationTags'].append(city)
                        final_data['locationTags'].append(country)
                        final_data['category'] = "Terrorism"
                        final_data['subcategory'] = []
                        final_data['MediaUrls'] = []
                        final_data['_uniqueKeyFields'] = "__eventId_Md5Hash,__Source_Md5Hash"
                        if len(dataa) >= limit:
                            break
                        dataa.append(final_data)
                        print(json.dumps(final_data))

        except Exception as e:
            print(e)

        return dataa

if __name__ == '__main__':
    since = "2022-03-10T00:00:00Z"
    until = "2022-03-22T00:00:00Z"
    until = datetime.strptime(until.split("T")[0], "%Y-%m-%d") if until else datetime.now()
    since = datetime.strptime(since.split("T")[0], "%Y-%m-%d")
    crawler().get_data(limit = 1000,since_date=since, until_date=until)
