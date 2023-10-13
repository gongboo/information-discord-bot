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
import openai
import feedparser

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
openai.api_key = os.getenv("GPT_KEY")

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
async def wordcloud(ctx, url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text()

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
async def delete_link(ctx, idx):
    existing_links = load_links_from_json("favorite_links.json")
    tmp = existing_links["favorite_links"].pop(int(idx))
    save_links_to_json(existing_links, "favorite_links.json")
    await ctx.send(f"deleted link: {tmp}")


@bot.command()
async def show_links(ctx):
    existing_links = load_links_from_json("favorite_links.json")
    links_text = "\n".join(existing_links["favorite_links"])
    await ctx.send(f"Here are your favorite links:\n{links_text}")


@bot.command()
async def show_contents(ctx):
    data = load_links_from_json("found_data.json")

    txt = ""
    for i, datum in enumerate(data):
        next_link = datum["title"]+" [link](<"+datum["link"]+">)\n"
        if (len(txt)+len(next_link) < 1000):
            txt += next_link
        elif (len(txt)+len(next_link) >= 1000):
            await ctx.send(txt, embed=None)
            txt = ""
            txt += next_link


async def call_gpt(text):
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo-0613",
        messages=[
            {
                "role": "system",
                "content": "Please categorize posts based on their topics, using the number before '::-' as the ID. When parsing IDs, utilize '::-'. If a post doesn't fit any current topic, establish a new one. Only display topics with associated posts and omit those unrelated to development. Newly created topics should have emojis prefixed. For concise responses, provide only the IDs and avoid using double line breaks like '\n\n'. Also don't say any additional comments"
            },
            {
                "role": "user",
                "content": "current topics:\n1::-NoSQL Databases\n2::-🎨 Front-end Frameworks\n3::-🖥️ Back-end Development\n4::-모바일 앱 개발\n\ncurrent posts:\n3::-An In-depth Guide to Bootstrap 5 Features and Components\n4::-Tailwind CSS: Rapid UI Development with Utility-first Design\n5::-Advanced Animations with GSAP: Breathing Life into Web Elements\n7::-Node.js Performance Tuning: Best Practices for Large-scale Applications\n8::-Understanding Django ORM: Efficient Database Management\n9::-From Monolith to Microservices: Transitioning with Spring Boot\n52::-Setting up Jenkins Pipelines for Automated Deployment\n53::-Travis CI vs. CircleCI: A Comparative Analysis\n54::-Automating Deployment with GitLab CI/CD"
            },
            {
                "role": "assistant",
                "content": "2::-3,4,5\n3::-7,8,9\n🚀 Continuous Integration/Continuous Deployment (CI/CD)::-52,53,54"
            },
            {
                "role": "user",
                "content": "current topics:\n1::-🗃️ NoSQL Databases\n2::-🎨 Front-end Frameworks\n3::-🖥️ Back-end Development\n\ncurrent posts:\n10::-MongoDB Optimization Techniques for Large-scale Data\n11::-Vue.js 3: A Comprehensive Introduction\n12::-How to make a strawberry cake\n13::-Node.js vs. Deno: A Performance Breakdown\n14::-CSS Grid: Creating Responsive Layouts\n15::-AWS Lambda: Building Serverless Applications\n16::-The Rise of Progressive Web Apps in 2023"
            },
            {
                "role": "assistant",
                "content": "1::-10\n2::-11,14,16\n3::-13\n☁️ Serverless Architectures::-15"
            },
            {
                "role": "user",
                "content": "current topics:\n1::-☁️ Cloud Computing\n2::-🤖 AI & Machine Learning\n\ncurrent posts:\n80::-Deep Reinforcement Learning in Video Games\n81::-Deploying a Scalable Web Application on AWS\n82::-Best Practices in Mobile App UI Design\n83::-Introduction to Cryptocurrencies and Blockchain\n84::-Creating Interactive Visualizations with D3.js\n85::-The Role of Edge Computing in IoT\n86::-Dogs playing in playground"
            },
            {
                "role": "assistant",
                "content": "1::-81,85\n2::-80\n📱 Mobile App Design::-82\n💰 Blockchain & Cryptocurrencies ::- 83\n📊 Data Visualization ::- 84\n🌐 Edge & IoT::- 85"
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    # print(response)
    gpt_answer = response.choices[0].message.content
    return gpt_answer if gpt_answer != None else "error"


@bot.command()
async def call(ctx):
    topics_and_posts = {1: []}
    posts_dict = dict()
    posts_link_dict = dict()

    topics_dict = {1: "🤖 AI & Machine Learning"}
    topics = ""
    posts = ""
    posts_list = []
    count = 1

    data = load_links_from_json("found_data.json")

    for i, datum in enumerate(data):
        posts_dict[i+1] = datum["title"]
        posts_link_dict[i+1] = datum["link"]
        next_link = str(i+1)+"::-"+datum["title"]+"\n"
        posts += next_link
        if (i+1) % 30 == 0:
            posts_list.append(posts)
            posts = ""
    posts_list.append(posts)
    # print(posts_list)
    for post_dump in posts_list:
        topics = ""
        # print("topics_dict: ", topics_dict)
        for idx in range(len(topics_dict)):
            topics += str(idx+1)+"::-"+topics_dict[idx+1]+"\n"
        text = "current topics:\n" + topics + "current posts:\n"+post_dump
        print(text)
        gpt_answer = await call_gpt(text)

        print("gpt_answer: ", gpt_answer)
        lst = gpt_answer.split("\n")
        for ans in lst:
            try:
                topic = ans.split("::-")[0].strip()
                posts = list(map(int, ans.split("::-")[1].strip().split(",")))
                if topic.isdigit():  # 이미 있던 주제일 경우
                    topics_and_posts[int(topic)] += posts
                else:  # 새로운 주제일 경우
                    cur_id = len(topics_dict)+1
                    topics_dict[cur_id] = topic
                    # cur_id += 1
                    topics_and_posts[cur_id] = posts
            except:
                print("error occurred")

    txt = ""
    for item in topics_and_posts:

        txt += "### "+topics_dict[item]+"\n"
        print(item, topics_dict[item])
        for post in topics_and_posts[item]:
            if len(txt) > 500:
                await ctx.send(txt, embed=None)
                txt = ""
            txt += posts_dict[post]+" [link](<"+posts_link_dict[post]+">)\n"
            print(" ", posts_dict[post])
    if len(txt) > 0:
        await ctx.send(txt, embed=None)


def get_keyword(text):
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
async def refresh_contents_feedparser(ctx):  # 테스트 안함
    with open('found_data.json', 'w') as json_file:
        json.dump([], json_file, indent=4)

    existing_links = load_links_from_json("favorite_links.json")
    found_data = load_links_from_json("found_data.json")
    for i, fav_link in enumerate(existing_links["favorite_links"]):
        await ctx.send(str(i) + "번째 링크 작업을 시작했습니다")
        feed = feedparser.parse(fav_link)
        for i in range(len(feed.entries)):
            if hasattr(feed.entries[i], 'published'):
                time = feed.entries[i].published
            elif hasattr(feed.entries[i], 'updated'):
                time = feed.entries[i].updated
            else:
                time = 'Not Available'
            title = feed.entries[i].title if hasattr(
                feed.entries[i], 'title') else 'Not Available'
            if hasattr(feed.entries[i], 'description'):
                content = feed.entries[i].description
            elif hasattr(feed.entries[i], 'summary'):
                content = feed.entries[i].summary
            else:
                content = 'Not Available'
            link = feed.entries[i].link if hasattr(
                feed.entries[i], 'link') else 'Not Available'
            # Assuming get_keyword is a function you've defined
            keywords = get_keyword(content)

            found_data.append({
                "title": title,
                "content": content,
                "link": link,
                "time": time,
                "keywords": keywords
            })
            with open('found_data.json', 'w') as json_file:
                json.dump(found_data, json_file, indent=4)


bot.run(TOKEN)
