from flask import Flask,flash, render_template, request, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import psycopg2,json
import nltk
import re
from nltk import word_tokenize, sent_tokenize, pos_tag
from urllib import request as req
from bs4 import BeautifulSoup
from jinja2 import Template
from authlib.integrations.flask_client import OAuth

def download_nltk_data():
    try:
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('averaged_perceptron_tagger')
    except LookupError:
        pass  # Ignore if the data is already downloaded

download_nltk_data()

app = Flask(__name__)


oauth = OAuth(app)

app.config['SECRET_KEY'] = "THIS SHOULD BE SECRET"
app.config['GITHUB_CLIENT_ID'] = "0952c4bc0e19e060904e"
app.config['GITHUB_CLIENT_SECRET'] = "97d5caa411a4b340e5a22ce459fdaf917c0d2700"
github_admin_usernames = ["harzrawat", "atmabodha"]

github = oauth.register(
    name='github',
    client_id=app.config["GITHUB_CLIENT_ID"],
    client_secret=app.config["GITHUB_CLIENT_SECRET"],
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

# GitHub admin usernames for verification


# Default route
@app.route('/')
def index():
    # is_admin = False
    # github_token = session.get('github_token')
    # if github_token:
    #     github = oauth.create_client('github')
    #     resp = github.get('user').json()
    #     username = resp.get('login')
        # if username in github_admin_usernames:
        #     is_admin = True
    # return render_template('index.html', logged_in=github_token is not None, is_admin=is_admin)
    return render_template('index.html')





db_params = {
    'dbname': 'dhp2024_500s',
    'user': 'harsh',
    'password': 'XchK9yElcWfGBv8r3b3JXSgjqK3I1sdl',
    'host': 'dpg-cnmptr0l6cac73fd67q0-a',
    'port': 5432
    
}

def create_table():
    #conn = psycopg2.connect(**db_params)  # the double star ** is used for dictionary unpacking

# CAN BE WRITTEN LIKE BELOW ALSO
# conn = psycopg2.connect(
#     user='your_username',
#     password='your_password',
#     host='your_host',
#     database='your_database',
#     port='your_port'
# )

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS url_table (
                id SERIAL PRIMARY KEY,
                username varchar(24),
                url varchar(500),
                paragraph varchar(5000),
                Author varchar(30),
                header varchar(1000)[],
                inshort varchar(1000),
                sen_count integer,
                word_count integer,
                UPOS_tags_freq JSONB,
                News_channel varchar(30),
                Published_on DATE
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

create_table()

# def select_data():
#     conn=psycopg2.connect(**db_params)
#     cur=conn.cursor()

#     cur.execute("SELECT * from url_table")
#     table_data=cur.fetchall()

#     global url_lst
#     url_lst=[]


#     cur.close()
#     conn.close()
    
def refined_text(url):

    #url="https://www.indiatoday.in/india/story/brs-legislator-lasya-nanditha-dies-in-car-accident-in-telangana-2505975-2024-02-23"
    html1=req.urlopen(url).read().decode('utf8')
    soup=BeautifulSoup(html1,'html.parser')

    author = soup.find_all(class_='authdetaisl')[0].get_text()
    published_date = soup.find_all(class_='authdetaisl')[1].get_text()

    text_div=soup.find('div',class_='Story_description__fq_4S')
    lst_para=[]
    for text in text_div.find_all('p'):
        text_line=text.get_text(strip=True)   # strip=True is for removing white spaces to prevent newline char to be printed which happens if we don't use strip
        lst_para.append(text_line)
        para1=' '.join(lst_para)

    inshort = soup.find('div',class_='Story_stry__highlights__9IosL')
    inshort_list=[]
    for text in inshort.find_all('li'):
        inshort_list.append(text.get_text()+".")
    in_short=' '.join(inshort_list)

    return para1,author,in_short,published_date

def word_count(text):
    
    global word_list
    word_list=word_tokenize(text)
    for i in word_list:
        if re.search('[^\w]',i):
            word_list.remove(i)
            #print(i)
    word_count=len(word_list)
    return word_count, word_list

def sen_count(text):
    sen_lst=sent_tokenize(text)
    sen_count=len(sen_lst)
    return sen_count

upos_dict = {
    'NOUN': 'Noun',
    'VERB': 'Verb',
    'ADJ': 'Adjective',
    'ADV': 'Adverb',
    'ADP': 'preposition',
    'CONJ': 'Conjunction',
    'DET': 'Determiner',
    'NUM': 'Numeral',
    'PRON': 'Pronoun',
    'PRT': 'Particle',
    'X': 'Other'
}

def pos_tag_freq(text):
    upos_freq_dict = {}
    upos_words = {}
    
    # Tokenize the text into a list of words
    words = word_tokenize(text)
    
    # Perform part-of-speech tagging on the list of words
    upos_tags = pos_tag(words,tagset='universal')
    
    for word, upos in upos_tags:
        upos_category = upos_dict.get(upos, 'Other')  # Default to 'Other' if upos is not in the dictionary
        if upos_category in upos_freq_dict:
            upos_freq_dict[upos_category] += 1
            upos_words[upos_category].append(word)
        else:
            upos_freq_dict[upos_category] = 1
            upos_words[upos_category] = [word]

    return upos_freq_dict, upos_words

def header(url):
    html1=req.urlopen(url).read().decode('utf8')
    soup=BeautifulSoup(html1,'html.parser')
    
    subtitle = soup.find('h2',class_='jsx-ace90f4eca22afc7')  

    title = soup.find(class_='Story_strytitle__MYXmR')  
    return title.get_text(),subtitle.get_text()

# @app.route("/")
# def index():

#     is_admin = False
#     github_token = session.get('github_token')
#     if github_token:
#         github = oauth.create_client('github')
#         resp = github.get('user').json()
#         username = resp.get('login')
#         if username in github_admin_usernames:
#             is_admin = True
#     return render_template('index.html', logged_in=github_token is not None, is_admin=is_admin)



@app.route("/submit",methods=['POST','GET'])
def submit():
    username1 = request.form.get('username','')

    url=request.form.get('url','')   # request.form['url'] can also get  

    para1,author,inshort1,published_date = refined_text(url)
    word_count1,word_list = word_count(para1)
    sen_count1 = sen_count(para1)
    title1,subtitle1 = header(url)

    pos_tag_freq1,pos_tag_dict = pos_tag_freq(para1)
    upos_dict_len = len(pos_tag_freq1)
    pos_tag_dict=json.dumps(pos_tag_freq1)

    news_channel = "India Today"

    # global para1 
    # para1= refined_text(url)
    # author = author(url)
    # inshort = inshort(url)
    # word_count,word_list = word_count(para1)
    # sen_count = sen_count(para1)
    # pos_tag_dict = pos_tag_freq(para1)
    

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # Insert the user information into the data_table
        #if url not in 
        # cur.execute("""
        #     INSERT INTO url_table (username,url,
        #         paragraph,
        #         Author,
        #         summary,
        #         inshort,
        #         sen_count,
        #         word_count,
        #         UPOS_tags_freq,
        #         News_channel,
        #         Published_on DATE
        #     ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        # """, (username,url,para1,author,None,inshort,sen_count,word_count,pos_tag_dict,news_channel,published_date))

        cur.execute("""
        INSERT INTO url_table (username, url, paragraph, Author, header, inshort, sen_count, word_count, UPOS_tags_freq, News_channel, Published_on)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (username1, url, para1, author,[title1,subtitle1], inshort1, sen_count1, word_count1, pos_tag_dict, news_channel, published_date))


        conn.commit()
        cur.close()
        conn.close()

        return render_template('dashboard.html',username=username1, para1=para1, author=author, inshort=inshort1, published_date=published_date, word_count=word_count1, sen_count=sen_count1, pos_tag_freq1=pos_tag_freq1, news_channel=news_channel)

    except psycopg2.IntegrityError:
        return "Error: User with the same name already exists."



@app.route("/dashboard")
def dashboard():

    text_value = request.args.get('text_value', '')
    idx=int(text_value)

    conn=psycopg2.connect(**db_params)
    cur=conn.cursor()

    cur.execute("SELECT * from url_table")
    news_data=cur.fetchall()

    cur.close()
    conn.close()
    row_data = news_data[idx]

    username1 = row_data[1]
    para1= row_data[3]
    author=row_data[4]
    inshort1=row_data[6]
    published_date = row_data[11]
    word_count = row_data[8]
    sen_count1 = row_data[7]
    pos_tag_freq1 = row_data[9]
    upos_dict_len = len(pos_tag_freq1)
    # pos_tag_dict=json.dumps(pos_tag_freq1)
    news_channel = "India Today"

    return render_template('dashboard.html',username=username1, para1=para1, author=author, inshort=inshort1, published_date=published_date, word_count=word_count, sen_count=sen_count1, pos_tag_freq1=pos_tag_freq1, news_channel=news_channel)

@app.route("/home2", methods=['GET','POST'])
def home2():
    conn=psycopg2.connect(**db_params)
    cur=conn.cursor()

    cur.execute("SELECT * from url_table")
    news_data=cur.fetchall()

    cur.close()
    conn.close()

    row_count = len(news_data)

    return render_template("home2.html", table_data=news_data, row_count=row_count)


# github
@app.route('/login/github')
def github_login():
    '''Route for initiating GitHub OAuth login'''
    github = oauth.create_client('github')  # Create a GitHub OAuth client
    redirect_uri = url_for('github_authorize', _external=True)  # It Generate the redirect URI for authorization
    return github.authorize_redirect(redirect_uri)  # Redirect the user to GitHub for authorization

# Github authorize route
@app.route('/login/github/authorize')
def github_authorize():
    '''Route for handling GitHub OAuth authorization'''
    # main function for github that check if the user is admin the it redirect to history page 
    # It take connection 
    # conn = psycopg2.connect(**db_params)  
    # cur = conn.cursor()  
    
    try:
        github = oauth.create_client('github')  # Create a GitHub OAuth client
        token = github.authorize_access_token()  # Get the access token from the authorization response
        session['github_token'] = token  # Store the access token in the session
        resp = github.get('user').json()  # Get the user's information from GitHub
        print(f"\n{resp}\n")
        logged_in_username = resp.get('login')  # Get the username from the user's information
        if logged_in_username in github_admin_usernames:  # Check if the username is in the list of admin usernames
            # cur.execute('select * from url_table')  
            # data = cur.fetchall()  # Fetch all rows from the 'news' table
            # conn.close()  
            return redirect(url_for('home2'))
        else:
            return render_template('index.html')  
    except:
        return render_template('index.html')

# Logout route for GitHub
@app.route('/logout/github')
def github_logout():
    '''Route for logging out from GitHub OAuth'''
    session.pop('github_token', None)  # Remove the access token from the session
    return redirect(url_for('index'))

if __name__=='__main__':
    app.run(debug=True)
