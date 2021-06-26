from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import re # Used to remove all non-numeric characters from transfermkt market_value
import unidecode # Used to normalize text, so that accents in text don't mess anything up

url_away = 'https://www.transfermarkt.com/danemark/kader/verein/3436/saison_id/2020'
url_home = 'https://www.transfermarkt.com/wales/startseite/verein/3864'
url_sofascore = 'https://www.sofascore.com/wales-denmark/BObscUb'

def get_team_name(url):
    soup = BeautifulSoup(requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}).text, 'lxml')
    team_name = soup.find('h1').text.split('\n')[1]
    return(team_name)

def get_mkt_stats(url):
    soup = BeautifulSoup(requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}).text, 'lxml')
    transfermkt_table = soup.find('table', class_ = 'items')
    player_list = []
    # team_name = soup.find('h1').text.split('\n')[1]

    for number in ['odd', 'even']:
        for player in transfermkt_table.find_all('tr', class_ = number):
            title_classes = ['hide', 'hauptlink']
            title = None

            for title_class in title_classes:
                try:
                    title = unidecode.unidecode(player.find('td', class_ = title_class).find('a').text)
                except:
                    pass
            
            try:
                market_value = player.find('td', class_ = 'rechts hauptlink').text
            except:
                market_value = None
            if 'Th' in market_value:
                multiplier = 1000
            elif 'm' in market_value:
                multiplier = 1000000
            else:
                multiplier = 1
            market_value = re.sub('[^0-9&.]', '', market_value)
            try:
                market_value = float(market_value)*multiplier
            except:
                market_value = None
            player_list.append([title, market_value])
    return player_list

def get_sofascore_stats(url):
    options = Options()
    options.add_argument('--start-maximized')
    browser = webdriver.Chrome(options=options)
    browser.get(url)
    player_list = []
    time.sleep(3)

    ## Get Bench players data
    html = browser.page_source
    soup = BeautifulSoup(html, 'lxml')
    bench = soup.find_all('div', class_ = 'Cell-decync-0 knmMhW u-pos-relative')[0]

    for team in bench.find_all('div', class_ = 'Section-sc-1a7xrsb-0 hwkKwf'):
        try:
            team_name = team.find('div', class_ = 'Cell-decync-0 fhgviz').text
            for bench_player in team.find_all('a', class_ = 'styles__Wrapper-x0hpjw-0 iTJSTP'):
                
                title = unidecode.unidecode(bench_player.find('div', class_ ='Content-sc-1o55eay-0 styles__NameWrapper-x0hpjw-5 gRoJDC')['title'])
                try:
                    rating = bench_player.find('div', class_ = 'Section-sc-1a7xrsb-0 styles__RatingSection-x0hpjw-6 hZBBnd').text
                except:
                    rating = None
                player_list.append([team_name, title, 'Bench'])
        except:
            pass
    
    ## Get Missing players data -- If information relating to missing players is needed
    # try:
    #     missing = soup.find_all('div', class_ = 'Cell-decync-0 knmMhW u-pos-relative')[1]
    #     for team in missing.find_all('div', class_ = 'Section-sc-1a7xrsb-0 hwkKwf'):
    #         try:
    #             team_name = team.find('div', class_ = 'Cell-decync-0 fhgviz').text
    #             for missing_player in team.find_all('a', class_ = 'styles__Wrapper-x0hpjw-0 iTJSTP'):
                    
    #                 title = unidecode.unidecode(missing_player.find('div', class_ ='Content-sc-1o55eay-0 styles__NameWrapper-x0hpjw-5 gRoJDC')['title'])
    #                 try:
    #                     rating = missing_player.find('div', class_ = 'Section-sc-1a7xrsb-0 styles__RatingSection-x0hpjw-6 hZBBnd').text
    #                 except:
    #                     rating = None
    #                 player_list.append([team_name, title, 'Missing'])
    #         except:
    #             pass
    # except:

    ## Get Field players data
    WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#__next > main > div > div.Content__PageContainer-sc-14479gi-0.ArfrF > div.Grid-sc-1kxv72p-0.gVSUkA > div.Col-pm5mcz-0.gnwDsu > div > div.u-mB12 > div > div.Tabs__Header-vifb7j-0.bpUSvK > a:nth-child(2)'))).click()
    html = browser.page_source
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('table', class_ = 'styles__Table-sc-1gdm1n4-6 dygnyR')
    body = table.find('tbody')
    for player in body.find_all('tr'):
        player_table_info = []
        player_info = []
        team_name = player.find('img')['alt']
        title = unidecode.unidecode(player.find('td', class_ = 'styles__FilterCell-sc-1gdm1n4-3 elgNrP').text)
        data = player.find_all('td', class_ = 'styles__StatisticCell-sc-1gdm1n4-5 hTKZks')
        for info in data:
            player_table_info.append(info.text) ## data[8] = position
        rating = player.find('td', class_ = 'styles__StatisticCell-sc-1gdm1n4-5 jtaVpb').text
        player_info = [team_name, title, 'Field']
        player_list.append(player_info)
    
    browser.quit()
    return player_list


with pd.ExcelWriter('football_data.xlsx') as writer:
    sofascore_df = pd.DataFrame(get_sofascore_stats(url_sofascore), columns=['Team Name', 'Player Name', 'Position'])
    sofascore_df.to_excel(writer, sheet_name='Sofascore')
    home_team_df = pd.DataFrame(get_mkt_stats(url_home), columns=['Player Name', 'Market Value'])
    home_team_df['Position'] = ('=IFERROR(VLOOKUP(INDIRECT("R[0]C[-2]",0),Sofascore!C:D,2,0), "Not Found")')
    home_team_df['Field Value'] = None
    home_team_df['Bench Value'] = None
    home_team_df['Field Count'] = None
    home_team_df['Bench Count'] = None
    home_team_df['Not Found Count'] = None
    home_team_df['Field Value'][0] = ('=SUMIF(D:D,"Field",C:C)')
    home_team_df['Bench Value'][0] = ('=SUMIF(D:D,"Bench",C:C)')
    home_team_df['Field Count'][0] = ('= COUNTIF(D:D,"Field")')
    home_team_df['Bench Count'][0] = ('= COUNTIF(D:D,"Bench")')
    home_team_df['Not Found Count'][0] = ('=COUNTIF(D:D, "Not Found")')
    home_team_df.to_excel(writer, sheet_name=get_team_name(url_home))
    away_team_df = pd.DataFrame(get_mkt_stats(url_away), columns=['Player Name', 'Market Value'])
    away_team_df['Position'] = ('=IFERROR(VLOOKUP(INDIRECT("R[0]C[-2]",0),Sofascore!C:D,2,0), "Not Found")')
    away_team_df['Field Value'] = None
    away_team_df['Bench Value'] = None
    away_team_df['Field Count'] = None
    away_team_df['Bench Count'] = None
    away_team_df['Not Found Count'] = None
    away_team_df['Field Value'][0] = ('=SUMIF(D:D,"Field",C:C)')
    away_team_df['Bench Value'][0] = ('=SUMIF(D:D,"Bench",C:C)')
    away_team_df['Field Count'][0] = ('= COUNTIF(D:D,"Field")')
    away_team_df['Bench Count'][0] = ('= COUNTIF(D:D,"Bench")')
    away_team_df['Not Found Count'][0] = ('=COUNTIF(D:D, "Not Found")')
    away_team_df.to_excel(writer, sheet_name=get_team_name(url_away))
