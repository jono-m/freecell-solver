# -*- coding: utf-8 -*-
"""
Created on Wed May 27 20:40:52 2015

@author: colinh
"""
import time
import random
import minimax
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
 
#felt: 'c-2D', 'c-3D', etc
 
#work piles: work1, work2... work8
#free cell piles: temp1, ... temp4
#completion piles: good1, ... good4
 
class TAS:
    
    def __init__(self):
        #select the headless web browser (whatever is installed)
        driver = webdriver.Firefox()

        f = open('logfile.txt', 'a')

        game_number = 1
        while True:
            driver.get('http://greenfelt.net/freecell?game=' + str(game_number))
            try:
                self.login(driver)
            except NoSuchElementException:
                print 'Already logged in.'

            time.sleep(1)
            driver.find_element_by_id('pause').click()
            f.write(str(game_number) + "\n")
            self.play_game(driver, f)
            time.sleep(3)
            game_number += 1

        f.close()

    def new_game(self, driver):
        driver.find_element_by_link_text('New Game').click()

    def play_game(self, driver, f):

        (piles, free, freeFilled, finish) = self.extract_piles(driver)
        
        # #example script for completion
        board = minimax.Board()
        board.fill(free, freeFilled, finish, piles)
        board.display()
        # raw_input('')
        (did_win, moves) = minimax.board_search(board)
        num_moves = len(moves)
        num_finish = 0
        newMoves = []
        while did_win:
            if len(moves) == 0:
                f.write('Won game in ' + str(num_moves) + ' moves.' + "\n-----\n\n")
                return
            print 'Won in ' + str(len(moves)) + ' moves. Executing...'
            for move in moves:
                print move
            driver.find_element_by_id('pause').click()
            time.sleep(1)
            for move in moves:
                card_tuple_jono, dst_pile, check_column = move
                if not self.drag(driver, self.tuple_to_felt(card_tuple_jono), dst_pile, check_column):
                    driver.find_element_by_id('pause').click()
                    time.sleep(1)
                    (piles, free, freeFilled, finish) = self.extract_piles(driver)
                    board = minimax.Board()
                    board.fill(free, freeFilled, finish, piles)
                    board.display()
                    (did_win, moves) = minimax.board_search(board)
                    break
                if dst_pile[0] == 'g':
                    num_finish += 1
                if num_finish >= 30:
                    driver.find_element_by_xpath('//a[@title="Ctrl-A or Left-Click (off any cards)"]').click()
                    driver.find_element_by_id('pause').click()
                    time.sleep(1)
                    (piles, free, freeFilled, finish) = self.extract_piles(driver)
                    board = minimax.Board()
                    board.fill(free, freeFilled, finish, piles)
                    board.display()
                    (did_win, moves) = minimax.board_search(board)
                    break

    def login(self, driver):
        driver.find_element_by_id('user').send_keys('bongwater')
        driver.find_element_by_id('pass').send_keys('bongwater')
        driver.find_element_by_id('login').click()


    def extract_piles(self, driver):
        #extract the deck information from the html
        #extract the html
        html = driver.page_source
        #convert to soup
        soup = BeautifulSoup(html)
        piles = []
        for i in range(1,9):
            name = "work"+str(i)
            pile = [None, None]
            #find the <div id=____>
            pile_soup = soup.find("div", {"id":name})
            for card_soup in pile_soup.contents:
                card_tuple = self.felt_to_tuple(card_soup['class'][-1])
                if (None in card_tuple):
                    pass
                else:
                    pile.append((card_tuple[0], str(card_tuple[1])))
            piles.append(pile)

        free = []
        freeFilled = 0
        for i in range(1, 5):
            name = "temp"+str(i)
            free_soup = soup.find("div", {"id":name})
            card = None
            for card_soup in free_soup.contents:
                card_tuple = self.felt_to_tuple(card_soup['class'][-1])
                if (None in card_tuple):
                    pass
                else:
                    card = (card_tuple[0], str(card_tuple[1]))
            free.append(card)
            if card != None:
                freeFilled += 1

        finish = [(0, 'D'), (0, 'C'), (0, 'H'), (0, 'S')]
        for i in range(1,5):
            name = "good"+str(i)
            finish_soup = soup.find("div", {"id":name})
            for card_soup in finish_soup.contents:
                card_tuple = self.felt_to_tuple(card_soup['class'][-1])
                if (None in card_tuple):
                    pass
                else:
                    finish[i-1] = (card_tuple[0], str(card_tuple[1]))
        return (piles, free, freeFilled, finish)

    #convert felt ('c-2D') to tuple (card, suit)
    def felt_to_tuple(self, felt):
        felt_list = felt.split('-')
        if ('empty' in felt_list):
            return (None, None)
        else:
            if(felt_list[1][0] == 'F'):
                return (None, None)
            if(felt_list[1][1] == '0'):
                card = 10
                suit = felt_list[1][2]
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
    def drag(self, driver, src_felt, dst_felt, check_column):
        
        source = driver.find_element_by_class_name(src_felt)
        if dst_felt[0] == 'c':
            target = driver.find_element_by_class_name(dst_felt)
        else:
            target = driver.find_element_by_id(dst_felt)
        
        ActionChains(driver).click_and_hold(source).perform()
        if dst_felt[0] == 'c':
            offset = 80
        else:
            offset = 0
        ActionChains(driver).move_to_element(target).move_by_offset(0, offset).perform()
        time.sleep(0.15)
        ActionChains(driver).release().perform()
        #check that it ended up in the proper destination
        html = driver.page_source
        soup = BeautifulSoup(html)
        pile_soup = soup.find("div", {"id":check_column})
        check_felt = pile_soup.contents[-1]['class'][-1]
        if (check_felt == src_felt):
            return True
        else:
            print 'Not carried out.'
            return False 
        return True
TAS()