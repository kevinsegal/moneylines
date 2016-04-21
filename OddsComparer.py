# from bs4 import BeautifulSoup
import re, time, sys, datetime, math
from config import CONFIG as config
import HTML_parser
import Emailer
import BettingDB
import random
import json

def print_json(json_object):
    print json.dumps(json_object, indent=4, sort_keys=True)
    print "\n"

class OddsComparer():

    def __init__(self):
        self.parser = HTML_parser.HTML_parser()
        self.bets_DB = BettingDB.BettingDB()
        self.emailer = Emailer.Emailer()
        self.games = {}
        self.date = datetime.datetime.now()

        random.seed(int(time.time()))

    def run(self):
        # get the money lines for each website
        while True:

            self.games = self.parser.get_moneylines()
            results = []

            # print_json(self.games)

            for sport in self.games:
                for group in self.games[sport]:
                    # check to see if game id exsists in
                    site = group["site"]
                    # print site
                    for game in group["moneylines"]:
                        # print game["game_time"]["day"]
                        # print game["game_time"]["day"] is None
                        # print_json(game)

                        # print game["game_time"]["day"] != None

                        if game["status"] == "upcoming":
                            game_id = self.bets_DB.get_game_id(game)
                            self.bets_DB.add_moneyline(game,game_id)

                            betting_result = self.compare_moneylines(game_id,game)

                            if betting_result:
                                results.append(betting_result)

                        else:
                            self.bets_DB.delete_id(game)

            if results:
                self.emailer.send_email(results)

            time_to_sleep = self.get_poisson_arrival_time(1/float(20*60))
            print "sleeping {} seconds".format(time_to_sleep)
            time.sleep(time_to_sleep)



    def compare_moneylines(self, game_id, game):
        # Look at current line
        # determine if the underdog is the home team or the away team, same with favourite

        # find lines with winning differences
        # store line details
        # return the best difference

        result = []

        if game["home_line"] > game["away_line"]:
            # the home team is the underdog and the away team is the favourite
            favourite = "home"
            underdog = "away"

        else:
            underdog = "away"
            favourite = "home"

        # betting on a team with +320 for 100 bucks and a team with -250 for 280
        # then if the + team wins then you get +320 -280 = 40 and if - team wins you get 112 - 100 = 12

        money_lines_to_compare = self.bets_DB.get_moneylines(game)

        for money_line in money_lines_to_compare:
            gametime_string = self.convert_timestamp_to_time_string(money_line["poll_time"])
            
            if money_line[favourite + "_line"] + game[underdog + "_line"] > 0:
                result.append("should have bet on {0} at {1} and {2} now".format(game[favourite+"_team"],
                    gametime_string, game[underdog+"_team"]))

            elif money_line[underdog + "_line"] + game[favourite + "_line"] > 0:
                result.append("should have bet on {0} at {1} and {2} now".format(game[underdog+"_team"],
                    money_line["poll_time"],game[favourite+"_team"]))


        return result

    def flush_games(self):
        self.games = {"live": [], "upcoming": []}    

    def convert_game_time_to_timestamp(self, time):
        pass

    def convert_timestamp_to_time_string(self,timestamp):
        game_datetime = datetime.datetime.fromtimestamp(timestamp)
        game_string = str(game_datetime.day) + ":" + str(game_datetime.hour) + \
            ":" + str(game_datetime.minute) + " (Day:Hour:Minute)"

        return game_string

    def get_poisson_arrival_time(self, lambda_val):
        return -1*math.log(max(0.0001,random.random()))/float(lambda_val)

if __name__ == "__main__":
    odds = OddsComparer()
    odds.run()
    # odds.add_moneylines_to_database()
    # odds.flush_games()


