import numpy as np
import pandas as pd
import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def espn_login(driver=None):  # Likely return to this to put it in another file
	'''If there is no active WebDriver session, open one and request ESPN 
	login.  Wait until login has been registered before advancing.
	Args:
	    driver: selenium WebDriver instance, logged in OR out of ESPN
	Return:
	    driver: selenium WebDriver instance, logged in to ESPN

	'''
	if not driver:
		driver = webdriver.Chrome('C:\ChromeDriver\chromedriver.exe')
    driver.get('http://www.espn.com/login/')
    logged_in = False
    while not logged_in:
    	innerHTML = driver.execute_script(
    		"return document.getElementsByTagName('html')[0].innerHTML")
		html = BeautifulSoup(innerHTML, 'html.parser')
		logged_in = not html.find_all('title')[0].get_text()=='Log In'
	return driver


def update_player_df(driver=None):
    ''' This function creates a pandas DataFrame where each row represents
    a single player with fields {name, pos, team, owner, keeper_val}.  It is
    meant to be run once per off-season, after the full player list for the
    upcoming draft has been updated on ESPN.  The field keeper_val initializes
    to NaN for all players, and must be modified manually or using the
    update_keeper_val function from this module afterwards.
    Args:
        driver: selenium WebDriver instance (optional), logged in OR out of ESPN
    Return:
        player_df: pandas DataFrame (n x 5) containing updated list of players 
                   for upcoming draft, but incomplete keeper_val field
    '''

    driver = espn_login(driver)
    driver.implicitly_wait(5)

    ''' Initialize an empty DataFrame, navigate to the player page, and begin to
    fill it.  Players will be added to the larger player_df DataFrame in chunks,
    with each chunk containing all the players on a single page. 
    '''
    player_df = pd.DataFrame(columns=['name', 'pos', 'team', 'owner', 
                                      'keeper_val'])
    driver.get('http://games.espn.com/ffl/freeagency?leagueId=2205911&teamId='
               '6&seasonId=2017#&seasonId=2017&avail=-1')
    last_player_logged = []
    while True:
        ''' Check to see if the page has loaded by testing if the last player
        on the page is the same as the last one logged on the previous page.
        '''
        waiting_to_load = True
        while waiting_to_load:          
            innerHTML = driver.execute_script(
                "return document.getElementsByTagName('html')[0].innerHTML")
            html = BeautifulSoup(innerHTML, 'html.parser')
            player_table = html.find(id='playertable_0')
            last_player_loaded = player_table.find_all('tr')[-1]
            last_player_loaded = last_player_loaded.find_all('td')[0].get_text()
            if last_player_logged != last_player_loaded:
                waiting_to_load = False

        ''' Fill the df_chunk DataFrame for the current page by iterating over
        every row and parsing the player data.
        '''
        players_on_page = len(player_table.find_all('tr'))-2   
        df_chunk = pd.DataFrame(
            columns=['name', 'pos', 'team', 'owner', 'keeper_val'], 
            index=range(0,players_on_page))
        row_marker = -1
        for row in player_table.find_all('tr')[2:]:
            row_marker += 1
            last_player_logged = row.find_all('td')[0].get_text()
            name_team_pos = re.split(', |\xa0', last_player_logged)
            if len(name_team_pos)==2:  # This applies only to d/st entries
                team_name = re.split(' ', name_team_pos[0])[0]
                name_team_pos = [name_team_pos[0], team_name, name_team_pos[1]]
            df_chunk.iat[row_marker, 0] = name_team_pos[0]
            df_chunk.iat[row_marker, 1] = name_team_pos[1]
            df_chunk.iat[row_marker, 2] = name_team_pos[2]
            df_chunk.iat[row_marker, 3] = row.find_all('td')[2].get_text()  
        player_df = player_df.append(df_chunk)
        ''' If another page becomes available within 3 seconds, click it to
        advance.  Otherwise, assume the final page has been reached, complete 
        the process, and exit the while loop.
        '''
        try:
            remaining_page = WebDriverWait(driver, 3).until(
            	EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'NEXT')))
            remaining_page.click()
        except:
            print('scraping complete')
            break

    ''' Fix the indices on the player_df DataFrame to match the number of the
    row, since each chunk was originally indexed separately.  Finally, return 
    the result.
    '''
    player_df = player_df.set_index(np.arange(len(player_df)))
    return(player_df)


