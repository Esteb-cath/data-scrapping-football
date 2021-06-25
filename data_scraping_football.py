from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import csv
import unidecode # Used to normalize text, so that accents in text don't mess anything up
from pdb import set_trace

url_away = 'https://www.transfermarkt.com/singha-chiangrai-united/startseite/verein/6759'
url_home = 'https://www.transfermarkt.com/jeonbuk-hyundai-motors/startseite/verein/6502'
url_sofascore = 'https://www.sofascore.com/jeonbuk-hyundai-motors-chiangrai-united/iNcsqGB'


def get_mkt_stats(url):
    soup = BeautifulSoup(requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}).text, 'lxml')
    transfermkt_table = soup.find('table', class_ = 'items')
    player_list = []

    team_name = soup.find('div', class_ = 'subkategorie-header').text.split('Squad of ')[1]

    for number in ['odd', 'even']:
        for player in transfermkt_table.find_all('tr', class_ = number):
            title = unidecode.unidecode(player.find('td', class_ = 'hide').text)
            market_value = player.find('td', class_ = 'rechts hauptlink').text
            player_list.append([team_name, title, market_value])
    return player_list

def get_sofascore_stats(url):
    options = Options()
    browser = webdriver.Chrome(options=options)
    browser.get(url)
    player_list = []
    time.sleep(3)

    ## Get Bench players data
    html = browser.page_source
    soup = BeautifulSoup(html, 'lxml')

    for team in soup.find_all('div', class_ = 'Section-sc-1a7xrsb-0 hwkKwf'):
        try:
            team_name = team.find('div', class_ = 'Cell-decync-0 fhgviz').text
            for bench_player in team.find_all('a', class_ = 'styles__Wrapper-x0hpjw-0 iTJSTP'):
                
                title = unidecode.unidecode(bench_player.find('div', class_ ='Content-sc-1o55eay-0 styles__NameWrapper-x0hpjw-5 gRoJDC')['title'])
                try:
                    rating = bench_player.find('div', class_ = 'Section-sc-1a7xrsb-0 styles__RatingSection-x0hpjw-6 hZBBnd').text
                except:
                    rating = None
                position = 'Bench'
                player_list.append([team_name, title, None, None, None, None, None, None, None, None, position, rating])
        except:
            pass



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
        player_info = [team_name, title]
        player_table_info[8] = 'Field - ' + player_table_info[8]
        player_info.extend(player_table_info)
        player_info.append(rating)
        player_list.append(player_info)
    
    browser.quit()
    return player_list




with open('football_scrape.csv', 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Transfermarkt Data'])
    csv_writer.writerow(['Team Name', 'Player Name', 'Market value'])
    player_list_mkt = get_mkt_stats(url_away)
    player_list_mkt.extend(get_mkt_stats(url_home))
    player_list_mkt.extend([[None]])
    player_list_mkt.extend([['Sofascore Data']])
    player_list_mkt.extend([['Team Name', 'Player Name', 'Goals', 'Assists', 'Tackles', 'Acc Passes', 'Duels (won)', 'Ground Duels (won)',
    'Aerial Duels (won)', 'Minutes Played','Position', 'Rating']])
    player_list_mkt.extend(get_sofascore_stats(url_sofascore))
    for player_mkt in player_list_mkt:
        # for player_sofa in player_list_sofa:
        #     player_mkt.append(player_sofa[1])
        csv_writer.writerow(player_mkt)
    ## get_mkt_stats(url_away, csv_file)



csv_file.close()