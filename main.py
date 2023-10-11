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
async def possible_sites(ctx):
    await ctx.send("현재 가능한 사이트는 reddit 입니다")


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


def get_text_for_gpt():
    data = load_links_from_json("found_data.json")
    total_txt = ""
    for i, datum in enumerate(data):
        next_link = str(i+1)+":"+datum["title"]+"\n"
        total_txt += next_link
    return total_txt


def callGPT(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
              "role": "system",
              "content": "Please categorize the post titles based on their general themes or subjects, and also provide a title for each category. Additionally, indicate the number of titles included in each category. Also please exclude categories and titles which are not related to computer science or technology.\n\nFor example like this:\npython basics: 1,4,8,12\nflutter news: 3,5"
            },
            {
                "role": "user",
                "content": "1:Hello! Does anyone here actively play the game Flutter: Starlight or would be willing to play it with me?\n2:Random heart flutter freaked me out And now I’m having frequent heart palpitations.\n3:Flutter Mane and Misdreavus upside down are another thing link\nPlaying Heavensward and Aymeric & Estinien make my heart flutter… I’m a straight guy!\n4:🔥 Butterflies Fluttering Around A Turtle\n5:TIL In 1994, in an attempt to ban raves, the UK passed a law banning public performance of music “wholly or predominantly characterized by the emission of a succession of repetitive beats.” In response, the electronic band Autechre issued a track, Flutter, in which no two bars have the same beat.\n6:Flutter by\n7:🔥 Butterflies fluttering around a turtle\nCan anyone identify this flag? And also tell me why it makes my heart flutter?\n8:Aeroelastic flutter\n9:[Ducker] Whatever your opinions on Pogba/his situation with United, I’d argue that no matter who the player the nerve to start fluttering eyelashes at another club days after your team have been stuffed 6-1 at home really isn’t a good look\n10:I’m an RN. My wife is an RN. I was just hospitalized for 2 days due to new onset atrial flutter and a sustained heart rate of 140 bpm for over an hour. My wife decided to update the whiteboard as a test. No one used my “preferred name” or mentioned it. Surprise.\n11:Theorymon: Upside-Down Flutter Mane\n12:“Atomic Habits” and Learning to Code: Identity and Beliefs. link\n13:I need to automate CRM tasks with Javascript. Unsure where to begin. Please help!\n14:Javascript Prototype Expalined\n15:Print HTM With Their Styles\n16:Pass by Value in JavaScript | Pass by Reference - Scientech Easy\n17:i use chatgpt to learn python\n18:STOP USING PYTHON 😡😡😡\n19:My college roommate wrote a Python script to let RNG give him rewards when he finishes an assignment or gets up early (I told him he's crazy for this).\n20:Python programmers be like: \"Yeah that makes sense\" 🤔\n21:#2020 - Python Cowboy"
            },
            {
                "role": "assistant",
                "content": "Category 1: Flutter Game 🎮 - 1\nCategory 2: Music and Flutter Beat 🎵- 5 \nCategory 3: Javascript Learning and Tasks 💻 - 13, 14, 15, 16 \nCategory 4: Python Learning and Application 🐍 - 17, 18, 19\nCategory 5: Humor in Programming (Specifically Python) 😄 - 20, 21"
            },
            {
                "role": "user",
                "content": "1:Flutter app looks weird suddenly?\n2:What are these strange spacings beneath my TextFields?\n3:Servicenow/Salesforce or Flutter, which is good from a career perspective\n4:What do you think about Flutter Flow ?\n5:I want to learn Python but have no idea where to start.\n6Announcing Python in Excel: Combining the power of Python and the flexibility of Excel.\n7:Python coming to excel\n8:Microsoft is bringing Python to Excel\n9:‘Monty Python’ Star John Cleese Says ‘Life Of Brian’ Scene Won’t Be Cut Despite Modern Sensitivites\n10:Capturing a python\n11:🔥 Cane toads riding a giant python to escape rising flood waters in Australia\n12:Monty Python’s Eric Idle says he hates conservatives: ‘they’re horrible people’\n13:Contagious giggles at the mere mention of the name Biggus Dickus (from Monty Python's Life of Brian, 1979)\n14:I mad a python script the lets you scribble with SD in realtime\nSteve Irwin casually reacts on being bitten by a python on Live TV\nMonty Python and the Curse of the Nat 1."
            },
            {
                "role": "assistant",
                "content": "Category 1: Flutter App Development 📱 - 1,2,3,4\nCategory 2: Python Programming and Application 💻 - 5,6,7,8,14\nCategory 3: Monty Python Entertainment Series 🎥- 9,12,13"
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=1,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    gpt_answer = response.choices[0].message.content
    return gpt_answer if gpt_answer != None else "error"


@bot.command()
async def get_topics_from_gpt(ctx):
    text = get_text_for_gpt()
    gptText = callGPT(text)
    if gptText == "error":
        ctx.send("gpt call error")
        return
    tmp_list = gptText.split("\n")

    for i, item in enumerate(tmp_list):
        txt = ""
        position = item.rindex("-")
        category_text = item[:position]
        titles_text = item[position+1:]

        txt += "# "+category_text+"\n"

        tmp_list = titles_text.split(",")
        title_numbers = [int(x) for x in tmp_list]

        data = load_links_from_json("found_data.json")
        # print("len data :" , len(data))

        for num in title_numbers:
            # print(num)
            next_link = data[num-1]["title"] + \
                " [link](<"+data[num-1]["link"]+">)\n"
            if (len(txt)+len(next_link) < 1000):
                txt += next_link
            elif (len(txt)+len(next_link) >= 1000):
                await ctx.send(txt, embed=None)
                txt = ""
                txt += next_link
        if len(txt) > 0:
            await ctx.send(txt, embed=None)


def call_gpt(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Please classify the posts according to the topics. The number before '::-' is ID. Use '::-' when parsing with IDs. If a post doesn't fit into an existing topic, create a new one. Exclude topics that are not related to development. When you make new topic, add emojis in front of it. To make the answer short, you should answer only with IDs. don't use double enter like\n\n "
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
    gpt_answer = response.choices[0].message.content
    return gpt_answer if gpt_answer != None else "error"


@bot.command()
async def call(ctx):
    topics_and_posts = dict()
    posts_dict = dict()
    posts_link_dict = dict()

    topics_dict = dict()
    topics = ""
    posts = ""
    posts_list = []
    count = 1
    # for idx in topics_dict:
    #     topics += str(count)+"::-"+topics_dict[idx]+"\n"

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
    print(posts_list)
    for post_dump in posts_list:
        topics = ""
        print("topics_dict: ", topics_dict)
        for idx in range(len(topics_dict)):
            topics += str(idx+1)+"::-"+topics_dict[idx+1]+"\n"
        text = "current topics:\n"+topics+"current posts:\n"+post_dump
        print(text)
        gpt_answer = call_gpt(text)

        print(gpt_answer)
        lst = gpt_answer.split("\n")
        for ans in lst:
            topic = ans.split("::-")[0].strip()
            posts = list(map(int, ans.split("::-")[1].strip().split(",")))
            if len(topic) <= 1:  # 이미 있던 주제일 경우
                topics_and_posts[int(topic)] += posts
            else:  # 새로운 주제일 경우
                cur_id = len(topics_dict)+1
                topics_dict[cur_id] = topic
                # cur_id += 1
                topics_and_posts[cur_id] = posts
    txt = ""
    for item in topics_and_posts:

        txt += "### "+topics_dict[item]+"\n"
        print(item, topics_dict[item])
        for post in topics_and_posts[item]:
            if len(txt) > 500:
                await ctx.send(txt, embed=None)
                txt = ""
            txt += posts_dict[post]+" [link](<"+posts_link_dict[post]+">)\n"
            print(post, posts_dict[post])
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


@bot.command()
async def refresh_contents(ctx):
    with open('found_data.json', 'w') as json_file:
        json.dump([], json_file, indent=4)

    existing_links = load_links_from_json("favorite_links.json")
    found_data = load_links_from_json("found_data.json")
    for i, fav_link in enumerate(existing_links["favorite_links"]):
        await ctx.send(str(i) + "번째 링크 작업을 시작했습니다")
        if ("https://www.reddit.com/" in fav_link):  # 링크가 레딧일 경우
            print("the link is reddit")
            try:
                # 헤더 429에러 때문에 변경
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(fav_link, headers=headers)

                if response.status_code == 200:
                    rss_content = response.text

                    # XML 파싱
                    root = ET.fromstring(rss_content)
                    namespace = {'ns': 'http://www.w3.org/2005/Atom'}

                    for entry in root.findall('ns:entry', namespace):
                        title = entry.find('ns:title', namespace).text
                        content = entry.find('ns:content', namespace).text
                        published = entry.find('ns:published', namespace).text
                        link = entry.find('ns:link', namespace).attrib['href']
                        found_data.append({
                            "title": title,
                            "content": content,
                            "link": link,
                            "time": published,
                            "keywords": get_keyword(content)
                        })
                        with open('found_data.json', 'w') as json_file:
                            json.dump(found_data, json_file, indent=4)

            except Exception as e:
                print(f"An error occurred: {e}")
            time.sleep(5)
        else:
            print("not made yet")


bot.run(TOKEN)
