// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2;

contract Mental_Poker {
    // Status variables
    enum Status {matchmaking, shuffle, draw_card, stake, key_reveal, optimistic_verify, pay_to_verify}
    Status public status;
    uint8 public turn_index;
    uint8 public draw_index;
    uint8 public topdeck_index;

    // Public game infos
    uint256 n;
    uint8[] deck_coding;
    uint256[] encrypted_deck;
    address[] players_addresses;

    event shuffle_event(uint8 turn_index);
    event draw_event(uint8 turn_index, uint8 draw_index, uint8 topdeck_index, uint8 hand_size);
    event stake_event();

    uint256 public PARTICIPATION_FEE = 5;
    uint8 MAX_PLAYERS = 2;
    uint8 HAND_SIZE = 5;

    bytes output;

    constructor() {
        status = Status.matchmaking;
        turn_index = 0;
        draw_index = 0;
        topdeck_index = 0;
    }

    function reset() public {
        status = Status.matchmaking;
        turn_index = 0;
        draw_index = 0;
        topdeck_index = 0;
        players_addresses = new address[](0);
    }

    function participate() public payable {
        require(status == Status.matchmaking);
        require(msg.value >= PARTICIPATION_FEE);
        
        if (msg.value > PARTICIPATION_FEE) {
            payable(msg.sender).transfer(msg.value - PARTICIPATION_FEE);
        }

        players_addresses.push(msg.sender);

        // If there are enough players game can start
        if (players_addresses.length >= MAX_PLAYERS) {
            status = Status.shuffle;
            emit shuffle_event(turn_index);
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

    function shuffle_dealer(uint256 _n, uint8[] memory _deck_coding, uint256[] memory _encrypted_deck) public {
        require(status == Status.shuffle && turn_index == 0);
        require(msg.sender == players_addresses[turn_index]);

        n = _n;
        deck_coding = _deck_coding;
        encrypted_deck = _encrypted_deck;

        turn_index += 1;
        emit shuffle_event(turn_index);
    }

    function shuffle(uint256[] memory _encrypted_deck) public {
        require(status == Status.shuffle && turn_index != 0);
        require(msg.sender == players_addresses[turn_index]);

        encrypted_deck = _encrypted_deck;

        turn_index += 1;
        if (turn_index >= MAX_PLAYERS) {
            status = Status.draw_card;
            draw_index = 0;
            turn_index = 1;
            emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE);
        }
        else {
            emit shuffle_event(turn_index);
        }
    }

    function get_n() public view returns(uint256) {
        return n;
    }

    function get_deck_coding() public view returns(uint8[] memory) {
        return deck_coding;
    }

    function get_encrypted_deck() public view returns(uint256[] memory) {
        return encrypted_deck;
    }

    function reveal_cards(uint256[] calldata decripted_cards) public {
        require(status == Status.draw_card && turn_index != draw_index);
        require(msg.sender == players_addresses[turn_index]);
        require(decripted_cards.length == HAND_SIZE);

        for (uint8 i=0; i<HAND_SIZE; i++) 
            encrypted_deck[topdeck_index+i] = decripted_cards[i];
        
        turn_index = (turn_index + 1) % MAX_PLAYERS;
        emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE); 
    }

    function get_card(uint8 index) public view returns(uint256) {
        return encrypted_deck[index];
    }

    function draw() public {
        require(status == Status.draw_card && turn_index == draw_index);
        require(msg.sender == players_addresses[draw_index]);

        draw_index += 1;
        if (draw_index >= MAX_PLAYERS) {
            emit stake_event();
        }
        else {
            turn_index = (draw_index + 1) % MAX_PLAYERS;
            topdeck_index += HAND_SIZE;
            emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE); 
        }
    }





    function getPlayer(uint256 index) public view returns (address) {
        require(index < players_addresses.length, "Index out of bounds");
        return players_addresses[index];
    }

    function getNumberOfParticipants() public view returns (uint8) {
        return uint8(players_addresses.length);
    }

    function calculateModularExponentiation(
        bytes32 lengthB,
        bytes32 lengthE,
        bytes32 lengthM,
        bytes memory b,
        bytes memory e,
        bytes memory m
    ) public {
        //require(lengthB == 32, "Invalid length for b");
        //require(lengthE == 32, "Invalid length for e");
        //require(lengthM == 32, "Invalid length for m");

        bytes memory input = abi.encodePacked(
            uint256(lengthB),
            uint256(lengthE),
            uint256(lengthM),
            b,
            e,
            m
        );

        bytes memory result = new bytes(uint256(lengthM));
        assembly {
            let success := call(gas(),              // remaining gas                    ???
                                0x05,               // precomiled contract address
                                0,                  // wei                              ???
                                add(input, 0x20),   // in an array data starts after 32 bytes (0x20 in hex)
                                mload(input),       // mload loads a word (32 bytes), since in an array the first 32 bytes contain its size, it load "input's" lenght
                                add(result, 0x20),  // where to save the result
                                mload(result))      // size of result

            if success {
                sstore(0, 1)
            }
        }

        output = result;
    }
}