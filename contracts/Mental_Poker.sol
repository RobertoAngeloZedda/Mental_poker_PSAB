// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2;

contract Mental_Poker {
    
    // CONSTANTS //
    uint8 public constant MAX_PLAYERS = 3;
    uint8 public constant HAND_SIZE = 5;
    //uint8 public constant PARTICIPATION_FEE = 5;
    uint256 public constant DEPOSIT = 4000000;
    uint8 constant DECK_SIZE = 52;

    // PUBLIC GAME's INFOS
    address[MAX_PLAYERS] players_addresses;
    
    uint256 public n;
    uint256[MAX_PLAYERS] enc_keys;
    uint256[MAX_PLAYERS] dec_keys;
    
    uint8[DECK_SIZE] deck_coding;
    /* keeps track of the shuffle steps so that the result can be verified */
    uint256[DECK_SIZE][MAX_PLAYERS] shuffle_steps;
    /* keeps track of drawing and revealing steps so that they can be verified */
    uint256[DECK_SIZE][MAX_PLAYERS] revealed_cards;
    /* cards_owner[i] = j means that the i-th card belongs to the j-th player
     * this vector is used to reconstruct hands on the client side and manage card change */
    uint8[DECK_SIZE] cards_owner;
    /* contains the results calculated by every client */
    uint8[MAX_PLAYERS] verify_results;


    // STATUS VARIABLES //
    enum Status {matchmaking, shuffle, draw_card_1, stake_1, card_change, draw_card_2, 
                 stake_2, key_reveal, optimistic_verify, verify}
    /* locks function access */
    Status public status;
    /* generically used to convey which player has to act */
    uint8 public turn_index;


    // DRAW PHASE VARIABLES //
    /* 'draw_index' refers to the player that will draw the card that is being revealed
     *  while 'turn_index' indicates which player should decrypt a card to reveal it */
    uint8 public draw_index;
    /* since the deck is securely shuffled, drawing from the top is perfectly secure
     * 'topdeck_index' points to the next card that will be drawn */
    uint8 public topdeck_index;


    // STAKE PHASE VARIABLES //
    /* keeps track of the last player that placed a bet in order to set an end to the stake loop */
    uint8 public last_raise_index;
    /* tracks the bets placed */
    uint256[MAX_PLAYERS] bets1;
    uint256[MAX_PLAYERS] bets2;
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
    uint8 public reporter_index;
    bool[MAX_PLAYERS] has_paid;


    // EVENTS //
    event shuffle_event(uint8 turn_index);
    event draw_event(uint8 turn_index, uint8 draw_index, uint8 topdeck_index, uint8 num_cards);
    event stake_event(uint8 turn_index);
    event card_change_event(uint8 turn_index);
    event key_reveal_event();
    /* result = 0 at the start of the phase 
     * result = 1 if everything went smoothly 
     * result = 2 if there's been a report */
    event optimistic_verify_event(uint8 result);
    event verify_event();
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

        reporter_index = MAX_PLAYERS;
    }

    /* for debugging sake */
    function reset() public {
        status = Status.matchmaking;

        for (uint8 i; i<DECK_SIZE; i++)
            cards_owner[i] = MAX_PLAYERS;
        
        for (uint8 i; i<MAX_PLAYERS; i++) {
            players_addresses[i] = address(0);
            bets1[i] = 0;
            bets2[i] = 0;
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

            has_paid[i] = false;
        }

        turn_index = 0;
        draw_index = 0;
        topdeck_index = 0;
        last_raise_index = 0;

        pot = 0;

        reporter_index = MAX_PLAYERS;
    }

    function next() private {
        if (status == Status.matchmaking) {
            /* if there are enough players game can start */
            if (players_addresses[players_addresses.length-1] != address(0)) {
                status = Status.shuffle;
                emit shuffle_event(turn_index);
            }
        }

        else if (status == Status.shuffle) {
            /* shuffle is always performed starting from player 0 and ending with player n-1 */
            turn_index += 1;
            if (turn_index >= MAX_PLAYERS) {
                status = Status.draw_card_1;
                /* since draw_index = 0, turn index = 1 */
                turn_index = 1;
                emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE);
            }
            else
                emit shuffle_event(turn_index);
        }

        else if (status == Status.draw_card_1) {
            /* if client has drawn */
            if (turn_index == draw_index) {
                topdeck_index += HAND_SIZE;
                draw_index += 1;
                /* if every client has drawn */
                if (draw_index >= MAX_PLAYERS) {
                    status = Status.stake_1;
                    turn_index = 0;
                    emit stake_event(turn_index);
                }
                else {
                    turn_index = (draw_index + 1) % MAX_PLAYERS;
                    emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE); 
                }
            }
            /* if client has decrypted */
            else {
                turn_index = (turn_index + 1) % MAX_PLAYERS;
                emit draw_event(turn_index, draw_index, topdeck_index, HAND_SIZE); 
            }
        }

        else if (status == Status.stake_1) {
            turn_index = (turn_index + 1) % MAX_PLAYERS;

            /* if the stake round hasnt been completed yet */
            if (turn_index != last_raise_index) {
                /* if client has folded we skip to the next client */
                if (fold_flags[turn_index])
                    next();
                else {
                    bool is_only_one_player_left = true;
                    for (uint8 i; i<MAX_PLAYERS; i++) {
                        if (i != turn_index && !fold_flags[i]) {
                            is_only_one_player_left = false;
                            break;
                        }
                    }

                    if (is_only_one_player_left) {
                        /* pot updated and bets reset */
                        for (uint8 i; i<MAX_PLAYERS; i++)
                            pot += bets1[i];

                        /* skip to the key_reveal phase */
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
            /* if the stake round has been completed */
            else {
                /* pot updated and bets reset */
                for (uint8 i; i<MAX_PLAYERS; i++)
                    pot += bets1[i];
                
                emit stake_event(MAX_PLAYERS);

                status = Status.card_change;
                emit card_change_event(turn_index);
            }
        }

        else if (status == Status.card_change) {
            turn_index = (turn_index + 1) % MAX_PLAYERS;

            /* if card_change phase is over */
            if (turn_index == last_raise_index) {    
                emit card_change_event(MAX_PLAYERS);

                /* finding the first player that has to draw, if there is any
                 * (excluding players that have folded and player who didnt change any cards) */
                uint8 num_cards;
                bool someone_has_to_draw;
                for (uint8 i; i<MAX_PLAYERS; i++) {
                    if (!fold_flags[i] && number_of_changed_cards[i] > 0) {
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
            /* if card_change phase isnt over yet */
            else {
                if (fold_flags[turn_index])
                    next();
                else
                    emit card_change_event(turn_index);
            }
        }

        else if (status == Status.draw_card_2) {
            /* if client has drawn */
            if (turn_index == draw_index) {
                topdeck_index += number_of_changed_cards[draw_index];

                /* finding the next player that has to draw, if there is any
                 * (excluding players that have folded and player who didnt change any cards) */
                uint8 num_cards;
                bool someone_has_to_draw;
                for (uint8 i=draw_index+1; i<MAX_PLAYERS; i++) {
                    if (!fold_flags[i] && number_of_changed_cards[i] > 0) {
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
            /* if client has decrypted */
            else {
                turn_index = (turn_index + 1) % MAX_PLAYERS;
                emit draw_event(turn_index, draw_index, topdeck_index, number_of_changed_cards[draw_index]); 
            }
        }

        else if (status == Status.stake_2) {
            turn_index = (turn_index + 1) % MAX_PLAYERS;

            /* if the stake round hasnt been completed yet */
            if (turn_index != last_raise_index) {
                /* if client has folded we skip to the next client */
                if (fold_flags[turn_index])
                    next();
                else {
                    bool is_only_one_player_left = true;
                    for (uint8 i; i<MAX_PLAYERS; i++) {
                        if (i != turn_index && !fold_flags[i]) {
                            is_only_one_player_left = false;
                            break;
                        }
                    }

                    if (is_only_one_player_left) {
                        /* pot updated */
                        for (uint8 i; i<MAX_PLAYERS; i++)
                            pot += bets2[i];
                        
                        emit stake_event(MAX_PLAYERS);
                        status = Status.key_reveal;
                        emit key_reveal_event();
                    }
                    else
                        emit stake_event(turn_index);
                }
            }
            /* if the stake round has been completed */
            else {
                for (uint8 i; i<MAX_PLAYERS; i++)
                    pot += bets2[i];

                emit stake_event(MAX_PLAYERS);

                status = Status.key_reveal;
                emit key_reveal_event();
            }
        }

        else if (status == Status.key_reveal) {
            /* does nothing if some player still has to communicate its keys */
            for (uint8 i; i<MAX_PLAYERS; i++) {
                if (enc_keys[i] == 0 || dec_keys[i] == 0) {
                    return;
                }
            }

            status = Status.optimistic_verify;
            emit optimistic_verify_event(0);
            
            if (reporter_index != MAX_PLAYERS) {
                emit optimistic_verify_event(2);
                status = Status.verify;
                emit verify_event();
            }
        }

        else if (status == Status.optimistic_verify) {
            /* does nothing if some player still has to communicate its result */
            for (uint8 i; i<verify_results.length; i++) {
                if (verify_results[i] == MAX_PLAYERS) {
                    return;
                }
            }
            
            /* Checking if all results match */
            uint8 winner_index = verify_results[0];
            for (uint8 i=1; i<verify_results.length; i++) {
                if (verify_results[i] != winner_index) {

                    emit optimistic_verify_event(2);
                    emit verify_event();

                    status = Status.verify;
                    reporter_index = i;
                    report_game_result();
                    
                    emit award_event();
                    return;
                }
            }

            payable(players_addresses[winner_index]).transfer(pot);
            for (uint8 i; i<MAX_PLAYERS; i++)
                payable(players_addresses[i]).transfer(DEPOSIT);
            emit optimistic_verify_event(1);
            emit award_event();
        }
    }


    // MATCHMAKING PHASE FUNCTIONS //
    function participate() public payable {
        require(status == Status.matchmaking);
        require(msg.value >= DEPOSIT);
        
        if (msg.value > DEPOSIT) {
            payable(msg.sender).transfer(msg.value - DEPOSIT);
        }

        for (uint i; i<MAX_PLAYERS; i++) {
            require(players_addresses[i] != msg.sender);
            
            if (players_addresses[i] == address(0)) {
                players_addresses[i] = msg.sender;
                break;
            }
        }

        next();
    }

    function get_my_turn_index() public view returns(uint8) {
        
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

    /* reconstructs the deck so that 
     * the data structure used to correctly verify the game execution
     * are completly trasparent to the client */
    function get_deck() public view returns (uint256[DECK_SIZE] memory) {
        /* during the shuffle steps only non dealer clients need to get access to the deck
         * (which is generated by the previous client encryption) */
        if (status == Status.shuffle && turn_index > 0)
            return shuffle_steps[turn_index-1];

        uint256[DECK_SIZE] memory deck;

        /* during the shuffle steps */
        if (status == Status.draw_card_1 || status == Status.draw_card_2) {
            for (uint8 i; i<DECK_SIZE; i++) {
                /* if no one owns the card its most recent version is in the last shuffle step */
                if (cards_owner[i] == MAX_PLAYERS)
                    deck[i] = shuffle_steps[MAX_PLAYERS-1][i];
                else {
                    /* if no client has decrypted the card yet
                     * its most recent version is in the last shuffle step */
                    if (turn_index == (draw_index + 1) % MAX_PLAYERS)
                        deck[i] = shuffle_steps[MAX_PLAYERS-1][topdeck_index+i];
                    /* if the card has already been decrypted
                     * its most recent version is in revealed_cards */
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

        /* In every other phase of the game the deck can be reconstructed
         * simply by using the cards_owner vector */
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

        if (status == Status.stake_1)
            require(msg.value > bets1[last_raise_index] - bets1[turn_index]);

        if (status == Status.stake_2)
            require(msg.value > bets2[last_raise_index] - bets2[turn_index]);

        last_raise_index = turn_index;

        if (status == Status.stake_1)
            bets1[turn_index] += msg.value;
        
        if (status == Status.stake_2)
            bets2[turn_index] += msg.value;

        next();
    }

    function call() public payable{
        require(status == Status.stake_1 || status == Status.stake_2);
        require(msg.sender == players_addresses[turn_index]);

        if (status == Status.stake_1) {
            require(bets1[last_raise_index] - bets1[turn_index] > 0);
            require(msg.value == bets1[last_raise_index] - bets1[turn_index]);

            bets1[turn_index] += uint256(msg.value);
        }
        
        if (status == Status.stake_2) {
            require(bets2[last_raise_index] - bets2[turn_index] > 0);
            require(msg.value == bets2[last_raise_index] - bets2[turn_index]);

            bets2[turn_index] += uint256(msg.value);
        }

        next();
    }

    function check() public {
        require(status == Status.stake_1 || status == Status.stake_2);
        require(msg.sender == players_addresses[turn_index]);

        if (status == Status.stake_1)
            require(bets1[last_raise_index] == 0);

        if (status == Status.stake_2)
            require(bets2[last_raise_index] == 0);

        next();
    }

    function fold() public {
        require(status == Status.stake_1 || status == Status.stake_2);
        require(msg.sender == players_addresses[turn_index]);

        fold_flags[turn_index] = true;

        next();
    }

    function get_last_raise_index() public view returns(uint8) { return last_raise_index; }

    function get_bets() public view returns(uint256[MAX_PLAYERS] memory) { 
        if (status < Status.stake_2)
            return bets1;
        else
            return bets2;
    }
    
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
        
        /* since this phase doesnt involve the use of turn_index
         * this checks if the client is one of the partecipants */
        uint8 index = MAX_PLAYERS;
        for (uint8 i; i<players_addresses.length; i++) {
            if (players_addresses[i] == msg.sender) {
                index = i;
                break;
            }
        }
        require(index != MAX_PLAYERS);
        
        /* checks if this client has already submitted its result */
        require(enc_keys[index] == 0);
        require(dec_keys[index] == 0);

        enc_keys[index] = e;
        dec_keys[index] = d;

        next();
    }

    function optimistic_verify(uint8 winner_index) public {
        require(status == Status.optimistic_verify);

        /* since this phase doesnt involve the use of turn_index
         * this checks if the client is one of the partecipants */
        uint8 index = MAX_PLAYERS;
        for (uint8 i; i<players_addresses.length; i++) {
            if (players_addresses[i] == msg.sender) {
                index = i;
                break;
            }
        }
        require(index != MAX_PLAYERS);
        
        /* checks if this client has already submitted its result */
        require(verify_results[index] == MAX_PLAYERS);

        verify_results[index] = winner_index;

        next();
    }


    // VERIFY FUNCTIONS //
    function report() private {
        require (reporter_index != MAX_PLAYERS);

        /* checking if the client is one of the partecipants */
        for (uint8 i; i<players_addresses.length; i++) {
            if (players_addresses[i] == msg.sender) {
                reporter_index = i;
                break;
            }
        }
        require(reporter_index < MAX_PLAYERS);

        /* report_n and report_deck_coding arrive in this state */
        if (status == Status.shuffle)
            status = Status.draw_card_1;

        /* report_draw might arrive in this state */
        if (status == Status.draw_card_1) {
            emit draw_event(0, 0, 0, 0);
            emit stake_event(MAX_PLAYERS);
            emit card_change_event(MAX_PLAYERS);

            status = Status.draw_card_2;
        }

        /* report_draw might arrive in this state */
        if (status == Status.draw_card_2) {
            emit draw_event(0, 0, 0, 0);
            emit stake_event(MAX_PLAYERS);

            /* letting the key_reveal phase be handled by next() */
            status = Status.key_reveal;
            emit key_reveal_event();
            return;
        }

        /* report_e_and_d arrive in this state 
         * report_draw reaches this state after keys are reveled
         * if the optimistic_verify fails we also reach this state */
        if (status == Status.optimistic_verify) {
            emit optimistic_verify_event(2);

            status = Status.verify;
            emit verify_event();
        }
    }

    function report_n() public {
        require (status == Status.verify);
        require (players_addresses[reporter_index] == msg.sender);

        // still need to check n

        uint256 bonus_refund;
        if (true) {
            // refund everyone expect client who reported
            bonus_refund = (bets1[reporter_index] + bets2[reporter_index]) / (MAX_PLAYERS - 1);
            for (uint8 i; i<MAX_PLAYERS; i++)
                if (i != reporter_index)
                    payable(players_addresses[i]).transfer(DEPOSIT + bonus_refund);
        } else {
            // refund everyone expect dealer
            bonus_refund = (bets1[0] + bets2[0]) / (MAX_PLAYERS - 1);
            for (uint8 i=1; i<MAX_PLAYERS; i++)
                payable(players_addresses[i]).transfer(DEPOSIT + bonus_refund);
        }

        emit award_event();
    }

    function report_deck_coding(uint8 index) public {
        require (status == Status.verify);
        require (players_addresses[reporter_index] == msg.sender);
        
        if (deck_coding[index] % n == 0 || deck_coding[index] == 1) {
            // refund everyone except dealer
            return;
        }
        
        bytes32 len = bytes32(uint256(32));
        bytes memory base = abi.encodePacked(deck_coding[index]);
        bytes memory exp  = abi.encodePacked(uint256((n - 1) / 2));         // INTEGER DIVISON ?
        bytes memory mod  = abi.encodePacked(n);

        uint256 result = modular_exponentiation(len, len, len, base, exp, mod);

        uint256 bonus_refund;
        if (result == 1) {
            // refund everyone expect client who reported
            bonus_refund = (bets1[reporter_index] + bets2[reporter_index]) / (MAX_PLAYERS - 1);
            for (uint8 i; i<MAX_PLAYERS; i++)
                if (i != reporter_index)
                    payable(players_addresses[i]).transfer(DEPOSIT + bonus_refund);
        } else {
            // refund everyone except dealer
            bonus_refund = (bets1[0] + bets2[0]) / (MAX_PLAYERS - 1);
            for (uint8 i=1; i<MAX_PLAYERS; i++)
                payable(players_addresses[i]).transfer(DEPOSIT + bonus_refund);
        }
        
        emit award_event();
    }

    function report_keys(uint8 player_index, uint256 proof) public {
        require (status == Status.verify);
        require (players_addresses[reporter_index] == msg.sender);

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

        uint256 bonus_refund;
        //if (output == proof) {
        if (result == proof) {
            // refund everyone expect client who reported
            bonus_refund = (bets1[reporter_index] + bets2[reporter_index]) / (MAX_PLAYERS - 1);
            for (uint8 i; i<MAX_PLAYERS; i++)
                if (i != reporter_index)
                    payable(players_addresses[i]).transfer(DEPOSIT + bonus_refund);
        } else {
            // refund everyone except player_index
            bonus_refund = (bets1[player_index] + bets2[player_index]) / (MAX_PLAYERS - 1);
            for (uint8 i; i<MAX_PLAYERS; i++)
                if (i != player_index)
                    payable(players_addresses[i]).transfer(DEPOSIT + bonus_refund);
        }
        
        emit award_event();
    }

    function report_shuffle() private returns(bool){
        uint256[DECK_SIZE] memory deck;
    
        bytes32 len = bytes32(uint256(32));
        bytes memory base;
        bytes memory exp;
        bytes memory mod;

        for (uint8 i; i<deck_coding.length; i++)
            deck[i] = deck_coding[i];

        for (uint8 player_index; player_index<MAX_PLAYERS; player_index++) {
            for (uint8 card_index; card_index<DECK_SIZE; card_index++) {
                base = abi.encodePacked(deck[card_index]);
                exp  = abi.encodePacked(enc_keys[player_index]);
                mod  = abi.encodePacked(n);

                deck[card_index] = modular_exponentiation(len, len, len, base, exp, mod);

                bool flag = false;
                for (uint8 deck_index; deck_index<DECK_SIZE; deck_index++) {
                    if (deck[card_index] == shuffle_steps[player_index][deck_index]) {
                        flag = true;
                        break;
                    }
                }

                if (!flag) {
                    // refund everyone expect client "player index"
                    uint256 bonus_refund = (bets1[player_index] + bets2[player_index]) / (MAX_PLAYERS - 1);
                    for (uint8 i; i<MAX_PLAYERS; i++)
                        if (i != player_index)
                            payable(players_addresses[i]).transfer(DEPOSIT + bonus_refund);
                    return true;
                }
            }
        }

        return false;
    }

    function report_draw() public {
        require (status == Status.verify);
        require (players_addresses[reporter_index] == msg.sender);

        if (report_shuffle())
            return;
        
        uint8 cards_drawn_count;
        for (uint8 i; i<DECK_SIZE; i++)
            if (cards_owner[i] != MAX_PLAYERS)
                cards_drawn_count++;
            else
                break;

        uint256[] memory deck = new uint256[](cards_drawn_count);
        uint256 bonus_refund;
    
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
                    bonus_refund = (bets1[player_index] + bets2[player_index]) / (MAX_PLAYERS - 1);
                    for (uint8 i; i<MAX_PLAYERS; i++)
                        if (i != player_index)
                            payable(players_addresses[i]).transfer(DEPOSIT + bonus_refund);
                    return;
                }
            }
        }
        
        bonus_refund = (bets1[reporter_index] + bets2[reporter_index]) / (MAX_PLAYERS - 1);
        for (uint8 i; i<MAX_PLAYERS; i++)
            if (i != reporter_index)
                payable(players_addresses[i]).transfer(DEPOSIT + bonus_refund);
        
        emit award_event();
    }

    function get_rank(uint8 card) private view returns(uint8) {
        for (uint8 i; i<DECK_SIZE; i++)
            if (deck_coding[i] == card)
                return uint8(i / 4) + 2;
        return 0;
    }
    
    function get_suit(uint8 card) private view returns(uint8) {
        for (uint8 i; i<DECK_SIZE; i++)
            if (deck_coding[i] == card)
                return i % 4;
        return 0;
    }
    
    function calculate_hand(uint8 index) private returns(uint8[HAND_SIZE] memory) {
        uint256[DECK_SIZE] memory deck = get_deck();
        
        uint8[HAND_SIZE] memory hand;

        bytes32 len = bytes32(uint256(32));
        bytes memory base;
        bytes memory exp;
        bytes memory mod;

        uint8 cards_count;
        for (uint8 i; i<DECK_SIZE; i++) {
            uint8 player_index = cards_owner[i];
            if (player_index == index) {
                base = abi.encodePacked(deck[i]);
                exp  = abi.encodePacked(dec_keys[player_index]);
                mod  = abi.encodePacked(n);

                hand[cards_count] = uint8(modular_exponentiation(len, len, len, base, exp, mod));

                cards_count += 1;
                if (cards_count == HAND_SIZE)
                    break;
            }
        }

        return hand;
    }

    function sort_hand(uint8[HAND_SIZE] memory hand) private pure returns(uint8[HAND_SIZE] memory) {
        uint8 min;
        uint8 aux;
        for (uint8 i; i<HAND_SIZE-1; i++) {
            min = i;
            for (uint8 j=i+1; j<HAND_SIZE; j++)
                if (hand[j] < hand[min])
                    min = j;
            aux = hand[min];
            hand[min] = hand[i];
            hand[i] = aux;
        }

        return hand;
    }

    function evaluate_hand(uint8[HAND_SIZE] memory hand) private view returns(uint8, uint8, uint8) {
        uint8[HAND_SIZE] memory sorted_hand = sort_hand(hand);

        uint8 card1;
        uint8 card2;

        bool flush_flag = true;
        bool straight_flag = true;
        uint8 first_pair_count = 1;
        uint8 second_pair_count = 0;

        for (uint8 i=1; i<5; i++) {
            if (i == 4 && straight_flag && get_rank(sorted_hand[i]) == 14 && get_rank(sorted_hand[i-1]) == 5)
                straight_flag = true;
            else if (straight_flag && get_rank(sorted_hand[i]) != get_rank(sorted_hand[i-1]) + 1)
                straight_flag = false;

            if (flush_flag && get_suit(sorted_hand[i]) != get_suit(sorted_hand[i-1]))
                flush_flag = false;

            if (get_rank(sorted_hand[i]) == get_rank(sorted_hand[i-1])) {
                if (second_pair_count < 1) {
                    card1 = sorted_hand[i];
                    first_pair_count += 1;
                }
                else {
                    card2 = sorted_hand[i];
                    second_pair_count += 1;
                }
            }
            else if (first_pair_count > 1 && second_pair_count == 0)
                second_pair_count = 1;
        }

        if (first_pair_count == 1)
            card1 = sorted_hand[4];
        
        if (first_pair_count == 4)
            return (7, card1, card2);
        
        if (first_pair_count == 3) {
            if (second_pair_count == 2)
                return (6, card1, card2);
            else
                return (3, card1, card2);
        }
        
        if (first_pair_count == 2) {
            if (second_pair_count == 3)
                return (6, card1, card2);
            if (second_pair_count == 2)
                return (2, card2, card1);
            else
                return (1, card1, card2);
        }
        
        if (flush_flag && straight_flag)
            return (8, card1, card2);
        
        if (flush_flag)
            return (5, card1, card2);
        
        if (straight_flag)
            return (4, card1, card2); 
        else
            return (0, card1, card2);
    }

    function same_hand_ranking_result(uint8 index1, uint8 index2, uint8 hand_ranking, uint8 best_card1, uint8 best_card2, uint8 card1, uint8 card2) private view returns(uint8) {
        uint8 winner;

        if (hand_ranking == 0 || hand_ranking == 1 || hand_ranking == 4 || hand_ranking == 3 || hand_ranking == 6 || hand_ranking == 7) {
            if (get_rank(best_card1) > get_rank(card1))
                winner = index1;
            else if (get_rank(best_card1) < get_rank(card1))
                winner = index2;
            else if (get_suit(card1) > get_suit(card1))
                winner = index1;
            else if (get_suit(card1) < get_suit(card1))
                winner = index2;
        }
        else if (hand_ranking == 2) {
            if (get_rank(best_card1) > get_rank(card1))
                winner = index1;
            else if (get_rank(best_card1) < get_rank(card1))
                winner = index2;
            else if (get_rank(best_card2) > get_rank(card2))
                winner = index1;
            else if (get_rank(best_card2) < get_rank(card2))
                winner = index2;
            else if (get_suit(best_card1) > get_suit(card1))
                winner = index1;
            else if (get_suit(best_card1) < get_suit(card1))
                winner = index2;
        }
        else if (hand_ranking == 5 || hand_ranking == 8) {
            if (get_suit(best_card1) > get_suit(card1))
                winner = index1;
            else if (get_suit(best_card1) < get_suit(card1))
                winner = index2;
            else if (get_rank(best_card1) > get_rank(card1))
                winner = index1;
            else if (get_rank(best_card1) < get_rank(card1))
                winner = index2;
        }

        return winner;
    }
    
    function report_game_result() public {
        require (status == Status.verify);
        require (reporter_index != MAX_PLAYERS);

        uint256 gas_left = gasleft();
        
        uint8 winner = MAX_PLAYERS;
        uint8 best_hand = MAX_PLAYERS;
        uint8 best_card1;
        uint8 best_card2;
        
        for (uint8 i; i<MAX_PLAYERS; i++) {
            if (!fold_flags[i]) {
                uint8[HAND_SIZE] memory hand = calculate_hand(i);
                (uint8 evaluated_hand, uint8 card1, uint8 card2) = evaluate_hand(hand);

                if (best_hand == MAX_PLAYERS || evaluated_hand > best_hand) {
                    winner = i;
                    best_hand = evaluated_hand;
                    best_card1 = card1;
                    best_card2 = card2;
                }
                else if (best_hand == evaluated_hand) {
                    if (same_hand_ranking_result(winner, i, best_hand, best_card1, best_card2, card1, card2) == i) {
                        winner = i;
                        best_card1 = card1;
                        best_card2 = card2;
                    }
                }
            }
        }
        
        /* paying the winner */
        payable(players_addresses[winner]).transfer(pot);
        /* giving back the deposit to every honest player*/
        for (uint8 i; i<MAX_PLAYERS; i++)
            if (verify_results[i] == winner)
                payable(players_addresses[i]).transfer(DEPOSIT);
        /* paying back the reporter the gas he spent */
        if (verify_results[reporter_index] == winner)
            payable(players_addresses[reporter_index]).transfer(gas_left - gasleft());
    }

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
            let success := call(gas(),              // remaining gas
                                0x05,               // precomiled contract address
                                0,                  // wei
                                add(input, 0x20),   // in an array data starts after 32 bytes (0x20 in hex)
                                mload(input),       // mload loads a word (32 bytes), since in an array the first 32 bytes contain its size, it load "input's" lenght
                                add(result, 0x20),  // where to save the result
                                mload(result))      // size of result
        }

        return bytes_to_int(result);
    }
}