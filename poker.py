'''
lessons learned:
careful with attributes and methods that have similar names (all_in versus all_in_ed, small_blind vs set_small_blind)
don't shadow function variable with for loop variable (or other similar shadowing)

'''

'''
To-do: (in sort-of priority order)

Regarding workflow:
Optimise testing process: perhaps hard-code some starting inputs (player names and stacks), 
    and use card = Card.new('Qh') etc to force hands (A23456789TJQK, hdcs)
    

Critical:
after each hand, must remove dead (stack = zero) players from players_dict (do this at the betting stage)
check, bet (as kind-of calls and raises, except with different prompts, inputs, and remarks)
implement all_in and side pots (has many consequences)
    what if to call is larger or equal to stack? 
    allow typing >= stack when asked to raise to signify all_in

Important:
tag for "last aggressor" determined on the river (for showdown priority)
implement tyers
note to self: during pre-flop stage, min-raise has some special cases. Try to figure these out. 

stupid-proofing:
max num players
input checking (min raise etc)

not-so-important:
implement sit-out for the hand
implement re-buy
implement changing (increasing) blinds (like a tournament)
'''

from treys import Card
from treys import Evaluator
from treys import Deck

players_dict = dict()

class Engine:
    def __init__(self, table, num_players):
        self.table = table
        small_blind = self.table.small_blind
        big_blind = self.table.big_blind
        for k in range(num_players):
            player_name = input(f"Name of player {k+1}: ")
            player_stack = int(input(f"Stack of player {k+1}: "))
            global players_dict
            players_dict[k] = Player(player_name, player_stack, small_blind, big_blind)
        self.hand_count = 0
        self.priority = 0

    def new_priority(self):
        old = self.priority
        global players_dict
        remaining = [*players_dict] # fancy way of saying list(dict); gets the keys from dict
        raw_new = old + 1
        if raw_new <= max(remaining):
            larger = [k for k in remaining if k >= raw_new]
            return min(larger)
        else:
            return min(remaining)

    def summary(self):
        pass

    def play(self):
        while True:
            start = input(f"Do you want to start hand number {self.hand_count + 1}?")
            if start == "yes":
                pass
            else:
                self.summary()
                break
            self.table.new_game(self.priority)
            self.hand_count += 1
            self.priority = self.new_priority()

