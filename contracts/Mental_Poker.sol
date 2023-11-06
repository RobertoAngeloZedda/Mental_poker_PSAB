// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2;

contract Mental_Poker {
    
    // CONSTANTS //
    uint8 MAX_PLAYERS = 2;
    uint8 HAND_SIZE = 1;
    uint8 PARTICIPATION_FEE = 5;


    // PUBLIC GAME's INFOS
    address[] public players_addresses;
    
    uint256 n;
    uint256[] enc_keys;
    uint256[] dec_keys;
    
    uint8[] deck_coding;
    uint256[][] shuffle_steps;
    uint256[] deck;

    uint8[] verify_results;


    // STATUS VARIABLES //
    enum Status {matchmaking, shuffle, draw_card, stake, key_reveal, optimistic_verify, pay_to_verify}
    /* locks function access */
    Status public status;
    /* generically used to convey which player has to act */
    uint8 public turn_index;


    // DRAW PHASE VARIABLES //
    /* while 'turn_index' indicates which player should decrypt a card, 
     * 'draw_index' refers to the player that will draw the card that is being revealed */
    uint8 draw_index;
    /* since the deck is securely shuffled, drawing from the top is perfectly secure
     * 'topdeck_index' points to the next card that will be drawn */
    uint8 topdeck_index;


    // STAKE PHASE VARIABLES //
    /* keeps track of the last player that placed a bet in order to set an end to the stake loop */
    uint8 last_raise_index;
    /* tracks the bets placed */
    uint8[] bets;
    /* fold_flags[i] = true when player i folds, false instead */
    bool[] fold_flags;


    // VERIFY PHASE VARIABLES //
    uint256 public output;
    

    // EVENTS //
    event shuffle_event(uint8 turn_index);
    event draw_event(uint8 turn_index, uint8 draw_index, uint8 topdeck_index, uint8 hand_size);
    event stake_event(uint8 turn_index);
    event key_reveal_event();
    event optimistic_verify_event();
    event pay_to_verify_event();
    event award_event();


    // PUBLIC GAME's INFOS GETTERS //
    function get_max_players() public view returns(uint256) { return MAX_PLAYERS; }
    
    function get_participation_fee() public view returns(uint256) { return PARTICIPATION_FEE; }
    
    function get_n() public view returns(uint256) { return n; }

    function get_deck_coding() public view returns(uint8[] memory) { return deck_coding; }

    function get_deck() public view returns(uint256[] memory) { return deck; }

    function get_enc_keys() public view returns(uint256[] memory) { return enc_keys; }
    
    function get_dec_keys() public view returns(uint256[] memory) { return dec_keys; }


    constructor() {
        status = Status.matchmaking;

        bets = new uint8[](MAX_PLAYERS);
        fold_flags = new bool[](MAX_PLAYERS);
        enc_keys = new uint256[](MAX_PLAYERS);
        dec_keys = new uint256[](MAX_PLAYERS);

        shuffle_steps = new uint256[][](MAX_PLAYERS);

        verify_results = new uint8[](MAX_PLAYERS);
        for (uint8 i=0; i<MAX_PLAYERS; i++) {
            verify_results[i] = MAX_PLAYERS;
        }
    }

    /* for debugging sake */
    function reset() public {
        status = Status.matchmaking;
        turn_index = 0;
        draw_index = 0;
        topdeck_index = 0;
        players_addresses = new address[](0);

        last_raise_index = 0;

        bets = new uint8[](MAX_PLAYERS);
        fold_flags = new bool[](MAX_PLAYERS);
        enc_keys = new uint256[](MAX_PLAYERS);
        dec_keys = new uint256[](MAX_PLAYERS);

        shuffle_steps = new uint256[][](MAX_PLAYERS);
        
        verify_results = new uint8[](MAX_PLAYERS);
        for (uint8 i=0; i<MAX_PLAYERS; i++) {
            verify_results[i] = MAX_PLAYERS;
        }

        output = 0;
    }


    // MATCHMAKING PHASE FUNCTIONS //
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
        for (uint8 i=0; i<players_addresses.length; i++) {
            if (players_addresses[i] == msg.sender) {
                index = i;
                break;
            }
        }
        
        require(index < players_addresses.length);

        return index;
    }


    // SHUFFLE PHASE FUNCTIONS //
    /* the first client that shuffles has to generate n and a deck_coding */
    function shuffle_dealer(uint256 _n, uint8[] memory _deck_coding, uint256[] memory encrypted_deck) public {
        require(status == Status.shuffle && turn_index == 0);
        require(msg.sender == players_addresses[turn_index]);

        n = _n;
        deck_coding = _deck_coding;
        shuffle_steps[0] = encrypted_deck;

        turn_index += 1;
        emit shuffle_event(turn_index);
    }

    function shuffle(uint256[] memory encrypted_deck) public {
        require(status == Status.shuffle && turn_index != 0);
        require(msg.sender == players_addresses[turn_index]);

        shuffle_steps[turn_index] = encrypted_deck;

        turn_index += 1;
        if (turn_index >= MAX_PLAYERS) {
            deck = shuffle_steps[shuffle_steps.length -1];

            status = Status.draw_card;
            draw_index = 0;
            turn_index = 1;
            emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE);
        }
        else {
            emit shuffle_event(turn_index);
        }
    }

    function get_shuffle_step() public view returns (uint256[] memory) { 
        require(status == Status.shuffle && turn_index != 0);
        require(msg.sender == players_addresses[turn_index]);

        return shuffle_steps[turn_index-1]; 
    }


    // DRAW PHASE FUNCTIONS //
    function reveal_cards(uint256[] calldata decripted_cards) public {
        require(status == Status.draw_card && turn_index != draw_index);
        require(msg.sender == players_addresses[turn_index]);
        require(decripted_cards.length == HAND_SIZE);

        for (uint8 i=0; i<HAND_SIZE; i++) 
            deck[topdeck_index+i] = decripted_cards[i];
        
        turn_index = (turn_index + 1) % MAX_PLAYERS;
        emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE); 
    }

    function draw() public {
        require(status == Status.draw_card && turn_index == draw_index);
        require(msg.sender == players_addresses[draw_index]);

        draw_index += 1;
        if (draw_index >= MAX_PLAYERS) {
            status = Status.stake;
            //last_raise_index = 0;
            turn_index = 0;
            emit stake_event(turn_index);
        }
        else {
            turn_index = (draw_index + 1) % MAX_PLAYERS;
            topdeck_index += HAND_SIZE;
            emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE); 
        }
    }
    

    // STAKE PHASE FUNCTIONS //
    function calculate_next_stake_turn() private {
        turn_index = (turn_index + 1) % MAX_PLAYERS;

        if (turn_index != last_raise_index) {
            if (fold_flags[turn_index])
                calculate_next_stake_turn();
            else
                emit stake_event(turn_index);
        }
        else {
            emit stake_event(MAX_PLAYERS);
            status = Status.key_reveal;
            emit key_reveal_event();
        }
    }

    function bet() public payable {
        require(status == Status.stake);
        require(msg.sender == players_addresses[turn_index]);
        require(msg.value > bets[last_raise_index] - bets[turn_index]);

        last_raise_index = turn_index;

        bets[turn_index] += uint8(msg.value);
        
        calculate_next_stake_turn();
    }

    function call() public payable{
        require(status == Status.stake);
        require(msg.sender == players_addresses[turn_index]);
        require(bets[last_raise_index] - bets[turn_index] > 0);
        require(msg.value == bets[last_raise_index] - bets[turn_index]);

        bets[turn_index] += uint8(msg.value);

        calculate_next_stake_turn();
    }

    function check() public {
        require(status == Status.stake);
        require(msg.sender == players_addresses[turn_index]);
        require(bets[last_raise_index] == 0);

        calculate_next_stake_turn();
    }

    function fold() public {
        require(status == Status.stake);
        require(msg.sender == players_addresses[turn_index]);

        fold_flags[turn_index] = true;

        calculate_next_stake_turn();
    }

    function get_last_raise_index() public view returns(uint8) { return last_raise_index; }

    function get_bets() public view returns(uint8[] memory) { return bets; }

    function get_fold_flags() public view returns(bool[] memory) { return fold_flags; }


    // OPTIMISTIC VERIFY PHASE FUNCTIONS //
    function key_reveal(uint256 e, uint256 d) public {
        require(status == Status.key_reveal);
        
        uint8 index = MAX_PLAYERS;
        for (uint8 i=0; i<players_addresses.length; i++) {
            if (players_addresses[i] == msg.sender) {
                index = i;
                break;
            }
        }
        require(index != MAX_PLAYERS);
        
        require(enc_keys[index] == 0);
        require(dec_keys[index] == 0);

        enc_keys[index] = e;
        dec_keys[index] = d;

        for (uint8 i=0; i<MAX_PLAYERS; i++) {
            if (enc_keys[i] == 0 || dec_keys[i] == 0) {
                emit key_reveal_event();
                return;
            }
        }
        
        status = Status.optimistic_verify;
        emit optimistic_verify_event();
    }

    function optimistic_verify(uint8 winner_index) public {
        require(status == Status.optimistic_verify);

        uint8 index = MAX_PLAYERS;
        for (uint8 i=0; i<players_addresses.length; i++) {
            if (players_addresses[i] == msg.sender) {
                index = i;
                break;
            }
        }
        require(index != MAX_PLAYERS);
        
        require(verify_results[index] == MAX_PLAYERS);

        verify_results[index] = winner_index;

        for (uint8 i=0; i<verify_results.length; i++) {
            if (verify_results[i] == MAX_PLAYERS) {
                emit optimistic_verify_event();
                return;
            }
        }
        
        for (uint8 i=0; i<verify_results.length; i++) {
            if (verify_results[i] != winner_index) {
                //da cambiare(?)
                status = Status.pay_to_verify;
                emit pay_to_verify_event();
                return;
            }
        }

        uint8 winnings = 0;
        for (uint8 i=0; i<MAX_PLAYERS; i++){
            winnings += bets[i];
        }
        
        payable(players_addresses[winner_index]).transfer(winnings + PARTICIPATION_FEE);
        emit award_event();
    }


    // VERIFY FUNCTIONS //

    /*
        function skip_to_verify():
        changes status
        notify clients with events (they expect a specific order)
        asks for verify fees
     */ 

    function report_n(uint256 divisor) public view {
        // check status

        //skip_to_verify()

        if (n % divisor == 0) {
            // refund everyone except dealer
            return;
        } else {
            // refund everyone expect client who reported
            return;
        }
    }

    function report_deck_coding(uint8 index) public {
        // check status

        //skip_to_verify()
        
        if (deck_coding[index] % n == 0 || deck_coding[index] == 1) {
            // refund everyone except dealer
            return;
        }
        
        bytes32 len = bytes32(uint256(32));
        bytes memory base = abi.encodePacked(deck_coding[index]);
        bytes memory exp  = abi.encodePacked((n - 1) / 2);         // INTEGER DIVISON ?
        bytes memory mod  = abi.encodePacked(n);

        uint256 result = modular_exponentiation(len, len, len, base, exp, mod);

        if (result == 1) {
            // refund everyone expect client who reported
            return;
        } else {
            // refund everyone except dealer
            return;
        }
    }

    function report_e_and_d(uint8 player_index, uint256 proof) public {
        // check status

        //skip_to_verify()

        // proof encryption
        bytes32 len = bytes32(uint256(32));
        bytes memory base = abi.encodePacked(proof);
        bytes memory exp  = abi.encodePacked(enc_keys[player_index]);
        bytes memory mod  = abi.encodePacked(n);

        uint256 result = modular_exponentiation(len, len, len, base, exp, mod);

        // proof decryption
        base = abi.encodePacked(result);
        exp  = abi.encodePacked(dec_keys[player_index]);
        mod  = abi.encodePacked(n);

        result = modular_exponentiation(len, len, len, base, exp, mod);

        //if (output == proof) {
        if (result == proof) {
            // refund everyone expect client who reported
            return;
        } else {
            // refund everyone except player_index
            return;
        }
    }

    function report_shuffle() public {
        // check status

        //skip_to_verify()
        
        uint256[52] memory _deck;
    
        bytes32 len = bytes32(uint256(32));
        bytes memory base;
        bytes memory exp;
        bytes memory mod;

        for (uint8 i=0; i<deck_coding.length; i++) {
            _deck[i] = deck_coding[i];
        }

        for (uint8 player_index=0; player_index<MAX_PLAYERS; player_index++) {
            for (uint8 card_index=0; card_index<52; card_index++) {
                base = abi.encodePacked(_deck[card_index]);
                exp  = abi.encodePacked(enc_keys[player_index]);
                mod  = abi.encodePacked(n);

                _deck[card_index] = modular_exponentiation(len, len, len, base, exp, mod);

                bool flag = false;
                for (uint8 deck_index=0; deck_index<52; deck_index++) {
                    if (_deck[card_index] == shuffle_steps[player_index][deck_index]) {
                        flag = true;
                        break;
                    }
                }

                if (!flag) {
                    // refund everyone expect client "player index"
                    output = 1;
                    return;
                }
            }
        }
        // refund everyone expect client who reported
        output = 2;
        return;
    }

    /*function report_game_result() public { 
        
    }*/

    function bytes_to_int(bytes memory data) private pure returns (uint256) {
        require(data.length > 0, "Input bytes must not be empty");

        uint256 result = 0;

        for (uint256 i = 0; i < data.length; i++) {
            result = result << 8; // Shift the current result to the left by 8 bits
            result = result | uint8(data[i]); // Bitwise OR to set the least significant 8 bits
        }

        return result;
    }

    function modular_exponentiation(bytes32 length_b, bytes32 length_e, bytes32 length_m,
                                    bytes memory b,   bytes memory e,   bytes memory m) 
                                    private returns (uint256) {
        //require(lengthB == 32, "Invalid length for b");
        //require(lengthE == 32, "Invalid length for e");
        //require(lengthM == 32, "Invalid length for m");

        bytes memory input = abi.encodePacked(
            uint256(length_b),
            uint256(length_e),
            uint256(length_m),
            b,
            e,
            m
        );

        bytes memory result = new bytes(uint256(length_m));
        assembly {
            let success := call(gas(),              // remaining gas                    ???
                                0x05,               // precomiled contract address
                                0,                  // wei                              ???
                                add(input, 0x20),   // in an array data starts after 32 bytes (0x20 in hex)
                                mload(input),       // mload loads a word (32 bytes), since in an array the first 32 bytes contain its size, it load "input's" lenght
                                add(result, 0x20),  // where to save the result
                                mload(result))      // size of result

            //if success {
                //sstore(0, 1)
            //}
        }

        output = bytes_to_int(result);
        return bytes_to_int(result);
    }
}