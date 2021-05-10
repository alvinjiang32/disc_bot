# Discord Betting Bot

## Overview
This bot will be used on the Discord server to track bets by users and provide them with the ability to create bets, delete bets, and update bets.
</br></br>
This bot will use python and will be hosted for free on Heroku and MongoDB.

### __Features__
#### Done
- [x] Ability to create a wallet
- [x] Place a bet
- [x] Transfer funds
- [x] View Leaderboard
- [x] View Balance
- [x] Get bonuses
- [x] Help menu
- [x] View all previous bets
- [x] View personal active and previous bets

#### To Do
- [ ] Update bet statuses/transaction of successful bet
- [ ] Create job to remove expired bets
- [ ] Design transaction flow for won bet
- [ ] Implement transaction flow for won bet
- [ ] Change architecture to microservices (one for listening to users, one for automatically removing expired bets, ...)

### __Records__
**Key**   | **Value**  
-----     | ------
Bets      | <BET_ DETAILS, BET_AMOUNT, EXPIRATION>
