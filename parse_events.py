from __future__ import print_function
import re
import csv
import datetime
import sys
import json
import os

from collections import defaultdict
from StringIO import StringIO
from os import listdir
from os.path import isfile, join

class GameState(object):
    def __init__(self):
        # empty 2-by-9 array representing the 9 active players on each team
        self.players = []
        for i in range(2):
            self.players.append([None] * 12)
        self.game_id = None
        self.date = None
        self.names = {}
        self.teams = {}

        self.bases = [None, None, None]
        self.outs = 0
        self.score = [0, 0]

        # map of each pitcher to the set of all batters they struck out
        self.k_graph = defaultdict(set)

        # map of each pitcher/batter pair to a list of times the pitcher struck
        # out the batter
        self.strikeouts = defaultdict(list)

    def load_teams(self, path):
        f = open(path)
        reader = csv.reader(f, delimiter=',')
        for l in reader:
            self.teams[l[0]] = l[2] + ' ' + l[3]

    def parse_line(self, line):
        # https://www.retrosheet.org/datause.txt

        if line[0] == 'com':
            pass

        # unique id for the game
        elif line[0] == 'id':
            self.game_id = line[1]

        # metadata about the game
        elif line[0] == 'info':
            if line[1] == 'date':
                self.date = datetime.datetime.strptime(line[2], '%Y/%m/%d')
            if line[1] == 'visteam':
                self.visteam = line[2]
            if line[1] == 'hometeam':
                self.hometeam = line[2]

        elif line[0] == 'version':
            pass

        # information about the starting lineup for each team
        elif line[0] == 'start':
            player = line[1]
            team = int(line[3])
            pos = int(line[-1]) - 1
            self.players[team][pos] = player
            self.names[player] = line[2]

        # information about a particular play
        elif line[0] == 'play':
            inning, team = int(line[1]), int(line[2])
            batter = line[3]
            pitcher = self.players[1 - team][0]
            play = line[-1]

            if '.' in play:
                play, moves = play.split('.')

            if '/' in play:
                play = play.split('/')[0]

            moves = moves.split(';')
            for m in moves:
                start, end = m.split('-')

                # runner scored
                if end == 'H':
                    self.score[team] += 1
                # runner advanced from home
                elif start == 'B':
                    self.bases[int(end)-1] = player
                # runner advanced from one base to another
                else:
                    self.bases[int(end)-1] = self.bases[int(start)-1]
                    self.bases[int(start)-1] = None

            # if we've already accounted for the batter getting on base, we're done
            if player not in bases:
                # single or walk or hit by pitch
                if play in ['W', 'HP'] or play[0] == 'S':
                    self.bases[0] = player
                # double
                if play[0] == 'D':
                    self.bases[1] = player
                # triple
                if play[0] == 'T':
                    self.bases[2] = player
                # home run
                if play == 'HR':
                    self.score[team] += 1

            # did this result in an out?
            if play[0] in map(str, range(1, 10)) + ['K']:
                self.outs += 1
                assert self.outs <= 3

            # is this a strikeout?
            if play[0] == 'K':
                self.k_graph[pitcher].add(batter)

                # `team` is the batter's team, so team == 0 means the away team
                # struck out
                if team == 0:
                    self.strikeouts[(pitcher, batter)].append((self.hometeam,
                                                               self.visteam,
                                                               self.date))
                else:
                    self.strikeouts[(pitcher, batter)].append((self.visteam,
                                                               self.hometeam,
                                                               self.date))

        # information about a substitution
        elif line[0] == 'sub':
            player = line[1]
            team = int(line[3])
            pos = int(line[-1]) - 1
            self.players[team][pos] = player
            self.names[player] = line[2]

        elif line[0] == 'data':
            pass


    def run(self, path):
        f = open(path)
        reader = csv.reader(f, delimiter=',')
        for l in reader:
            self.parse_line(l)

            if self.


    def do_search(self, start, end):
        starts = []
        ends = []

        if start not in self.names:
            for k, v in self.names.items():
                if start.lower() == v.lower():
                    starts.append(k)

        if end not in self.names:
            for k, v in self.names.items():
                if end.lower() == v.lower():
                    ends.append(k)

        for s in starts:
            for e in ends:
                res = self.search(s, e)
                if res is not None:
                    return res

        return None


    def search(self, start, end):
        q = [[p] for p in self.k_graph[start]]
        seen = set()

        while q:
            path = q.pop(0)
            if path[-1] == end:
                return [start] + path

            for p in self.k_graph[path[-1]]:
                if p not in seen:
                    seen.add(p)
                    q.append(path + [p])

        print("No path")


    def graph(self):
        import pandas as pd
        import networkx as nx
        import matplotlib.pyplot as plt

        ks = []
        for p, batters in self.k_graph.items():
            for k in batters:
                ks.append((p, k))

        df = pd.DataFrame(columns=['source', 'target'], data=ks)
        return nx.from_pandas_edgelist(df)
        nx.draw(G, with_labels=False)
        plt.show()


    def to_json(self):
        json.dump({k: list(v) for k, v in self.k_graph.items()}, open('k_graph.json', 'w'))
        json.dump({'.'.join(k): [[s[0], s[1], s[2].strftime('%m/%d/%Y')] for s in v] for k, v in self.strikeouts.items()}, open('strikeouts.json', 'w'))
        json.dump(self.names, open('names.json', 'w'))



def parse(path):
    oldpath = os.getcwd()
    os.chdir(path)
    gs = GameState()

    files = [f for f in listdir('./') if isfile(f)
             and re.match('^\d{4}\w+\.EV\w$', f)]

    for f in files:
        gs.run(f)

    gs.load_teams('./TEAMABR.TXT')
    print('Finished parsing %d edges' % len(gs.k_graph), file=sys.stderr)

    os.chdir(oldpath)

    return gs


def load(path):
    gs = GameState()

    gs.k_graph = json.load(open(join(path, 'k_graph.json')))
    gs.strikeouts = json.load(open(join(path, 'strikeouts.json')))
    gs.names = json.load(open(join(path, 'names.json')))
    gs.load_teams(join(path, 'TEAMABR.TXT'))

    print('Finished loading %d edges' % len(gs.k_graph), file=sys.stderr)

    return gs


from flask import Flask, request, render_template
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route('/', methods=['GET'])
def search():
    start = request.args.get('start', 'Adam Ottavino')
    end = request.args.get('end', 'Babe Ruth')

    path = gs.do_search(start, end)

    if path:
        text = '<h3>%s could strike out %s.</h3>\n' % (gs.names[path[0]],
                                                       gs.names[path[-1]])

        for i in range(len(path) - 1):
            p = path[i]
            b = path[i+1]
            text += "<p>%s struck out %s:\n<ul>\n" % (gs.names[p], gs.names[b])

            for k in gs.strikeouts[(p, b)]:
                text += "<li>pitching for the %s against the %s on %s</li>\n" % (
                    gs.teams[k[0]], gs.teams[k[1]], k[2].strftime('%m/%d/%Y'))

            text += "</ul></p>\n"
    else:
        text = '<h3>%s couldn\'t strike out %s.</h3>' % (start, end)

    return render_template('index.html', start=start, end=end, text=text)


if __name__ == '__main__':
    gs = parse('./data')
    app.run(host="0.0.0.0", port=443,
            ssl_context=('/etc/letsencrypt/live/transitivestrikeouts.com/fullchain.pem',
                         '/etc/letsencrypt/live/transitivestrikeouts.com/privkey.pem'))
