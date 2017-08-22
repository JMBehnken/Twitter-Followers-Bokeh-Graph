from collections import Counter
from bs4 import BeautifulSoup
import pandas as pd
import requests
import tweepy
import sys

festival = sys.argv[1]
max_followers_loaded = int(sys.argv[2])

csv_edges_path = 'build/{}_Graph_Edges.csv'.format(festival)
csv_nodes_path = 'build/{}_Graph_Nodes.csv'.format(festival)

twitter_auth = 'twitter_auth.csv'



auth_keys = pd.read_csv(twitter_auth, header=None)[0].tolist()
ckey = auth_keys[0]
csecret = auth_keys[1]
atoken = auth_keys[2]
asecret = auth_keys[3]


def getNames():
    url = {'Hurricane':'http://www.hurricane.de/', 'Wacken':'http://www.wacken.com/de/bands/bands-billing/'}
    html = requests.get(url[festival]).text
    bs = BeautifulSoup(html, 'lxml')

    band_names = []
    if festival=='Hurricane':
        for elem in bs.findAll('div', {'class':'ABSATZ_LINEUP'}):
            for link in elem.findAll('a'):
                band = link.get_text().replace('\xa0', ' ')
                if band!='':
                    band_names.append(band)
    if festival=='Wacken':
        for elem in bs.findAll('div', {'class':'col-sm-20'}):
            for link in elem.findAll('a'):
                band = link.get_text()
                if band!='':
                    band_names.append(band)
    return set(band_names)


def getTwitterAccounts():
    twitter_band_names = []
    for band in band_names:
        twitter_search_url = 'https://twitter.com/search?f=users&vertical=default&q={}&src=typd&lang=de'.format(band)

        html = requests.get(twitter_search_url).text
        bs = BeautifulSoup(html, 'lxml')

        for elem in bs.findAll('span', {'class':'ProfileCard-screenname'})[:1]:
            twitter_band_names.append([band, elem.span.get_text()[1:]])
    return twitter_band_names


def getTwitterData():
    band_values = []
    translate_dict = {'Tweets':2, 'Folge ich':3, 'Follower':4, '„Gefällt mir“':5}

    for band, twitter_band in twitter_band_names:
        twitter_url = 'https://twitter.com/{}?lang=de'.format(twitter_band)

        html = requests.get(twitter_url).text
        bs = BeautifulSoup(html, 'lxml')

        values = []
        for value in bs.find('ul', {'class':'ProfileNav-list'}).findAll('li'):
            try:
                x = value.find('a')['title']
                values.append(x.split(' ', 1))
            except:
                pass

        twitter_data = [band.replace(' ', '_'), twitter_band, 0, 0, 0, 0]
        for value, name in values[:4]:
            try:
                twitter_data[translate_dict[name.split('-', 1)[0]]] = int(value.replace('.', ''))
            except:
                pass

        band_values.append(twitter_data)

    df_twitter_data = pd.DataFrame(band_values, columns=['Id', 'Account', 'Tweets', 'Following', 'Follower', 'Likes'])
    df_twitter_data.to_csv(csv_nodes_path, index=False)
    return df_twitter_data


def getTwitterFollowers():
    follower_dict = {}
    for band, account in df_twitter_data[['Id', 'Account']].values:
        ids = []
        try:
            for page in tweepy.Cursor(api.followers_ids, screen_name=account).pages():
                ids.extend(page)
                if len(ids)>=max_followers_loaded:
                    break
            print(band, len(ids))
        except:
            print('Fehler: {}'.format(band), len(ids))
        follower_dict[band] = ids
    return follower_dict


def getMultipleFollowers():
    keys, values = zip(*follower_dict.items())
    id_dict = Counter([item for sublist in values for item in sublist])
    id_mix = [item[0] for item in id_dict.items() if item[1]>1]
    return id_mix


def getDirectedEdges():
    edges = {key_1+'::'+key_2:len(set(follower_dict[key_2]).intersection(set(follower_dict[key_1]).intersection(id_mix)))/len(follower_dict[key_1]) for key_1 in follower_dict.keys() for key_2 in follower_dict.keys() if key_1 != key_2 and len(follower_dict[key_1])>0}
    directed_edges = [[item[0].split('::')[0].replace(' ', '_'), item[0].split('::')[1].replace(' ', '_'), item[1]] for item in edges.items() if item[1]>0]
    return directed_edges


def addIdcount():
    id_count = [[key, len(ids)]for key, ids in follower_dict.items()]
    df_id_count = pd.DataFrame(id_count, columns=['Id', '#Follower_Used'])

    df_nodes = pd.read_csv(csv_nodes_path)
    
    df_combined = df_nodes.merge(df_id_count, on='Id', how='left').fillna(0)
    df_combined.to_csv(csv_nodes_path, index=False)


band_names = getNames()
twitter_band_names = getTwitterAccounts()
df_twitter_data = getTwitterData()


auth = tweepy.OAuthHandler(ckey, csecret)
auth.set_access_token(atoken, asecret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


follower_dict = getTwitterFollowers()
addIdcount()
id_mix = getMultipleFollowers()
directed_edges = getDirectedEdges()


df = pd.DataFrame(directed_edges, columns=['Source', 'Target', 'Weight'])
df.to_csv(csv_edges_path, index=False)
