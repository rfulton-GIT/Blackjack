This Project is about analyzing the Game of 21, also known as Blackjack. As a disclaimer, I am definitely not the first person to do this, and there are probably many people
who have done it better than me. 

In the file "histo.py", I wrote code to allow the user to play Blackjack against a dealer who hits until reaching a hand valued at 17.
To start a new game of 1000 rounds, call the function newGame(). If you want to change the number of rounds, just change the global variable near the top.

In the same file, you can call the function histogram with input numIterations to generate a histogram modelling the probabilistic distribution
of profit/loss of a hard-coded playing/betting strategy which I borrowed from the website blackjackapprenticeship.com. Before calling histogram, make sure 
to change PLAYERTYPE to "auto". The input numIterations governs the number of trials used in constructing the histogram

In the file "strategy.py", I'm writing code to generate the optimal playing strategy for Blackjack. This is still a bit of a work in progress.
I'm not fully confident that the strategy is correct in all cases, I'm not happy with the runtime, and I want to make the strategy more comprehensive.
