import copy
import time
import random

# Webdata:

# Index   0      1       2      3       4       5       6      7
#         COL0   COL1    Col2   COL3    COL4    COL5    COL6   COL7

# 0  Back        (10,'H')
# 1   .          (9, 'C')
# .   .          (13, 'S')
# .   .
# n  Front

class Board:
    """The representation of the freecell board."""

    def __init__(self):
        self.colFree = (None, None, None, None)
        self.freeFilled = 0
        self.colFinish = ((0, 'D'), (0, 'C'), (0, 'H'), (0, 'S'))
        self.cols = ((None, None), (None, None), (None, None), (None, None), 
                    (None, None), (None, None), (None, None), (None, None))

    def fill(self, colFree, freeFilled, colFinish, cols):
        self.colFree = tuple(colFree)
        self.freeFilled = freeFilled
        self.colFinish = tuple(colFinish)
        self.cols = cols_get_immutable(cols)

    def fill_web(self, webdata):
        self.cols = cols_get_immutable(webdata)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.cols == other.cols and self.colFinish == other.colFinish:
                for freeCell in self.colFree:
                    if freeCell not in other.colFree:
                        return False
                return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        temp_colfree = list(self.colFree)
        temp_colfree.sort(key=sort_temp)
        return hash((self.cols, tuple(temp_colfree), self.colFinish))
    def move_cc(self, fromCell, to):
        newBoardCols = cols_get_mutable(self.cols)
        newBoardCols[to].append(newBoardCols[fromCell].pop())
        newBoard = Board()
        newBoard.fill(self.colFree, self.freeFilled, self.colFinish, newBoardCols)
        if self.cols[to][-1] == None:
            destination = 'work' + str(to+1)
        else:
            destination = tuple_to_felt(self.cols[to][-1])
        return (newBoard, (self.cols[fromCell][-1], destination, 'work' + str(to+1), 'work' + str(fromCell+1)))

    def move_col_free(self, fromCell, to):
        newBoardCols = cols_get_mutable(self.cols)
        newBoardFree = list(self.colFree)
        newBoardFree[to] = newBoardCols[fromCell].pop()
        newBoard = Board()
        newBoard.fill(newBoardFree, self.freeFilled + 1, self.colFinish, newBoardCols)
        return (newBoard, (self.cols[fromCell][-1], 'temp' + str(to+1), 'temp' + str(to+1), 'work' + str(fromCell+1)))

    def move_free_col(self, fromCell, to):
        newBoardCols = cols_get_mutable(self.cols)
        newBoardFree = list(self.colFree)
        newBoardCols[to].append(newBoardFree[fromCell])
        newBoardFree[fromCell] = None
        newBoard = Board()
        newBoard.fill(newBoardFree, self.freeFilled - 1, self.colFinish, newBoardCols)
        if self.cols[to][-1] == None:
            destination = 'work' + str(to+1)
        else:
            destination = tuple_to_felt(self.cols[to][-1])
        return (newBoard, (self.colFree[fromCell], destination, 'work' + str(to+1), 'temp' + str(fromCell+1)))

    def move_free_finish(self, fromCell, to):
        newBoardFree = list(self.colFree)
        newBoardFinish = list(self.colFinish)
        newBoardFinish[to] = newBoardFree[fromCell]
        newBoardFree[fromCell] = None
        newBoard = Board()
        newBoard.fill(newBoardFree, self.freeFilled - 1, newBoardFinish, self.cols)
        return (newBoard, (self.colFree[fromCell], 'good' + str(to+1), 'good' + str(to+1), 'temp' + str(fromCell+1)))

    def move_col_finish(self, fromCell, to):
        newBoardCols = cols_get_mutable(self.cols)
        newBoardFinish = list(self.colFinish)
        newBoardFinish[to] = newBoardCols[fromCell].pop()
        newBoard = Board()
        newBoard.fill(self.colFree, self.freeFilled, newBoardFinish, newBoardCols)
        return (newBoard, (self.cols[fromCell][-1], 'good' + str(to+1), 'good' + str(to+1), 'work' + str(fromCell+1)))

    # Check valididy of moves
    def is_valid_cc(self, fromCell, to):
        if len(self.cols[fromCell]) == 2:
            return False
        if len(self.cols[to]) == 2:
            return True
        return valid_move(self.cols[fromCell][-1], self.cols[to][-1])

    def is_valid_col_free(self, fromCell, to):
        if len(self.cols[fromCell]) == 2 or self.colFree[to] != None:
            return False
        return True

    def is_valid_free_col(self, fromCell, to):
        if self.colFree[fromCell] == None:
            return False
        if len(self.cols[to]) == 2:
            return True
        return valid_move(self.colFree[fromCell], self.cols[to][-1])

    def is_valid_free_finish(self, fromCell, to):
        if self.colFree[fromCell] == None:
            return False
        return valid_finish(self.colFree[fromCell], self.colFinish[to])

    def is_valid_col_finish(self, fromCell, to):
        if len(self.cols[fromCell]) == 2:
            return False
        return valid_finish(self.cols[fromCell][-1], self.colFinish[to])

    def is_winning_board(self):
        for i in range(4):
            if self.colFinish[i][0] != 13:
                return False
        return True

    def bad_placed(self):
        num_badly_placed = 0;
        for col in self.cols:
            if len(col) > 3:
                for i in range(2, len(col)-1):
                    cardA = col[i]
                    cardB = col[i+1]
                    if (cardA[0] != cardB[0]+1) or (suit_to_color(cardA[1]) == suit_to_color(cardB[1])):
                        num_badly_placed += 1
        return num_badly_placed

    def free_cells(self):
        open_cols = 0
        for col in self.cols:
            if len(col) == 2:
                open_cols += 1
        openFreeCells = 4 - self.freeFilled + open_cols
        return openFreeCells

    def min_finish(self):
        minFinish = self.colFinish[0][0]
        for col in self.colFinish:
            if col[0] < minFinish:
                minFinish = col[0]
        return minFinish

    def max_finish(self):
        maxFinish = self.colFinish[0][0]
        for col in self.colFinish:
            if col[0] > maxFinish:
                maxFinish = col[0]
        return maxFinish

    def difference_finish(self):
        return self.max_finish()-self.min_finish()

    def sum_of_bottom(self):
        sum_cols = 0
        for col in self.cols:
            if len(col) > 2:
                sum_cols += col[3][0]
        return 100-sum_cols

    def depth(self):
        minFinish = self.min_finish()

        depths = []
        for colFinish in self.colFinish:
            if colFinish[0] == 13:
                continue
            next_card = (colFinish[0]+1, colFinish[1])
            if next_card in self.colFree:
                depths.append(0)
                continue

            next_depth = 0
            for col in self.cols:
                if next_card in col:
                    next_depth = len(col)-col.index(next_card)
            depths.append((next_depth+1) / (colFinish[0]-minFinish+1))

        total_depth = 0
        if len(depths) > 0:
            total_depth = sum(depths)

        return total_depth

    def cards_completed(self):
        cards_completed = 0
        for i in range(4):
            cards_completed += self.colFinish[i][0]
        return cards_completed

    def heuristic(self):
        heuristic = 0

        cc = self.cards_completed() * 450
        fc = self.free_cells()*3

        difference = self.difference_finish()
        if difference < 2:
            df = 0
        elif difference == 2:
            df = 50
        else:
            df = 200*difference
        depth = 3*self.depth()
        return (cc, -df, fc, -depth)

    def evaluate(self):
        if self.is_winning_board():
            return 100000
        return sum(self.heuristic())

    def count_cards(self):
        number_of_cards = 0
        for col in self.cols:
            number_of_cards += len(col)-2
        for col in self.colFinish:
            number_of_cards += col[0]
        for col in self.colFree:
            if col != None:
                number_of_cards += 1
        return number_of_cards

    def display(self):
        print '{0}\t{1}\t{2}\t{3}  |  {4}\t{5}\t{6}\t{7}'.format(
                    ctt(self.colFree[0]), ctt(self.colFree[1]), 
                    ctt(self.colFree[2]), ctt(self.colFree[3]),
                    ctt(self.colFinish[0]), ctt(self.colFinish[1]),
                    ctt(self.colFinish[2]), ctt(self.colFinish[3]))
        print '--------------------------------------------------------'
        max_length = maxLength(self.cols)
        for row_index in range(2, max_length):
            colString = ''
            for col_index in range(8):
                if row_index < len(self.cols[col_index]):
                    colString += '|' + ctt(self.cols[col_index][row_index]) + '\t'
                else:
                    colString += '|\t'
            print colString
        for row_index in range(20-max_length):
            colString = ''
            for col_index in range(8):
                colString += '|\t'
            print colString
        
        print ''

