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
        # empty 2-by-9 array
        self.players = []
        for i in range(2):
            self.players.append([None] * 12)
        self.game_id = None
        self.date = None
        self.k_graph = defaultdict(set)
        self.strikeouts = defaultdict(list)
        self.names = {}
        self.teams = {}

    def load_teams(self, path):
        f = open(path)
        reader = csv.reader(f, delimiter=',')
        for l in reader:
            self.teams[l[0]] = l[2] + ' ' + l[3]

    def parse_line(self, line):
        if line[0] == 'com':
            pass

        elif line[0] == 'id':
            self.game_id = line[1]

        elif line[0] == 'info':
            if line[1] == 'date':
                self.date = datetime.datetime.strptime(line[2], '%Y/%m/%d')
            if line[1] == 'visteam':
                self.visteam = line[2]
            if line[1] == 'hometeam':
                self.hometeam = line[2]

        elif line[0] == 'version':
            pass

        elif line[0] == 'start':
            player = line[1]
            team = int(line[3])
            pos = int(line[-1]) - 1
            self.players[team][pos] = player
            self.names[player] = line[2]

        elif line[0] == 'play':
            # is this a strikeout?
            if line[-1][0] == 'K':
                team = int(line[2])
                batter = line[3]
                pitcher = self.players[1 - team][0]
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


    def search(self, start, end):
        if start not in self.names:
            for k, v in self.names.items():
                if start.lower() == v.lower():
                    start = k

        if end not in self.names:
            for k, v in self.names.items():
                if end.lower() == v.lower():
                    end = k

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

@app.route('/search', methods=['GET'])
def search():
    start = request.args.get('start', 'Adam Ottavino')
    end = request.args.get('end', 'Babe Ruth')

    path = gs.search(start, end)

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
    app.run()
