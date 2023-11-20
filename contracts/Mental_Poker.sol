// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2;

contract Mental_Poker {
    
    // CONSTANTS //
    uint8 public constant MAX_PLAYERS = 3;
    uint8 public constant HAND_SIZE = 5;
    uint8 public constant PARTICIPATION_FEE = 5;
    uint8 constant DECK_SIZE = 52;

    // PUBLIC GAME's INFOS
    address[MAX_PLAYERS] public players_addresses;
    
    uint256 public n;
    uint256[MAX_PLAYERS] enc_keys;
    uint256[MAX_PLAYERS] dec_keys;
    
    uint8[DECK_SIZE] deck_coding;
    uint256[DECK_SIZE][MAX_PLAYERS] public shuffle_steps;
    
    uint256[DECK_SIZE][MAX_PLAYERS] public revealed_cards;
    uint8[DECK_SIZE] public cards_owner;

    uint8[MAX_PLAYERS] verify_results;


    // STATUS VARIABLES //
    enum Status {matchmaking, shuffle, draw_card_1, stake_1, card_change, draw_card_2, stake_2, key_reveal, optimistic_verify, pay_to_verify}
    /* locks function access */
    Status public status;
    /* generically used to convey which player has to act */
    uint8 public turn_index;


    // DRAW PHASE VARIABLES //
    /* while 'turn_index' indicates which player should decrypt a card, 
     * 'draw_index' refers to the player that will draw the card that is being revealed */
    uint8 public draw_index;
    /* since the deck is securely shuffled, drawing from the top is perfectly secure
     * 'topdeck_index' points to the next card that will be drawn */
    uint8 public topdeck_index;


    // STAKE PHASE VARIABLES //
    /* keeps track of the last player that placed a bet in order to set an end to the stake loop */
    uint8 last_raise_index;
    /* tracks the bets placed */
    uint256[MAX_PLAYERS] bets;
    /* fold_flags[i] = true when player i folds, false instead */
    bool[MAX_PLAYERS] fold_flags;
    /* holds the total amount of bets after each stake phase */
    uint256 public pot;
    

    // CARD CHANGE PHASE VARIABLES //
    /* for each player tracks the cards marked for change after the first stake phase */
    bool[HAND_SIZE][MAX_PLAYERS] changed_cards;
    /* tracks the number of changed cards for each player */
    uint8[MAX_PLAYERS] number_of_changed_cards;


    // VERIFY PHASE VARIABLES //
    uint256 public output;


    // EVENTS //
    event shuffle_event(uint8 turn_index);
    event draw_event(uint8 turn_index, uint8 draw_index, uint8 topdeck_index, uint8 num_cards);
    event stake_event(uint8 turn_index);
    event card_change_event(uint8 turn_index);
    event key_reveal_event();
    event optimistic_verify_event();
    event pay_to_verify_event();
    event award_event();

    
    // PUBLIC GAME INFO GETTERS //
    function get_deck_coding() public view returns(uint8[DECK_SIZE] memory) { return deck_coding; }

    function get_enc_keys() public view returns(uint256[MAX_PLAYERS] memory) { return enc_keys; }
    
    function get_dec_keys() public view returns(uint256[MAX_PLAYERS] memory) { return dec_keys; }
    
    function get_cards_owner() public view returns(uint8[DECK_SIZE] memory) { return cards_owner; }


    constructor() {
        status = Status.matchmaking;

        for (uint8 i; i<DECK_SIZE; i++)
            cards_owner[i] = MAX_PLAYERS;

        for (uint8 i; i<MAX_PLAYERS; i++)
            verify_results[i] = MAX_PLAYERS;
                }

    /* for debugging sake */
    function reset() public {
        status = Status.matchmaking;

        for (uint8 i; i<DECK_SIZE; i++)
            cards_owner[i] = MAX_PLAYERS;
        
        for (uint8 i; i<MAX_PLAYERS; i++) {
            players_addresses[i] = address(0);
            bets[i] = 0;
            fold_flags[i] = false;
            enc_keys[i] = 0;
            dec_keys[i] = 0;

            for (uint8 j; j<DECK_SIZE; j++)
                shuffle_steps[i][j] = 0;

            for (uint8 j; j<DECK_SIZE; j++)
                revealed_cards[i][j] = 0;
            
            for (uint8 j; j<HAND_SIZE; j++)
                changed_cards[i][j] = false;
            
            number_of_changed_cards[i] = 0;

            verify_results[i] = MAX_PLAYERS;
        }

        turn_index = 0;
        draw_index = 0;
        topdeck_index = 0;
        
        last_raise_index = 0;

        pot = 0;

        output = 0;
    }

    function next() private {
        if (status == Status.matchmaking) {
            // If there are enough players game can start
            if (players_addresses[players_addresses.length-1] != address(0)) {
                pot = PARTICIPATION_FEE;

                status = Status.shuffle;
                emit shuffle_event(turn_index);
            }
        }
        else if (status == Status.shuffle) {
            // Shuffle is always performed starting from player 0 and ending with player n-1
            turn_index += 1;
            if (turn_index >= MAX_PLAYERS) {
                status = Status.draw_card_1;
                draw_index = 0;
                turn_index = 1;
                emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE);
            }
            else {
                emit shuffle_event(turn_index);
            }
        }
        else if (status == Status.draw_card_1) {
            if (turn_index == draw_index) {
                topdeck_index += HAND_SIZE;
                draw_index += 1;
                if (draw_index >= MAX_PLAYERS) {
                    status = Status.stake_1;
                    //last_raise_index = 0;
                    turn_index = 0;
                    emit stake_event(turn_index);
                }
                else {
                    turn_index = (draw_index + 1) % MAX_PLAYERS;
                    emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE); 
                }
            }
            else {
                turn_index = (turn_index + 1) % MAX_PLAYERS;
                emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE); 
            }
        }
        else if (status == Status.stake_1) {
            turn_index = (turn_index + 1) % MAX_PLAYERS;

            if (turn_index != last_raise_index) {
                if (fold_flags[turn_index])
                    next();
                else {
                    bool is_only_one_player_left = true;
                    for (uint8 i; i<MAX_PLAYERS; i++) {
                        if (i != turn_index && fold_flags[i] == false) {
                            is_only_one_player_left = false;
                            break;
                        }
                    }

                    if (is_only_one_player_left) {
                        for (uint8 i; i<MAX_PLAYERS; i++) {
                            pot += bets[i];
                            bets[i] = 0;
                        }

                        emit stake_event(MAX_PLAYERS);
                        status = Status.card_change;
                        emit card_change_event(MAX_PLAYERS);
                        status = Status.draw_card_2;
                        emit draw_event(turn_index, draw_index, topdeck_index, 0);
                        status = Status.key_reveal;
                        emit key_reveal_event();
                    }
                    else
                        emit stake_event(turn_index);
                }
            }
            else {
                for (uint8 i; i<MAX_PLAYERS; i++) {
                    pot += bets[i];
                    bets[i] = 0;
                }
                
                emit stake_event(MAX_PLAYERS);
                status = Status.card_change;
                emit card_change_event(turn_index);
            }
        }
        else if (status == Status.card_change) {
            turn_index = (turn_index + 1) % MAX_PLAYERS;

            if (turn_index == last_raise_index) {    
                emit card_change_event(MAX_PLAYERS);

                uint8 num_cards;
                bool someone_has_to_draw;
                for (uint8 i; i<MAX_PLAYERS; i++) {
                    if (fold_flags[i] == false && number_of_changed_cards[i] > 0) {
                        draw_index = i;
                        turn_index = (draw_index + 1) % MAX_PLAYERS;
                        someone_has_to_draw = true;
                        break; 
                    }
                }
                if (someone_has_to_draw) {
                    num_cards = number_of_changed_cards[draw_index];
                    status = Status.draw_card_2;
                }
                
                emit draw_event(turn_index, draw_index, topdeck_index, num_cards);
                
                if (!someone_has_to_draw) {
                    status = Status.stake_2;
                    emit stake_event(turn_index);
                }
            }
            else {
                if (fold_flags[turn_index])
                    next();
                else
                    emit card_change_event(turn_index);
            }
        }
        else if (status == Status.draw_card_2) {
            if (turn_index == draw_index) {
                topdeck_index += number_of_changed_cards[draw_index];

                uint8 num_cards;
                bool someone_has_to_draw;
                for (uint8 i=draw_index+1; i<MAX_PLAYERS; i++) {
                    if (fold_flags[i] == false && number_of_changed_cards[i] > 0) {
                        draw_index = i;
                        turn_index = (draw_index + 1) % MAX_PLAYERS;
                        someone_has_to_draw = true;
                        break; 
                    }
                }

                if (someone_has_to_draw)
                    num_cards = number_of_changed_cards[draw_index];
                
                emit draw_event(turn_index, draw_index, topdeck_index, num_cards);
                
                if (!someone_has_to_draw) {
                    status = Status.stake_2;
                    turn_index = last_raise_index;
                    emit stake_event(turn_index);
                }
            }
            else {
                turn_index = (turn_index + 1) % MAX_PLAYERS;
                emit draw_event(turn_index, draw_index, topdeck_index, number_of_changed_cards[draw_index]); 
            }
        }
        else if (status == Status.stake_2) {
            turn_index = (turn_index + 1) % MAX_PLAYERS;

            if (turn_index != last_raise_index) {
                if (fold_flags[turn_index])
                    next();
                else {
                    bool is_only_one_player_left = true;
                    for (uint8 i; i<MAX_PLAYERS; i++) {
                        if (i != turn_index && fold_flags[i] == false) {
                            is_only_one_player_left = false;
                            break;
                        }
                    }

                    if (is_only_one_player_left) {
                        for (uint8 i; i<MAX_PLAYERS; i++)
                            pot += bets[i];
                        
                        emit stake_event(MAX_PLAYERS);
                        status = Status.key_reveal;
                        emit key_reveal_event();
                    }
                    else
                        emit stake_event(turn_index);
                }
            }
            else {
                for (uint8 i; i<MAX_PLAYERS; i++)
                    pot += bets[i];

                emit stake_event(MAX_PLAYERS);
                status = Status.key_reveal;
                emit key_reveal_event();
            }
        }
        else if (status == Status.key_reveal) {
            for (uint8 i; i<MAX_PLAYERS; i++) {
                if (enc_keys[i] == 0 || dec_keys[i] == 0) {
                    return;
                }
            }

            status = Status.optimistic_verify;
            emit optimistic_verify_event();
        }
        else if (status == Status.optimistic_verify) {
            // Checking if every client has communicated his result
            for (uint8 i; i<verify_results.length; i++) {
                if (verify_results[i] == MAX_PLAYERS) {
                    return;
                }
            }
            
            // Checking if all results match
            /*for (uint8 i; i<verify_results.length; i++) {
                if (verify_results[i] != winner_index) {
                    //da cambiare(?)
                    status = Status.pay_to_verify;
                    emit pay_to_verify_event();
                    return;
                }
            }*/

            //payable(players_addresses[winner_index]).transfer(winnings + PARTICIPATION_FEE);
            payable(players_addresses[verify_results[0]]).transfer(pot);
            emit award_event();
        }
    }


    // MATCHMAKING PHASE FUNCTIONS //
    function participate() public payable {
        require(status == Status.matchmaking);
        require(msg.value >= PARTICIPATION_FEE);
        
        if (msg.value > PARTICIPATION_FEE) {
            payable(msg.sender).transfer(msg.value - PARTICIPATION_FEE);
        }

        for (uint i; i<MAX_PLAYERS; i++) {
            if (players_addresses[i] == address(0)) {
                players_addresses[i] = msg.sender;
                break;
            }
        }

        next();
    }

    function get_my_turn_index() public view returns(uint8) {
        //require(players_addresses.length > 0);
        
        uint8 index = MAX_PLAYERS;
        for (uint8 i; i<players_addresses.length; i++) {
            if (players_addresses[i] == msg.sender) {
                index = i;
                break;
            }
        }
        
        require(index < MAX_PLAYERS);

        return index;
    }


    // SHUFFLE PHASE FUNCTIONS //
    /* the first client that shuffles has to generate n and a deck_coding */
    function shuffle_dealer(uint256 _n, uint8[DECK_SIZE] memory _deck_coding, uint256[DECK_SIZE] memory encrypted_deck) public {
        require(status == Status.shuffle && turn_index == 0);
        require(msg.sender == players_addresses[turn_index]);

        n = _n;

        deck_coding = _deck_coding;

        shuffle_steps[0] = encrypted_deck;

        next();
    }

    function shuffle(uint256[DECK_SIZE] memory encrypted_deck) public {
        require(status == Status.shuffle && turn_index != 0);
        require(msg.sender == players_addresses[turn_index]);

        shuffle_steps[turn_index] = encrypted_deck;

        next();
    }

    function get_deck() public view returns (uint256[DECK_SIZE] memory) {
        if (status == Status.shuffle && turn_index > 0)
            return shuffle_steps[turn_index-1];

        uint256[DECK_SIZE] memory deck;

        if (status == Status.draw_card_1 || status == Status.draw_card_2) {
            for (uint8 i; i<DECK_SIZE; i++) {
                if (cards_owner[i] == MAX_PLAYERS)
                    deck[i] = shuffle_steps[MAX_PLAYERS-1][i];
                else {
                    if (turn_index == (draw_index + 1) % MAX_PLAYERS)
                        deck[i] = shuffle_steps[MAX_PLAYERS-1][topdeck_index+i];
                    else {
                        uint8 prev_index;
                        if (turn_index == 0)
                            prev_index = MAX_PLAYERS-1;
                        else
                            prev_index = turn_index-1;

                        deck[i] = revealed_cards[prev_index][i];
                    }
                }
            }
            return deck;
        }

        for (uint8 i; i<DECK_SIZE; i++) {
            if (cards_owner[i] == MAX_PLAYERS)
                deck[i] = shuffle_steps[MAX_PLAYERS-1][i];
            else {
                uint8 prev_index;
                if (cards_owner[i] == 0)
                    prev_index = MAX_PLAYERS-1;
                else
                    prev_index = cards_owner[i]-1;

                deck[i] = revealed_cards[prev_index][i];
            }
        }

        return deck;
    }


    // DRAW PHASE FUNCTIONS //
    function reveal_cards(uint256[] memory decripted_cards) public {
        require((status == Status.draw_card_1 && decripted_cards.length == HAND_SIZE) || (status == Status.draw_card_2 && decripted_cards.length == number_of_changed_cards[draw_index]));
        require(turn_index != draw_index);
        require(msg.sender == players_addresses[turn_index]);

        for (uint8 i; i<decripted_cards.length; i++) {
            revealed_cards[turn_index][topdeck_index + i] = decripted_cards[i];
            cards_owner[topdeck_index+i] = draw_index;
        }

        next();
    }

    function draw() public {
        require(status == Status.draw_card_1 || status == Status.draw_card_2);
        require(turn_index == draw_index);
        require(msg.sender == players_addresses[draw_index]);

        next();
    }
    

    // STAKE PHASE FUNCTIONS //
    function bet() public payable {
        require(status == Status.stake_1 || status == Status.stake_2);
        require(msg.sender == players_addresses[turn_index]);
        require(msg.value > bets[last_raise_index] - bets[turn_index]);

        last_raise_index = turn_index;

        bets[turn_index] += msg.value;
        
        next();
    }

    function call() public payable{
        require(status == Status.stake_1 || status == Status.stake_2);
        require(msg.sender == players_addresses[turn_index]);
        require(bets[last_raise_index] - bets[turn_index] > 0);
        require(msg.value == bets[last_raise_index] - bets[turn_index]);

        bets[turn_index] += uint256(msg.value);

        next();
    }

    function check() public {
        require(status == Status.stake_1 || status == Status.stake_2);
        require(msg.sender == players_addresses[turn_index]);
        require(bets[last_raise_index] == 0);

        next();
    }

    function fold() public {
        require(status == Status.stake_1 || status == Status.stake_2);
        require(msg.sender == players_addresses[turn_index]);

        fold_flags[turn_index] = true;

        next();
    }

    function get_last_raise_index() public view returns(uint8) { return last_raise_index; }

    function get_bets() public view returns(uint256[MAX_PLAYERS] memory) { return bets; }
    
    function get_fold_flags() public view returns(bool[MAX_PLAYERS] memory) { return fold_flags; }


    // CARD CHANGE PHASE FUNCTIONS //
    function card_change(bool[] memory cards_to_change) public {
        require(status == Status.card_change);
        require(msg.sender == players_addresses[turn_index]);
        require(cards_to_change.length == HAND_SIZE);
        
        for (uint8 i; i<HAND_SIZE; i++) {
            if (cards_to_change[i]) {
                changed_cards[turn_index][i] = true;
                number_of_changed_cards[turn_index]++;
                cards_owner[turn_index * HAND_SIZE + i] = MAX_PLAYERS;
            }
        }
        
        require(number_of_changed_cards[turn_index] < HAND_SIZE);

        next();
    }

    function get_number_of_changed_cards() public view returns(uint8[MAX_PLAYERS] memory) { return number_of_changed_cards; }


    // OPTIMISTIC VERIFY PHASE FUNCTIONS //
    function key_reveal(uint256 e, uint256 d) public {
        require(status == Status.key_reveal);
        
        uint8 index = MAX_PLAYERS;
        for (uint8 i; i<players_addresses.length; i++) {
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

        next();
    }

    function optimistic_verify(uint8 winner_index) public {
        require(status == Status.optimistic_verify);

        uint8 index = MAX_PLAYERS;
        for (uint8 i; i<players_addresses.length; i++) {
            if (players_addresses[i] == msg.sender) {
                index = i;
                break;
            }
        }
        require(index != MAX_PLAYERS);
        
        require(verify_results[index] == MAX_PLAYERS);

        verify_results[index] = winner_index;

        next();
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
            output = 2;
            return;
        } else {
            // refund everyone except player_index
            output = 1;
            return;
        }
    }

    function report_shuffle() public {
        // check status

        //skip_to_verify()
        
        uint256[52] memory deck;
    
        bytes32 len = bytes32(uint256(32));
        bytes memory base;
        bytes memory exp;
        bytes memory mod;

        for (uint8 i; i<deck_coding.length; i++)
            deck[i] = deck_coding[i];

        for (uint8 player_index; player_index<MAX_PLAYERS; player_index++) {
            for (uint8 card_index; card_index<52; card_index++) {
                base = abi.encodePacked(deck[card_index]);
                exp  = abi.encodePacked(enc_keys[player_index]);
                mod  = abi.encodePacked(n);

                deck[card_index] = modular_exponentiation(len, len, len, base, exp, mod);

                bool flag = false;
                for (uint8 deck_index; deck_index<52; deck_index++) {
                    if (deck[card_index] == shuffle_steps[player_index][deck_index]) {
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

    function report_draw() public {
        // check status

        //skip_to_verify()
        
        uint8 cards_drawn_count;
        for (uint8 i; i<DECK_SIZE; i++)
            if (cards_owner[i] != MAX_PLAYERS)
                cards_drawn_count++;
            else
                break;

        uint256[] memory deck = new uint256[](cards_drawn_count);
    
        bytes32 len = bytes32(uint256(32));
        bytes memory base;
        bytes memory exp;
        bytes memory mod;

        for (uint8 card_index; card_index<cards_drawn_count; card_index++) {
            for (uint8 player_index = (cards_owner[card_index] + 1) % MAX_PLAYERS;
                       player_index == cards_owner[card_index];
                       (player_index + 1) % MAX_PLAYERS) {

                if (player_index == (cards_owner[card_index] + 1) % MAX_PLAYERS)
                    base = abi.encodePacked(shuffle_steps[MAX_PLAYERS-1][card_index]);
                else {
                    uint8 prev_index;
                    if (cards_owner[card_index] == 0)
                        prev_index = MAX_PLAYERS-1;
                    else
                        prev_index = cards_owner[card_index]-1;
                    base = abi.encodePacked(revealed_cards[prev_index][card_index]);
                }
                exp  = abi.encodePacked(enc_keys[player_index]);
                mod  = abi.encodePacked(n);

                deck[card_index] = modular_exponentiation(len, len, len, base, exp, mod);

                if (revealed_cards[player_index][card_index] != deck[card_index]) {
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

    //function report_game_result() public {}

    function bytes_to_int(bytes memory data) private pure returns (uint256) {
        require(data.length > 0, "Input bytes must not be empty");

        uint256 result = 0;

        for (uint256 i; i<data.length; i++) {
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