def tuple_to_felt(card_tuple):
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

def cols_get_mutable(cols):
    return [list(cols[0]), list(cols[1]), list(cols[2]), 
        list(cols[3]), list(cols[4]), list(cols[5]), 
        list(cols[6]), list(cols[7])]

def cols_get_immutable(cols):
    return (tuple(cols[0]), tuple(cols[1]), tuple(cols[2]), 
            tuple(cols[3]), tuple(cols[4]), tuple(cols[5]), 
            tuple(cols[6]), tuple(cols[7]))

def maxLength(cols):
    lengths = []
    for col in cols:
        lengths.append(len(col))
    return max(lengths)

def ctt(card):
    if card == None:
        return '  '
    return str(card[0]) + str(card[1])

def valid_finish(from_card, to_card):
    if from_card[1] == to_card[1] and from_card[0] == to_card[0]+1:
        return True

def valid_move(from_card, to_card):
        # Compare rank
        if (from_card[0] == to_card[0]-1):
            # Compare color
            if (suit_to_color(from_card[1]) != (suit_to_color(to_card[1]))):
                return True
        return False

def suit_to_color(a):
    """Red is 1. Black is 0."""
    return (a == 'H' or a == 'D')

def sort_temp(pair):
    if pair == None:
        return -1
    rank = pair[0]
    suit = pair[1]
    if suit == 'H':
        suitkey = 0
    elif suit == 'D':
        suitkey = 1
    elif suit == 'S':
        suitkey = 2
    else:
        suitkey = 3
    return rank*10+suitkey


