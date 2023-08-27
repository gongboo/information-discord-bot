import time
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import os
from dotenv import load_dotenv
import json
import xml.etree.ElementTree as ET
import yake

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@bot.command()
async def echo(ctx, say):
    await ctx.send(say)


@bot.command()
async def generate_wordcloud(ctx, url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    text = soup.get_text()
    # print(text)

    # 한글 폰트 깨져서 경로 지정
    font_path = 'assets/NotoSansKR-VariableFont_wght.ttf'

    wc = WordCloud(font_path=font_path, background_color="white",
                   width=800, height=600).generate(text)

    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')

    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='PNG')
    img_bytes.seek(0)

    await ctx.send(file=discord.File(img_bytes, 'wordcloud.png'))


def save_links_to_json(links, json_file_path):
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(links, f, ensure_ascii=False, indent=4)


def load_links_from_json(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@bot.command()
async def add_link(ctx, link):
    existing_links = load_links_from_json("favorite_links.json")

    existing_links["favorite_links"].append(link)

    save_links_to_json(existing_links, "favorite_links.json")

    await ctx.send(f"Added new link: {link}")


@bot.command()
async def show_links(ctx):
    existing_links = load_links_from_json("favorite_links.json")

    links_text = "\n".join(existing_links["favorite_links"])

    await ctx.send(f"Here are your favorite links:\n{links_text}")


@bot.command()
async def show_saved_topic_links(ctx):
    data = load_links_from_json("found_data.json")

    for datum in data:
        txt = ""
        txt += datum["title"]+"\n"
        txt += datum["link"]+"\n"+"\n"
        await ctx.send(f"Here are your titles links:\n{txt}")
        time.sleep(1)


def getKeyword(text):
    # 키워드 추출 : yake
    language = "en"
    max_ngram_size = 3
    deduplication_threshold = 0.9
    num_of_keywords = 20

    custom_kw_extractor = yake.KeywordExtractor(
        lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, top=num_of_keywords, features=None)

    keywords = custom_kw_extractor.extract_keywords(text)

    lst = []
    for kw in keywords:
        lst.append(kw[0])

    return lst


@bot.command()
async def add_contents(ctx):
    existing_links = load_links_from_json("favorite_links.json")
    print(existing_links["favorite_links"])

    for link in existing_links["favorite_links"]:
        print(link)
        if ("https://www.reddit.com/" in link):  # 링크가 레딧일 경우
            print("the link is reddit")
            try:
                # 헤더 429에러 때문에 변경
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(link, headers=headers)

                if response.status_code == 200:
                    rss_content = response.text

                    # XML 파싱
                    root = ET.fromstring(rss_content)
                    namespace = {'ns': 'http://www.w3.org/2005/Atom'}

                    entry_data = []
                    for entry in root.findall('ns:entry', namespace):
                        title = entry.find('ns:title', namespace).text
                        content = entry.find('ns:content', namespace).text
                        link = entry.find('ns:link', namespace).attrib['href']
                        entry_data.append({
                            "title": title,
                            "content": content,
                            "link": link,
                            "keywords": getKeyword(content)
                        })
                        with open('found_data.json', 'w') as json_file:
                            json.dump(entry_data, json_file, indent=4)

            except Exception as e:
                print(f"An error occurred: {e}")
            time.sleep(10)
        else:
            print("not made yet")


bot.run(TOKEN)