class Betting:

    deck = Deck()
    evaluator = Evaluator()
    pot = None
    community = None

    def __init__(self, small_blind, big_blind):
        global players_dict
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.previous_bet = 0
        self.to_match = 0
        self.minimum_bet = big_blind
        self.pot = 0
        # self.side_pots = [0]*len(players_dict) #probably a better structure for this

    def new_game(self, priority):
        if self.pre_flop(priority) == "finished":
            return
        if self.flop(priority) == "finished":
            return
        if self.turn(priority) == "finished":
            return
        if self.river(priority) == "finished":
            return
        if self.showdown() == "finished":
            return
    # def remove_player(self, players, index_to_remove):
    #     del(players[index_to_remove])
    #     for k in range(index_to_remove, len(players)):
    #         available = list(j for j in list(players) if j >= k)
    #         if len(available) != 0:
    #             players[k] = players.pop(min(available))
    #         else:
    #             break

    # def next_player_index(self, players, old_player_index):

    def key_list_with_max_value(self, d):
        k = list(d.keys())
        v = list(d.values())
        maximal_list = []
        max_val = max(v)
        for i in range(len(k)):
            if v[i] == max_val:
                maximal_list.append(k[i])
        return maximal_list

    def score_to_rank_string(self, score_integer):
        eclass = self.evaluator.get_rank_class(score_integer)
        return self.evaluator.class_to_string(eclass)

    def showdown(self):
        # NOTE: to implement side pot decisions, need to implement win/tie situations on each side pot. Not done yet.
        for a_player in players_dict.values():
            if not a_player.folded:
                score = self.evaluator.evaluate(self.community, a_player.hole_cards)
                a_player.score = score
        players_scores = dict()
        for b_player in players_dict.values():
            if not b_player.folded:
                players_scores[b_player] = b_player.score
        top_players_list = self.key_list_with_max_value(players_scores)
        return self.winner_or_tiers(top_players_list)

    def winner_or_tiers(self, top_players_list):
        if len(top_players_list) == 1:
            return self.winner(top_players_list)
        else:
            return self.tier(top_players_list)

    def winner(self, top_players_list):
        winner_player = top_players_list[0]
        winner_score = winner_player.score
        winning_rank_string = self.score_to_rank_string(winner_score)
        print(f"Player {winner_player.name} wins the {self.pot} pot with {winning_rank_string}!")
        for a_player in players_dict.values():
            a_player.all_in_ed = False
            a_player.can_act = True
            a_player.folded = False
            a_player.hole_cards = None
            a_player.score = None
        winner_player.stack += self.pot
        self.pot = 0
        self.previous_bet = 0
        self.to_match = 0
        self.community = None
        return "finished"

    def tier(self, top_players_list):
        print("A tying situation is not yet implemented.")
        return "finished"

    
    def pre_flop(self, priority):
        player_index_to_act = priority
        global players_dict

        for a_player in players_dict.values():
            a_player.hole_cards = self.deck.draw(2)
            pretty_hole_cards = Card.print_pretty_cards(a_player.hole_cards)
            print(f"Player {a_player.name}'s hole cards are {pretty_hole_cards}.")

        small_blind_player = players_dict[player_index_to_act]
        self.set_small_blind(small_blind_player, self.small_blind)

        player_index_to_act = (player_index_to_act + 1) % (len(players_dict))
        big_blind_player = players_dict[player_index_to_act]
        self.set_big_blind(big_blind_player, self.big_blind)

        player_index_to_act = (player_index_to_act + 1) % (len(players_dict))
        self.previous_bet = self.big_blind
        self.to_match = self.big_blind
        # note: even if BB shoves less than 1 BB, the next player has to call 1 BB
        return self.normal_betting(player_index_to_act)

    def flop(self, priority):
        player_index_to_act = priority
        self.community = self.deck.draw(3)
        pretty_flop = Card.print_pretty_cards(self.community)
        print(f"The flop is {pretty_flop}.")

        return self.normal_betting(player_index_to_act)

    def turn(self, priority):
        player_index_to_act = priority
        turn = self.deck.draw(1)
        pretty_turn = Card.print_pretty_card(turn)
        print(f"The turn is {pretty_turn}.")
        self.community.append(turn)
        pretty_community = Card.print_pretty_cards(self.community)
        print(f"The community is {pretty_community}.")

        return self.normal_betting(player_index_to_act)

    def river(self, priority):
        player_index_to_act = priority
        river = self.deck.draw(1)
        pretty_river = Card.print_pretty_card(river)
        print(f"The river is {pretty_river}.")
        self.community.append(river)
        pretty_community = Card.print_pretty_cards(self.community)
        print(f"The community is {pretty_community}.")

        return self.normal_betting(player_index_to_act)

    def normal_betting(self, player_index_to_act):
        global players_dict
        player_to_act = players_dict[player_index_to_act]
        while player_to_act.can_act:
            call_amount = self.to_match - player_to_act.stake
            player_action = input(f"Player {player_to_act.name}, you have {call_amount} to call. ")
            if player_action == 'raise':
                minimum_raise_total = max(2 * self.previous_bet, self.previous_bet + self.minimum_bet)
                # note: the above is also = the min bet at flop/turn/river
                min_add_raise = minimum_raise_total - player_to_act.stake
                raise_add_amount = int(input(f"Raise an additional how many chips? (min = {min_add_raise}) > "))
                if raise_add_amount >= min_add_raise:
                    self.upraise(player_to_act, raise_add_amount)
            elif player_action == 'call':
                self.call(player_to_act, call_amount)
            elif player_action == 'fold':
                self.fold(player_to_act)
                # check if only one player is left
                if self.only_one_unfolded():
                    return self.pre_showdown_finish()

            player_index_to_act = (player_index_to_act + 1) % (len(players_dict))
            player_to_act = players_dict[player_index_to_act]

        #the following 'sweeps' the stakes into a pot. NOTE: side pots are not handled
        for key, a_player in players_dict.items():
            self.pot += players_dict[key].stake
            players_dict[key].stake = 0
            if not(a_player.folded or a_player.all_in_ed):
                players_dict[key].can_act = True
            print(f"There is now {self.pot} in the pot.")
        self.to_match = 0
        self.previous_bet = 0

    def only_one_unfolded(self):
        incrementer = 0
        for key, a_player in players_dict.items():
            if not a_player.folded:
                incrementer += 1
        if incrementer == 1:
            return True
        else:
            return False

    def the_unfolded_player_key(self):
        for key in players_dict:
            if not players_dict[key].folded:
                return key

    def pre_showdown_finish(self):
        for a_player in players_dict.values():
            self.pot += a_player.stake
            print(f"The pot is {self.pot}.")
            a_player.stake = 0
        winner_player = players_dict[self.the_unfolded_player_key()]
        winner_player.stack += self.pot
        print(f"Player {winner_player.name} wins {self.pot}!")
        for b_player in players_dict.values():
            b_player.all_in_ed = False
            b_player.can_act = True
            b_player.folded = False
            b_player.hole_cards = None
            b_player.score = None
        self.pot = 0
        self.previous_bet = 0
        self.to_match = 0
        self.community = None
        return "finished"

    def call(self, player, amount):
        if player.stack > amount: # implement = and < later
            player.stack -= amount
            player.stake += amount
            print(f"Player {player.name} have called {amount}, and has a stack of {player.stack} left.")
            # self.previous_bet = amount # you do not update this during calls
            self.to_match = player.stake
            player.can_act = False

    def upraise(self, player, amount):
        global players_dict
        if player.stack > amount: #implement = and < later
            player.stack -= amount
            player.stake += amount
            print(f"Player {player.name} has raised {amount}, and has a stack of {player.stack} left.")
            self.previous_bet = amount # this is correct; remember to do this at S3, S4, S5 bets / raises
            self.to_match = player.stake
            for key, o_player in players_dict.items():
                if not(o_player.folded or o_player.all_in_ed):
                    # other_player.can_act = True
                    players_dict[key].can_act = True
                    print(f"Can {players_dict[key].name} act? {players_dict[key].can_act}.")
            player.can_act = False

    def check(self, player):
        pass

    def fold(self, player):
        player.folded = True
        player.can_act = False
        print(f"Player {player.name} has folded.")
        pass

    def all_in(self, player):
        pass

    def set_big_blind(self, player, amount):
        if player.stack > amount: # implement = and < later
            player.stack -= amount
            player.stake += amount
            print(f"Player {player.name} have staked big blind {amount}, and has a stack of {player.stack} left.")
            self.previous_bet = amount # not overridden; this is correct -- see if BB has < 1 BB
            # self.to_match = player.stake # overridden by normal_betting

    def set_small_blind(self, player, amount):
        if player.stack > amount: # implement = and < later
            player.stack -= amount
            player.stake += amount
            print(f"Player {player.name} have staked small blind {amount}, and has a stack of {player.stack} left.")

class Player(Betting):

    def __init__(self, name, stack, small_blind, big_blind):
        super().__init__(small_blind=small_blind, big_blind=big_blind)
        self.name = name
        self.stack = stack
        self.hole_cards = None
        self.stake = 0
        self.folded = False
        self.all_in_ed = False
        self.can_act = True
        self.score = None

    def hole_cards(self):
        self.hole_cards = self.deck.draw(2)

a_table = Betting(1,2)
a_game = Engine(a_table, 3)
a_game.play()

