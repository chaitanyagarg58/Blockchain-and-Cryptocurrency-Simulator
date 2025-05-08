# DEX Simulation Project

This project simulates a Decentralized Exchange (DEX) using an Automated Market Maker (AMM) model. It includes Solidity smart contracts, simulation scripts, data visualization, and an analytical report covering slippage, arbitrage, liquidity provider (LP) dynamics, and gas efficiency.

---

# Running Instructions

Upload the ```contracts``` and ```scripts``` folder on [Remix IDE](https://remix.ethereum.org/). The contracts can be compiled and deployed as usual.

The scipts require contract addresses to be updated in code in lines:

- ```simulate_DEX.js``` : Line 223 - 225
- ```simulate_arbitrage.js``` : Line 117 - 121

Ensure the directories are at root level of IDE. The scripts have been tested on the Remix Desktop IDE, and the path to contract artifacts are set accordingly. Although the same paths seem to work corectly on browser as well, in case of any error in loading artifacts, please correct the path in lines:

- ```simulate_DEX.js``` : Line 195, 201, 207
- ```simulate_arbitrage.js``` : Line 83, 89, 94, 101

---

# Code Files

- ```contracts/Token.sol``` :  Basic ERC20 token implementation (used in DEX)
- ```contracts/LPToken.sol``` : ERC20 token representing LP shares
- ```contracts/DEX.sol``` : Core AMM-based DEX contract
- ```contracts/arbitrage.sol``` : Arbitrage contract to exploit price differences

- ```scripts/simulate_DEX.sol``` : Deploy and simulate trading/liquidity provisioning
- ```scripts/simulate_arbitrage.sol``` : Simulate profitable and unprofitable arbitrage across DEXs

# Visualisation Script
Running ```simulate_DEX.js``` on Remix IDE prints a csv format table on console on successful completion. Copy and paste this table in a ```.csv``` file.

```
Usage: python visualization.py <path_to_csv>
```
Generates all the plots for visualization.