def generate_web_data():
    random.seed()
    cards = []
    for rank in range(13):
        for suit in ['D', 'H', 'C', 'S']:
            cards.append((rank+1, suit))
    cols = [[], [], [], [], [], [], [], []]
    for column in cols:
        column.append(None)
        column.append(None)
    col = 0
    while len(cards) > 0:
        card = cards.pop(random.randrange(len(cards)))
        cols[col].append(card)
        col = (col+1) % 8

    return cols

## Returns: (Did win?, should continue?, Path)
def board_search(start_board): 
    allboards = {}
    boards = [(start_board, [])]
    time_start = time.time()
    while len(boards) > 0:
        if(time.time()-time_start > 180):
            return(False, [])
        (board, path) = boards.pop(0)
        print board.heuristic()
        # board.display()
        if board.is_winning_board():
            return (True, path)
        newBoards = []
        for colA in range(8):
            for colB in range(colA):
                if board.is_valid_cc(colA, colB):
                    (newBoard, move) = board.move_cc(colA, colB)
                    newBoards.append((newBoard, path + [move]))
                if board.is_valid_cc(colB, colA):
                    (newBoard, move) = board.move_cc(colB, colA)
                    newBoards.append((newBoard, path + [move]))
            for freeCell in range(4):
                if board.is_valid_free_col(freeCell, colA):
                    (newBoard, move) = board.move_free_col(freeCell, colA)
                    newBoards.append((newBoard, path + [move]))
                if board.is_valid_col_free(colA, freeCell):
                    (newBoard, move) = board.move_col_free(colA, freeCell)
                    newBoards.append((newBoard, path + [move]))
            for finishCell in range(4):
                if board.is_valid_col_finish(colA, finishCell):
                    (newBoard, move) = board.move_col_finish(colA, finishCell)
                    newBoards.append((newBoard, path + [move]))
        for freeCell in range(4):
            for finishCell in range(4):
                if board.is_valid_free_finish(freeCell, finishCell):
                    (newBoard, move) = board.move_free_finish(freeCell, finishCell)
                    newBoards.append((newBoard, path + [move]))
        for newBoard in newBoards:
            if newBoard[0] not in allboards:
                allboards[newBoard[0]] = True
                boards.append(newBoard)
        boards.sort(key=lambda pair: pair[0].evaluate(), reverse=True)
    return (False, None)

def play_in_terminal():
    testBoard = Board()
    testBoard.fill_web(generate_web_data())
    storeboard = Board()
    while(True):
        print ''
        testBoard.display()
        command = raw_input('Move: ').split('_')
        if command[0] == 'cc':
            if not testBoard.is_valid_cc(int(command[1]), int(command[2])):
                print 'Invalid move.'
                continue
            testBoard = testBoard.move_cc(int(command[1]), int(command[2]))
        elif command[0] == 'cfree':
            if not testBoard.is_valid_col_free(int(command[1]), int(command[2])):
                print 'Invalid move.'
                continue
            testBoard = testBoard.move_col_free(int(command[1]), int(command[2]))
        elif command[0] == 'freec':
            if not testBoard.is_valid_free_col(int(command[1]), int(command[2])):
                print 'Invalid move.'
                continue
            testBoard = testBoard.move_free_col(int(command[1]), int(command[2]))
        elif command[0] == 'cfinish':
            if not testBoard.is_valid_col_finish(int(command[1]), int(command[2])):
                print 'Invalid move.'
                continue
            testBoard = testBoard.move_col_finish(int(command[1]), int(command[2]))
        elif command[0] == 'freefinish':
            if not testBoard.is_valid_free_finish(int(command[1]), int(command[2])):
                print 'Invalid move.'
                continue
            testBoard = testBoard.move_free_finish(int(command[1]), int(command[2]))
        elif command[0] == 'store':
            storeboard = testBoard
        elif command[0] == 'compare':
            if storeboard == testBoard:
                print 'Stored board and test board are equal.'
            else:
                print 'Stored board and test board are NOT equal.'
        elif command[0] == 'quit':
            break
        else:
            print 'Not a valid command.'


def simulate():
    testBoard = Board()
    testBoard.fill_web(generate_web_data())
    testBoard.display()
    (did_win, path) = board_search(testBoard)
    if did_win:
        path[-1].display()
        print 'You won! Number of moves: ' + str(len(path)) + '.'
    else:
        print 'No solution.'

# play_in_terminal()
# simulte()
