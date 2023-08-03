"""Web app to generate SQL queries from user input using GPT-3"""
import os
import json
import sys
import time
import psycopg2
import openai
import re

from flask import Flask, request, render_template
from schema import Schema
from langchain.prompts.prompt import PromptTemplate
from langchain import OpenAI, SQLDatabase, SQLDatabaseChain

from db_helper import execute_query

app = Flask(__name__, template_folder='tpl')

OPENAI_ENGINE = os.getenv('OPENAI_ENGINE') or 'text-davinci-003'
TEMPLATE_DIR = os.path.abspath('./app/tpl')
PROMPT_DIR = os.path.abspath('./app/prompts')
APP_PORT = os.getenv('APP_PORT') or 5000

print(f"POSTGRES_USER {os.environ['POSTGRES_USER']}")
print(f"POSTGRES_PASSWORD {os.environ['POSTGRES_PASSWORD']}")
print(f"POSTGRES_HOST {os.environ['POSTGRES_HOST']}")
print(f"POSTGRES_DB {os.environ['POSTGRES_DB']}")

if os.getenv('OPENAI_TOKEN'):
    openai.api_key = os.getenv('OPENAI_TOKEN')

if not openai.api_key:
    print('Please set OPENAI_TOKEN in .env file or set token in UI') # Not a critical error

# Generate SQL Schema from PostgreSQL
schema = Schema()
sql_schema, json_data = schema.index()
print('SQL data was generated successfully.')

def load_prompt(name: str) -> str:
    """Load prompt from file"""
    with open(os.path.join(PROMPT_DIR, name + ".txt"), 'r', encoding='utf-8') as file:
        return file.read()

# Middleware to check key in request or in .env file
@app.before_request
def get_key():  
    """Get API key from request or .env file"""
    if (request.content_type != 'application/json'
        or request.method != 'POST'
        or request.path == '/run'):
        return
    content = request.json
    if not content['api_key'] and not openai.api_key:
        return {
            'success': False,
            'error': 'Please set OPENAI_TOKEN in .env file or set token in UI'
        }

    if content and content['api_key']:
        request.api_key = content['api_key']
    else:
        request.api_key = os.getenv('OPENAI_TOKEN')

@app.get('/')
def index():
    """Show SQL Schema + prompt to ask GPT-3 to generate SQL queries"""
    normalized_json_data = json.dumps(json_data)
    return render_template(
        'index.html',
        has_openai_key=bool(openai.api_key),
        sql_schema=sql_schema,
        json_data=normalized_json_data
    )

@app.post('/generate')
def generate():
    """Generate SQL query from prompt + user input"""
    try:
        content = request.json
        user_input = content['query']
        query_temperture = content['temp']
        selected = content['selected']

        openai.api_key = request.api_key
        regen_schema = schema.regen(selected)
        fprompt = load_prompt('sql_llm')
        # Edit prompt on the fly by editing prompts/sql_llm.txt

        # Ask GPT-3
        PROMPT = PromptTemplate(
            input_variables=["input", "table_info", "dialect", "top_k"], template=fprompt
        )
        API_KEY = os.getenv('OPENAI_TOKEN')
        db = SQLDatabase.from_uri(
            f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:5432/{os.environ['POSTGRES_DB']}"
        )
        llm = OpenAI(model_name="text-davinci-003", openai_api_key=API_KEY, temperature=0)
        db_chain = SQLDatabaseChain.from_llm(
            llm, db, prompt=PROMPT, verbose=True, use_query_checker=True, return_intermediate_steps=True,
            return_direct=False, top_k=5
        )
        err_flag = False
        try:
            gpt_response = db_chain(user_input)
        except:  # self correct with version chatgpt v3
            err_flag = True
            regen_schema = schema.regen(selected)
            fprompt = load_prompt('sql').replace('{regen_schema}', regen_schema).replace('{user_input}', user_input)
            gpt_response = openai.Completion.create(
            engine=OPENAI_ENGINE,
            prompt=fprompt,
            temperature=0,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n\n"]
        )
            used_tokens = gpt_response['usage']['total_tokens']

            # Get SQL query
            sql_query = gpt_response['choices'][0]['text']
            sql_query = sql_query.lstrip().rstrip()
            

        if not err_flag:
            for obj in gpt_response['intermediate_steps']:
                if isinstance(obj, dict) and 'sql_cmd' in obj:
                    sql_query = obj['sql_cmd']
        else:  # check if sql is correct
            results = execute_query(sql_query)

            # incorrect sql
            if not results['success'] and results.get('error') is None:
                prompt = """
                correct this sql query
                {sql_query}
                and then outline the correct query in code block"""
                prompt = prompt.format(sql_query=sql_query)
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0
                )
                content = response.get('choices', [])[0].get('message', {}).get('content')
                matches = [m.group(1) for m in re.finditer("```([\w\W]*?)```", content)]
                sql_query = matches[0]      
            elif not results['success'] and results.get('error'):
                return results

        print('Generated SQL query:', sql_query)
        sql_query = sql_query.lstrip().rstrip()

        # Return json
        return {
            'success': True,
            'sql_query': sql_query,
            'used_tokens': 0,
        }
    except Exception as err:
        print(err)
        return {
            'success': False,
            'error': str(err)
        }

