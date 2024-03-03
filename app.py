from flask import Flask,render_template, url_for, request,redirect
import nltk
from nltk import word_tokenize, sent_tokenize,pos_tag
from nltk.corpus import stopwords
import psycopg2
import json
app = Flask(__name__)

db_params = {
    'dbname': 'dhp2024',
    'user': 'harsh',
    'password': 'og0SmkFq8jjWPuHtF33OKNf67Ksr6ccl',
    'host': 'postgres://harsh:og0SmkFq8jjWPuHtF33OKNf67Ksr6ccl@dpg-cn3rmr2cn0vc738puj60-a/dhp2024',
    'port': 5432
    
}

def create_dat_table():
    conn = psycopg2.connect(**db_params)
    # Establish a connection to the PostgreSQL database using the provided connection parameters
    
    cur = conn.cursor()
    # This line creates a cursor object (cur) using the conn.cursor() method. A cursor is needed to execute SQL commands on the database.
    
    # Create the data_table if it does not exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dat_table (
            id SERIAL PRIMARY KEY,
            Text char(500),
            Word_Count integer,
            sent_count integer,
            stop_count integer,
            upos_tag_dict JSONB,
            upos_tag_count integer
        )
    """)

    conn.commit()
    # This line commits the changes made by the execute method to the database. Changes are not permanent until they are committed.
    
    cur.close()
    # This line closes the cursor. Closing the cursor is important to release the database resources associated with it.
    
    conn.close()
    # This line closes the database connection. Like closing the cursor, it releases the resources associated with the database connection.

create_dat_table()

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/data_submit", methods=['POST'])
def data_submit():
    text = request.form["inputText"]

    def word_count(text):
        c=0
        for i in text:
            if i==" ":
                c+=1
        if text[len(text)-1] != " ":
            c+=1
            return c
        else:
            return c
            
    
    word_lst = word_tokenize(text)
    word_count = word_count(text)

    def sen_count(text):
        c=0
        for i in text:
            if i in ['.','?']:
                c+=1
        return c
    

    sent_tokenize1 = sent_tokenize(text)
    sen_count = sen_count(text)

    stopwords_lst = stopwords.words('english')
    def count_stop(word_lst):
        c=0
        for i in word_lst:
            if i in stopwords_lst:
                c+=1
        return c

    stop_count = count_stop(word_lst)

    upos_tags = pos_tag(word_lst)
    tag_count_dict = {}
    
    for word,tags in upos_tags:
        if tags in tag_count_dict:
            tag_count_dict[tags]+=1
        else:
            tag_count_dict[tags]=1
    tag_count = len(tag_count_dict)
    tag_count_dict = json.dumps(tag_count_dict)
    
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        cur.execute("""
            insert into dat_table (Text,Word_Count,sent_count,stop_count,upos_tag_dict,upos_tag_count) values (%s,%s,%s,%s,%s,%s)""",(text,word_count,sen_count,stop_count,tag_count_dict,tag_count))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('dashboard'))
    except psycopg2.IntegrityError:
        return "Error: User with the same name already exists."

@app.route("/dashboard")
def dashboard():
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    cur.execute("select * from dat_table")
    users1 = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("dashboard.html",users = users1)

if __name__=="__main__":
    app.run(debug=True)
