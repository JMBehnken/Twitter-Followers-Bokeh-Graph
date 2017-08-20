from bs4 import BeautifulSoup
import pandas as pd
import requests
import tweepy


csv_edges_path = 'Wacken_Graph_Edges.csv'
csv_nodes_path = 'Wacken_Graph_Nodes.csv'

max_followers_loaded = 25000

twitter_auth = 'twitter_auth.csv'



auth_keys = pd.read_csv(twitter_auth, header=None)[0].tolist()
ckey = auth_keys[0]
csecret = auth_keys[1]
atoken = auth_keys[2]
asecret = auth_keys[3]


def getWackenBands():
    url = 'http://www.wacken.com/de/bands/bands-billing/'
    html = requests.get(url).text
    bs = BeautifulSoup(html, 'lxml')
    
    band_names = []
    for elem in bs.findAll('div', {'class':'col-sm-20'}):
        for link in elem.findAll('a'):
            band = link.get_text()
            if band!='':
                band_names.append(band)

    return band_names


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
    translate_dict = {'Tweets':1, 'Folge ich':2, 'Follower':3, '„Gefällt mir“':4}
    
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
            
        twitter_data = [band, 0, 0, 0, 0]
        for value, name in values[:4]:
            twitter_data[translate_dict[name.split('-', 1)[0]]] = int(value.replace('.', ''))
    
        band_values.append(twitter_data)
        
    df_twitter_data = pd.DataFrame(band_values, columns=['Id', 'Tweets', 'Following', 'Follower', 'Likes'])
    df_twitter_data.to_csv(csv_nodes_path, index=False)
    
    return df_twitter_data


def getTwitterFollowers():
    follower_dict = {}
    for band in df_twitter_data['Id'].values:
        ids = []
        try:
            for page in tweepy.Cursor(api.followers_ids, screen_name=band).pages():
                ids.extend(page)
                if len(ids)>=max_followers_loaded:
                    break
            follower_dict[band] = ids
            print(band)
        except:
            print('Fehler: {}'.format(band))

    return follower_dict


def getMultipleFollowers():
    id_dict = {}
    for key in follower_dict.keys():
        for id in follower_dict[key]:
            if id in id_dict.keys():
                id_dict[id] += 1
            else:
                id_dict[id] = 1

    id_mix = []
    for item in id_dict.items():
        if item[1]>1:
            id_mix.append(item[0])

    return id_mix


def getDirectedEdges():
    edges = {}
    for key_1 in follower_dict.keys():
        follower_count = len(follower_dict[key_1])
        for id_1 in follower_dict[key_1]:
            if id_1 in id_mix:
                for key_2 in follower_dict.keys():
                    if key_1 != key_2:
                        if id_1 in follower_dict[key_2]:
                            edge = key_1+'::'+key_2
                            if edge in edges.keys():
                                edges[edge] += 1/follower_count
                            else:
                                edges[edge] = 1/follower_count

    directed_edges = []
    for item in edges.items():
        nodes = item[0].split('::')
        directed_edges.append([nodes[0], nodes[1], item[1]])

    return directed_edges


band_names = getWackenBands()
twitter_band_names = getTwitterAccounts()
df_twitter_data = getTwitterData()


auth = tweepy.OAuthHandler(ckey, csecret)
auth.set_access_token(atoken, asecret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


follower_dict = getTwitterFollowers()
id_mix = getMultipleFollowers()
directed_edges = getDirectedEdges()


df = pd.DataFrame(directed_edges, columns=['Source', 'Target', 'Weight'])
df.to_csv(csv_edges_path, index=False)