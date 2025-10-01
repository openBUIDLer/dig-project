from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel
import concurrent.futures

load_dotenv()
#
# api_key = os.getenv("PERPLEXITY_KEY")
#
# url = "https://api.perplexity.ai/chat/completions"
# headers = {
#     "Authorization": f'Bearer {api_key}',
#     "Content-Type": "application/json"
# }

client = OpenAI()

class EventSchema(BaseModel):
    name: str
    slug: str

class DigSchema(BaseModel):
    project_name: str
    project_description: str
    github_links: list[str]
    how_its_made: str
    image_links: list[str]
    video_links: list[str]
    event_details: EventSchema

def dig_project(start_digging: str):
    try:
        response = requests.request("GET", start_digging)
        soup = BeautifulSoup(response.text, "html.parser")
        all_scripts = soup.find_all("script")
        dig = None
        for script in all_scripts:
            if "fullUrl" in script.text:
                response = client.responses.parse(
                    model="gpt-4o-2024-08-06",
                    input=[
                        {
                            "role": "system", "content": "Extract the information as per the given schema."
                        },
                        {
                            "role": "user",
                            "content": script.text,
                        },
                    ],
                    text_format=DigSchema,
                )

                dig = response.output_parsed

        if dig is not None:
            print(f"lookup: {dig.project_name}")
            web_search = f'''
            {dig.project_name} - {dig.project_description}, do a deep research using this links: {','.join(dig.github_links)}, and respond in only json format, with any lookalike projects ( Plagiarised checker), total number of commits, average lines edited per commit.
            '''

            response = client.responses.create(
                model="gpt-5",
                tools=[{"type": "web_search"}],
                input=web_search
            )

            print(response.output_text)

    except Exception as error:
        print(error)

projects = open("projects.txt", "r").read().splitlines()
pool = concurrent.futures.ThreadPoolExecutor(max_workers=50)

for project in projects:
    print(f"project: {project}")
    pool.submit(dig_project, project)

pool.shutdown(wait=True)