# GPT-3 SQL Query Generator and UI (And AI Chart Generator)

This is simple python application to generate SQL Schema + prompt to ask GPT-3 to generate SQL queries.

It also has a simple UI to show results in a table. And yes, **you can try to generate a chart from the results of query**.

GPT-3 self choose the chart type and prepare the data for it (it is not perfect, but it is a good start).

**It can generate a prompt for you, if you don't know what to ask GPT-3.**

![](https://github.com/Hormold/gpt-sql-box/blob/master/docs/demo.gif?raw=true)


## How it works:
1. Getting SQL schemas from PostgreSQL and compile prompt from SQL Schema
3. Wait for user input
4. Generate SQL query from prompt + user input
5. Show SQL query and ask user to confirm or edit if it is correct before executing it
6. Execute SQL query and show results in a table

## Environment
- OPENAI_TOKEN: OpenAI API token (Not nessessary, you can set it in the UI)
- APP_PORT: Port to run the application (default: 5000)
- OPENAI_ENGINE: OpenAI engine to use (default: text-davinci-003, not nessessary). You can set some free to use model: text-chat-davinci-002-20221122

## How to run
1. Install docker in local.
2. Set environment variables in `.env` file in project root or in your system/
3. Run command `docker-compose up --build -d`.
4. List docker container `docker ps` and get CONTAINER ID I.E `b13d03ee9dd8`.
5. Connect to docker container and generate fake data `docker exec -it b13d03ee9dd8 sh` note that `b13d03ee9dd8` can be different.
6. Run command `cd app` then `python gen_data.py` then type `exit`.
7. Open `http://localhost:8000` in your browser.
8. Note that Should limit by 10 so chart can appears.

