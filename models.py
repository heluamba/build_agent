import os
import ollama
from openai import OpenAI
from dotenv import load_dotenv

OPEN_MODEL = "openai/gpt-oss-20b:free"
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_MULTIMODAL="qwen2.5vl:3b"

load_dotenv()
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY environment variable not set")


open_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

ollama_client = OpenAI(
	base_url="http://localhost:11434/v1",
	api_key="ollama"
)


def	gerate_content(client: OpenAI, messages):
	response = client.chat.completions.create(
		model = OPEN_MODEL,
		messages=messages,
		max_tokens=300
	)

	respo = {
            "res": response.choices[0].message.content,
			"prompt_tokens": response.usage.prompt_tokens,
			"completion_tokens": response.usage.completion_tokens
    }
	return respo


def	response_by_open_model(prompt):
	response = open_client.chat.completions.create(
	 	model = OPEN_MODEL,
	 	messages=
	 	[
	 		{   
	 			"role": "user",
	 			"content": prompt
	 		}
	 	],
	 	max_tokens=300,
		temperature=0
	 )
	respo = {
            "res": response.choices[0].message.content.strip(),
			"prompt_tokens": response.usage.prompt_tokens,
			"completion_tokens": response.usage.completion_tokens
    }
	
	return (respo)

def	response_by_ollama_model(prompt):
	response = ollama.chat(
	model=OLLAMA_MODEL,
	messages=[
				{
					"role":"user",
					"content": prompt
				}
			],
	options={
			"temperature":0,
			}
	)
	return (response['message']['content']).strip()

def	response_by_ollama_multimodal(prompt, image_path):
	response = ollama.chat(
	model=OLLAMA_MULTIMODAL,
	messages=[
				{
					"role":"user",
					"content": prompt,
					"images":[image_path]
				}
			],
	options={
			"temperature":0,
			}
	)
	tokens_entrada = response.get('prompt_eval_count', 0)
	tokens_saida = response.get('eval_count', 0)
	
	respo = {
				"total_tokens": tokens_entrada + tokens_saida,
				"response":response['message']['content'].strip()
			}
	return (respo)
