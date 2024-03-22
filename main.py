import discord
import os
from dotenv import load_dotenv
from interpreter import interpreter
from discord.ext import commands
import re

# Load environment variables from .env file
load_dotenv()  
TOKEN = os.getenv('DISCORD_TOKEN')
interpreter.offline = True
interpreter.llm.api_base  = os.getenv('OLAMA_HOST')
interpreter.llm.model = os.getenv('OLAMA_MODEL')
interpreter.llm.max_tokens = 500
interpreter.messages = []
answer = []
current_message_index = 0


# Response functions
async def llm_response(ctx, arg):
    global answer
    answer = []  # Reset answer before processing new question
    for chunk in interpreter.chat(arg, display=False, stream=True):
        str(chunk)
        print(str(chunk))
        process_chunk(chunk)
    formatted_answer_chunks = format_answer(answer)
    for chunk in formatted_answer_chunks:
        await ctx.send('```'+chunk+'```')


# Define the process_chunk function
def process_chunk(chunk):
    global current_message_index, answer
    if chunk.get('start'):
        temp_message = {
            'role': chunk['role'],
            'type': chunk['type'],
            'content': "",
        }
        if 'format' in chunk:
            temp_message['format'] = chunk['format']
        if 'recipient' in chunk:
            temp_message['recipient'] = chunk['recipient']

        answer.append(temp_message)
        current_message_index = len(answer) - 1

    if chunk.get('format') == "active_line":
        answer[current_message_index]['activeLine'] = chunk['content']
    elif chunk.get('end') and chunk.get('type') == "console":
        answer[current_message_index]['activeLine'] = None

    if chunk.get('content') and chunk.get('format') != "active_line":
        answer[current_message_index]['content'] += str(chunk['content'])
        
def format_answer(answer):
    formatted_answer = ""
    for message in answer:
        if 'content' in message:
            if message.get('type') == 'code':
                # Ensure the provided code block is formatted properly
                format_code = message.get('format', '')  # Get the specified format
                if format_code:
                    formatted_answer += f"```{format_code}\n{message['content']}\n```\n"
                else:
                    formatted_answer += f"```\n{message['content']}\n```\n"
            else:
                formatted_answer += f"{message['content']}\n"

    # Split the formatted answer into chunks of 2000 characters
    chunks = []
    current_chunk = ""
    for line in formatted_answer.split('\n'):
        if len(current_chunk) + len(line) + 5 > 2000:  # Add 5 for potential code block formatting
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += line + '\n'
    if current_chunk:  # Append remaining chunk
        chunks.append(current_chunk)

    return chunks


# Init bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)


@bot.command()
async def q(ctx, *, question: str):
    await ctx.send("Asking Language Model...")
    await llm_response(ctx, question)


@bot.command()
async def test(ctx):
    pass


bot.run(TOKEN)