@app.post('/run')
def execute():
    """Execute SQL query and show results in a table"""
    # Get SQL query
    try:
        ts_start = time.time()
        content = request.json
        sql_query = content['query']
        print('Run SQL query:', sql_query)
        # Execute SQL query and show results in a table
        conn = psycopg2.connect(
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            host=os.environ['POSTGRES_HOST'],
            database=os.environ['POSTGRES_DB']
        )
        cur = conn.cursor()
        cur.execute(sql_query)
        results = cur.fetchall()

        # Return json with all columns names and results
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in results]
        seconds_elapsed = time.time() - ts_start
        return {
            'success': True,
            'columns': columns,
            'results': results,
            'seconds_elapsed': seconds_elapsed
        }

    except psycopg2.Error as err:
        print(err)
        return {
            'success': False,
            'error': str(err)
        }
    except Exception as err:
        print(err)
        return {
            'success': False,
            'error': str(err)
        }

@app.post('/generate_prompt')
def generate_prompt():
    """Generate prompt from selected tables"""
    try:
        content = request.json
        selected = content['selected']
        query_temperture = content['temp']

        openai.api_key = request.api_key

        # Update prompt
        regen_schema = schema.regen(selected)
        final_prompt = load_prompt('idk').replace('{regen_schema}', regen_schema)
        print(f'Final prompt: {final_prompt}')

        gpt_response = openai.Completion.create(
            engine=OPENAI_ENGINE,
            prompt=final_prompt,
            temperature=float(query_temperture),
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n\n"]
        )

        used_tokens = gpt_response['usage']['total_tokens']

        # Get SQL query
        query = gpt_response['choices'][0]['text'].lstrip().rstrip()
        print('Generated prompt:', query)

        return {
            'success': True,
            'query': query,
            'used_tokens': used_tokens,
        }
    except Exception as err:
        print(err)
        return {
            'success': False,
            'error': str(err)
        }

@app.post('/generate_chart')
def generate_chart():
    """Generate chart from SQL query"""
    content = request.json
    csv_data = str(content['csv_data'])
    query_temperture = float(content['temp'])
    print('CSV data:', csv_data)
    print('Query temperture:', query_temperture)
    #chart_type = content['chart_type'] # bar, line, pie, scatter
    example_prompt = load_prompt('graph').replace('{csv_data}', csv_data)

    openai.api_key = request.api_key
    gpt_response = openai.Completion.create(
        engine=OPENAI_ENGINE,
        prompt=example_prompt,
        temperature=float(query_temperture),
        max_tokens=300,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n\n"]
    )

    used_tokens = gpt_response['usage']['total_tokens']
    pseudo_code = gpt_response['choices'][0]['text'].lstrip().rstrip();
    chart_type = pseudo_code.split('|')[0]
    chart_data = pseudo_code.split('|')[1]

    return {
        'success': True,
        'chart_type': chart_type,
        'chart_data': chart_data,
        'used_tokens': used_tokens,
    }

# Run web app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(APP_PORT), debug=True)
