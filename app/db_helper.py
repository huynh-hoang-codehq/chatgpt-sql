import psycopg2
import os

def execute_query(sql_query):
    try:
        conn = psycopg2.connect(
                user=os.environ['POSTGRES_USER'],
                password=os.environ['POSTGRES_PASSWORD'],
                host=os.environ['POSTGRES_HOST'],
                database=os.environ['POSTGRES_DB']
            )
        cur = conn.cursor()
        cur.execute(sql_query)
        results = cur.fetchall()
        return {
            'success' : True,
            'results' : results
        }
    except psycopg2.Error as err:
        return {
            'success' : False,
            'results' : None
        }
    except Exception as err:
        return {
            'success': False,
            'error': str(err)
        }