// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2;

contract Mental_Poker {
    // Status variables
    enum Status {matchmaking, shuffle, reveal_card, deal_card, stake, key_reveal, optimistic_verify, pay_to_verify}
    Status public status;
    uint8 public turn_index;
    address[] players_addresses;

    uint8 MAX_PLAYERS = 2;

    constructor() {
        status = Status.matchmaking;
        turn_index = 0;
    }

    function participate() public /*payable*/ {
        require(status == Status.matchmaking);

        players_addresses.push(msg.sender);

        // handle payment

        // If there are enough players game can start
        if (players_addresses.length >= MAX_PLAYERS) {
            status = Status.shuffle;
            // event
        }        
    }

    function get_my_turn_index() public view returns(uint8) {
        require(players_addresses.length > 0);
        
        uint8 index = MAX_PLAYERS;
        for (uint8 i=0; i<players_addresses.length; i++)
            if (players_addresses[i] == msg.sender)
                index = i;
        
        require(index != players_addresses.length);

        return index;
    }
}