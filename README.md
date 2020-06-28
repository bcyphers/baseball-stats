# Baseball stats repository

This has a couple of different scripts for parsing through RetroSheet data. I
may add more in the future.

## Transitive strikeout graph

Could Adam Ottavino strike out Babe Ruth? Could Babe Ruth strike out Mike Trout?
Thanks to graph theory, we have the answer.

Parses data from RetroSheet to find all strikeouts since 1919. Builds a directed
graph and uses BFS to find the shortest route from a pitcher to a hitter.

To run: 
```
$ pip install -r requirements.txt
python main.py
```

Credits:
[https://reddit.com/r/baseball/comments/df4ypv/adam_ottavinos_transitive_strikeout_of_babe_ruth/](https://old.reddit.com/r/baseball/comments/df4ypv/adam_ottavinos_transitive_strikeout_of_babe_ruth/)
[https://www.retrosheet.org/](https://www.retrosheet.org/)


## Man On Second rule

The MLB is changing the rules for the shortened 2020 season so that every extra
inning will start with a man on second. This is meant to shorten games, but how
well will it work?

code in man\_on\_2nd.py
