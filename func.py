import io
import json

from fdk import response

import requests
from bs4 import BeautifulSoup
import pandas


def handler(ctx, data: io.BytesIO=None):
    ans = getWeather()
    return response.Response(
        ctx, response_data=json.dumps(ans),
        headers={"Content-Type": "application/json"}
    )

def getWeather():
    page = requests.get("https://weather.com/weather/hourbyhour/l/7472a7bbd3a7454aadf596f0ba7dc8b08987b1f7581fae69d8817dffffc487c2")
    content = page.content
    soup = BeautifulSoup(content, "html.parser")
    l = []
    all = soup.find("div", {"class": "locations-title hourly-page-title"}).find("h1").text

    table = soup.find_all("table", {"class": "twc-table"})

    for items in table:
        for i in range(len(items.find_all("tr")) - 1):
            d = {}
            try:
                d["desc"] = items.find_all("td", {"class": "description"})[i].text
                d["temp"] = items.find_all("td", {"class": "temp"})[i].text
            except:
                d["desc"] = "None"
                d["temp"] = "None"
            l.append(d)

    df = pandas.DataFrame(l)

    resp0nse = "It is " + df.at[0, "desc"] + ". The temperature is " + df.at[0, "temp"]

    return resp0nse