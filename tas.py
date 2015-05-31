# -*- coding: utf-8 -*-
"""
Created on Wed May 27 20:40:52 2015

@author: colinh
"""
import time
import minimax
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
 
 
#felt: 'c-2D', 'c-3D', etc
 
#work piles: work1, work2... work8
#free cell piles: temp1, ... temp4
#completion piles: good1, ... good4
 
class TAS:
    
    def __init__(self, url):
        #select the headless web browser (whatever is installed)
        driver = webdriver.Firefox()
        #driver = webdriver.Chrome()
        
        #get the page information
        driver.get(url)
        #extract the html
        html = driver.page_source
        #convert to soup
        soup = BeautifulSoup(html)
        
        #extract the deck information from the html
        piles = []
        for i in range(1,9):
            name = "work"+str(i)
            pile = [None, None]
            #find the <div id=____>
            pile_soup = soup.find("div", {"id":name})
            for card_soup in pile_soup.contents:
                #print card_soup['class'][-1]
                card_tuple = self.felt_to_tuple(card_soup['class'][-1])
                if (None in card_tuple):
                    pass
                else:
                    pile.append((card_tuple[0], str(card_tuple[1])))
            piles.append(pile)
        print piles
        
        #example script for completion
        board = minimax.Board()
        board.fill_web(piles)
        board.display()
        (did_win, moves) = minimax.board_search(board)
        if did_win:
            print 'Won in ' + str(len(moves)) + ' moves. Executing...'
            for move in moves:
              card_tuple_jono, dst_pile = move
              self.hacky_move(driver, self.tuple_to_felt(card_tuple_jono), dst_pile)

    #convert felt ('c-2D') to tuple (card, suit)
    def felt_to_tuple(self, felt):
        felt_list = felt.split('-')
        if ('empty' in felt_list):
            card = None
            suit = None
        else:
            card =  felt_list[1][0]
            suit = felt_list[1][1]  
            
            if card == 'J':
                card = 11
            if card == 'Q':
                card = 12
            if card == 'K':
                card = 13
            if card == 'A':
                card = 1
            else:
                card = int(card)
        return (card, suit)
    
    #convert tuple (card, suit) to felt ('c-2D')
    def tuple_to_felt(self, card_tuple):
        card, color = card_tuple
        if card == 11:
            card = "J"
        if card == 12:
            card = "Q"
        if card == 13:
            card = "K"
        if card == 1:
            card = "A"
        return "c-"+str(card)+color

    #Click on a felt object. Follows the logic from piles.js
    #pile_game.prototype.best_pile (lines 240-246) ->
    #pile_game.prototype.move_affinity (lines 964-971) ->
    #accept: (lines 929-934)
    #icon bonus: (lines 925-927)
    
    #essentially it gives 10 points to any move to valid pile
    #15 points to any move to a completion pile (final pile)
    #for any tie (among all valid piles) it chooses by sort order (work->temp)
    
    def click(self, driver, felt):
        #driver.find_element_by_class_name('c-QS').click()
        driver.find_element_by_class_name(felt).click()
      
    #Drag on a felt object. Occassionally registers as a click()
    def drag(self, driver, src_felt, dst_felt):
        
        source = driver.find_element_by_class_name(src_felt)
        target = driver.find_element_by_id(dst_felt)
 
        actions = ActionChains(driver)
        ActionChains(driver).drag_and_drop(source, target).perform()
        
        #check that it ended up in the proper destination
        html = driver.page_source
        soup = BeautifulSoup(html)
        pile_soup = soup.find("div", {"id":dst_felt})
        check_felt = pile_soup.contents[-1]['class'][-1]
        if (check_felt == src_felt):
            return True
        else:
            return False 
    
    def hacky_move(self, driver, src_felt, dst_felt):
        while not (self.drag(driver, src_felt, dst_felt)):
            pass

        
TAS('http://greenfelt.net/freecell?game=107409544')