def update_keeper_val(driver=None, prev_player_df=None, player_df=None):
	''' This function updates the keeper_val field for all players of a 
	player_df DataFrame that has recently been created using the 
	update_player_df function.
	Args:
		driver: selenium WebDriver instance (optional), logged in OR out of ESPN
	    prev_player_df: pandas DataFrame containing previous season's keeper_val
	                    data
	    player_df: pandas DataFrame containing updated list of players for
	               upcoming draft, but incomplete keeper_val field
	Returns:
	    player_df: pandas DataFrame containing updated list of players for
	               upcoming draft, with complete keeper_val field
	'''

	driver = espn_login(driver)
	driver.implicitly_wait(5)

	'''Navigate to the transactions page and change the date range to include 
	the full transaction history.
	'''
	driver.get('http://games.espn.com/ffl/recentactivity?leagueId=2205911&'
	           'activityType=2')
	innerHTML = driver.execute_script(
	    "return document.getElementsByTagName('html')[0].innerHTML")
	html = BeautifulSoup(innerHTML, 'html.parser')
	''' Log the oldest transaction on the page so that you can check whether the
	form submission for including full transactions has finished loading.
	'''
	check_element_prev = html.find_all('tr')[-1].get_text()
	check_element_cur = check_element_prev
	startDate = Select(driver.find_element_by_name('startDate'))
	startDate.select_by_index(0)
	driver.find_element_by_name('startDate').submit()
	while check_element_prev == check_element_cur:
	    innerHTML = driver.execute_script(
	        "return document.getElementsByTagName('html')[0].innerHTML")
	    html = BeautifulSoup(innerHTML, 'html.parser')
	    check_element_prev = html.find_all('tr')[-1].get_text()

	''' Iterate over all of the currently owned players and assign 7 as their
	keeper value if they were a FA pickup.
	'''
	owned_players = player_df.loc[player_df['owner'] != 'FA']
	for ind, player in owned_players.iterrows():
	    try:
	        trans_index = 0
	        while True:
	            trans_text = html(text=player['name']
	                )[trans_index].find_parents('td')[0].get_text()
	            if not 'traded' in trans_text:
	                player_df.loc[ind]['keeper_val'] = 7
	                break
	            else:
	                trans_index += 1
	    except IndexError:
	        pass

	''' Iterate over all of the remaining owned players, which must have
	been drafted, and assign their keeper values based on the round they
	were drafted in.  Also, reduce their value by 1 if they were kept last
	season.
	'''
	driver.get(
	    'http://games.espn.com/ffl/tools/draftrecap?leagueId=2205911')
	innerHTML = driver.execute_script(
	    "return document.getElementsByTagName('html')[0].innerHTML")
	html = BeautifulSoup(innerHTML, 'html.parser')
	owned_players = player_df.loc[player_df['owner'] != 'FA']
	drafted_players = owned_players.loc[pd.isnull(owned_players['keeper_val'])]
	for ind, player in drafted_players.iterrows():
	    draft_row = html(text=player['name'])[0].find_parents('tr')[0]
	    round_header = draft_row.find_previous_siblings('tr')[-1].get_text()
	    player_df.loc[ind]['keeper_val'] = int(re.split(' ', round_header)[-1])
	    if prev_player_df:
	        kept_twice = not pd.isnull(prev_player_df.loc[
	            prev_player_df['name']==player['name']]['keeper_val'][0])
	        if (player_df.loc[ind]['keeper_val']>1) & kept_twice:
	            player_df.loc[ind]['keeper_val'] -= 1

    return(player_df)


