# Mental_poker_PSAB
A decentralized approach to Mental Poker using SRA, which allows players to play a 5-card draw game of poker on the Ethereum blockchain.

# Setup
The code related to the management of clients and the game has been written in Python.
Therefore, a Python distribution is required to run it. The project was developed and tested with Python 3.11.6, but there shouldn't be any compatibility issues with other versions. The repository also includes a "requirements.txt" file containing the libraries that need to be installed in order to execute all of the Python code.

As it relates to the smart contract, the code was written in Solidity. To execute it, we used the Remix IDE, which is available online at the Remix IDE.

The project was created using compiler version 0.8.18+commit.87f61d96, and we activated the compiler optimization set to 200 runs to reduce the bytecode size.

For development and debugging, we used a software for simulating a local blockchain: Ganache. Remix interfaces with Ganache during the contract deployment phase.

In the repository, there is a "addresses.txt" file containing the addresses of the local blockchain node used during development. To obtain these addresses, Ganache needs to be configured with the hostname of the server set to 127.0.0.1 and the port set to 8545. It's entirely possible to choose different configurations but in that case, the "addresses.txt" file and the files related to wallet addresses will need to be modifed by inserting the new addresses.
