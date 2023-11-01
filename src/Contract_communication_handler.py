from web3 import Web3, HTTPProvider
import json
import time

DEBUG = False

class Contract_communication_handler:

	def __init__(self, addresses_file_path: str, abi_file_path: str, user_wallet_address: str, user_wallet_password: str):
		try:
			with open(addresses_file_path) as file:
				lines = [line.strip() for i, line in enumerate(file)]

				if len(lines) != 2:
					raise Exception('Addresses file does not meet the right format.')
				
				split = lines[0].split(': ')
				if len(split) == 2 or split[0] == 'node_address':
					self.node_address = split[1]
				else:
					raise Exception('Error in Addresses file line 1.')
				
				split = lines[1].split(': ')
				if len(split) == 2 or split[0] == 'contract_address':
					self.contract_address = split[1]
				else:
					raise Exception('Error in Addresses file line 2.')

		except FileNotFoundError:
			exit('Addresses file not found.')
		except Exception as e:
			exit(str(e))
		
		try:
			with open(abi_file_path) as file:
				self.abi = json.load(file)
		except FileNotFoundError:
			exit('Abi file not found.')

		try:
			self.connection = Web3(HTTPProvider(self.node_address))
			if not self.connection.is_connected():
				exit('Connection to node "' + self.node_address + '" failed.')
		except:
			exit('Connection to node "' + self.node_address + '" failed.')
		
		try:
			self.wallet_address = user_wallet_address
			self.wallet_password = user_wallet_password
			self.connection.eth.defaultAccount = self.connection.eth.account.from_key(self.wallet_password)
		except:
			exit('User\'s wallet address error.')
		
		try:
			self.contract = self.connection.eth.contract(address=self.contract_address, abi=self.abi)
			# call some function to verify connection
		except:
			exit('Error during the creation of the "Contract" object.')

	def catch_shuffle_event(self, turn_index):

		# check if my last transaction triggered the event
		transaction = self.connection.eth.get_transaction(self.last_transaction)
		block_number = transaction['blockNumber']
		logs = self.contract.events.shuffle_event.get_logs(fromBlock=block_number)
		if len(logs) >= 1:
			_turn_index = logs[-1]['args']['turn_index']

			if DEBUG: print('Past event caught (from block', block_number, '). {turn_index:', _turn_index, '}')
			if _turn_index == turn_index:
				return
		
		# otherwise listen for it
		event_filter = self.contract.events.shuffle_event.create_filter(fromBlock='latest')

		while True:
			for event in event_filter.get_new_entries():
				_turn_index = event['args']['turn_index']

				if DEBUG: print('New event caught. {turn_index:', _turn_index, '}')
				if _turn_index == turn_index:
					return
				
			time.sleep(1)
	
	def catch_draw_event(self, turn_index):

		# check if my last transaction triggered the event
		transaction = self.connection.eth.get_transaction(self.last_transaction)
		block_number = transaction['blockNumber']
		logs = self.contract.events.draw_event.get_logs(fromBlock=block_number)
		if len(logs) >= 1:
			_turn_index = logs[-1]['args']['turn_index']
			draw_index = logs[-1]['args']['draw_index']
			topdeck_index = logs[-1]['args']['topdeck_index']
			hand_size = logs[-1]['args']['hand_size']

			if DEBUG: print('Past event caught (from block', block_number, ').',
		          	        ' {turn_index:', _turn_index,
		 		            ', draw_index:', draw_index,
				            ', topdeck_index:', topdeck_index,
				            ', hand_size:', hand_size, '}')
			if _turn_index == turn_index:
				return draw_index, topdeck_index, hand_size
		
		# otherwise listen for it
		event_filter = self.contract.events.draw_event.create_filter(fromBlock='latest')

		while True:
			for event in event_filter.get_new_entries():
				_turn_index = event['args']['turn_index']
				draw_index = event['args']['draw_index']
				topdeck_index = event['args']['topdeck_index']
				hand_size = event['args']['hand_size']

				if DEBUG: print('New event caught.',
		                        ' {turn_index:', _turn_index,
					            ', draw_index:', draw_index,
					            ', topdeck_index:', topdeck_index,
					            ', hand_size:', hand_size, '}')
				if _turn_index == turn_index:
					return draw_index, topdeck_index, hand_size
				
			time.sleep(1)

	def catch_stake_event(self, turn_index, end_index):

		# check if my last transaction triggered the event
		transaction = self.connection.eth.get_transaction(self.last_transaction)
		block_number = transaction['blockNumber']
		logs = self.contract.events.stake_event.get_logs(fromBlock=block_number)
		if len(logs) >= 1:
			_turn_index = logs[-1]['args']['turn_index']

			if DEBUG: print('Past event caught (from block', block_number, ').',
		                    ' {turn_index:', _turn_index, '}')
			if _turn_index == turn_index or _turn_index == end_index:
				return _turn_index
		
		# otherwise listen for it
		event_filter = self.contract.events.stake_event.create_filter(fromBlock='latest')

		while True:
			for event in event_filter.get_new_entries():
				_turn_index = event['args']['turn_index']

				if DEBUG: print('New event caught.',
					            ' {turn_index:', _turn_index, '}')
				if _turn_index == turn_index or _turn_index == end_index:
					return _turn_index
				
			time.sleep(1)
	
	def catch_key_reveal_event(self):

		# check if my last transaction triggered the event
		transaction = self.connection.eth.get_transaction(self.last_transaction)
		block_number = transaction['blockNumber']
		logs = self.contract.events.key_reveal_event.get_logs(fromBlock=block_number)
		if len(logs) >= 1:
			if DEBUG: print('Past event caught (from block', block_number, '). ')
			return
		
		# otherwise listen for it
		event_filter = self.contract.events.key_reveal_event.create_filter(fromBlock='latest')

		while True:
			for _ in event_filter.get_new_entries():
				if DEBUG: print('New event caught.')
				return
				
			time.sleep(1)

	def catch_optimistic_verify_event(self):

		# check if my last transaction triggered the event
		transaction = self.connection.eth.get_transaction(self.last_transaction)
		block_number = transaction['blockNumber']
		logs = self.contract.events.optimistic_verify_event.get_logs(fromBlock=block_number)
		if len(logs) >= 1:
			if DEBUG: print('Past event caught (from block', block_number, '). ')
			return
		
		# otherwise listen for it
		event_filter = self.contract.events.optimistic_verify_event.create_filter(fromBlock='latest')

		while True:
			for _ in event_filter.get_new_entries():
				if DEBUG: print('New event caught.')
				return
				
			time.sleep(1)
	
	def catch_award_event(self):

		# check if my last transaction triggered the event
		transaction = self.connection.eth.get_transaction(self.last_transaction)
		block_number = transaction['blockNumber']
		logs = self.contract.events.award_event.get_logs(fromBlock=block_number)
		if len(logs) >= 1:
			if DEBUG: print('Past event caught (from block', block_number, '). ')
			return
		
		# otherwise listen for it
		event_filter = self.contract.events.award_event.create_filter(fromBlock='latest')

		while True:
			for _ in event_filter.get_new_entries():
				if DEBUG: print('New event caught.')
				return
				
			time.sleep(1)

	def participate(self, fee):
		try:
			self.last_transaction = self.contract.functions.participate().transact({'from': self.wallet_address, 'value': fee})
		except:
			exit('Error while calling function "participate".')
	
	def get_my_turn_index(self):
		try:
			return self.contract.functions.get_my_turn_index().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_my_turn_index".')
	
	def shuffle_dealer(self, n, deck_coding, encrypted_deck):
		try:
			self.last_transaction = self.contract.functions.shuffle_dealer(n, deck_coding, encrypted_deck).transact({'from': self.wallet_address})
		except:
			exit('Error while calling function "shuffle_dealer".')
	
	def get_n(self):
		try:
			return self.contract.functions.get_n().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_n".')
	
	def get_deck_coding(self):
		try:
			return self.contract.functions.get_deck_coding().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_deck_coding".')
	
	def get_encrypted_deck(self):
		try:
			return self.contract.functions.get_encrypted_deck().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_encrypted_deck".')
	
	def get_max_players(self):
		try:
			return self.contract.functions.get_max_players().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_max_players".')
	
	def get_participation_fee(self):
		try:
			return self.contract.functions.get_participation_fee().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_participation_fee".')
	
	def shuffle(self, encrypted_deck):
		try:
			self.last_transaction = self.contract.functions.shuffle(encrypted_deck).transact({'from': self.wallet_address})
		except:
			exit('Error while calling function "shuffle".')
	
	def reveal_cards(self, encrypted_cards):
		try:
			self.last_transaction = self.contract.functions.reveal_cards(encrypted_cards).transact({'from': self.wallet_address})
		except:
			exit('Error while calling function "reveal_cards".')
	
	def draw(self):
		try:
			self.last_transaction = self.contract.functions.draw().transact({'from': self.wallet_address})
		except:
			exit('Error while calling function "draw".')
	
	def bet(self, fee):
		try:
			self.last_transaction = self.contract.functions.bet().transact({'from': self.wallet_address, 'value': fee})
		except:
			exit('Error while calling function "bet".')
	
	def call(self, fee):
		try:
			self.last_transaction = self.contract.functions.call().transact({'from': self.wallet_address, 'value': fee})
		except:
			exit('Error while calling function "call".')
	
	def check(self):
		try:
			self.last_transaction = self.contract.functions.check().transact({'from': self.wallet_address})
		except:
			exit('Error while calling function "check".')
	
	def fold(self):
		try:
			self.last_transaction = self.contract.functions.fold().transact({'from': self.wallet_address})
		except:
			exit('Error while calling function "fold".')
	
	def get_last_raise_index(self):
		try:
			return self.contract.functions.get_last_raise_index().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_last_raise_index".')
	
	def get_bets(self):
		try:
			return self.contract.functions.get_bets().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_bets".')
	
	def get_fold_flags(self):
		try:
			return self.contract.functions.get_fold_flags().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_fold_flags".')
	
	def key_reveal(self, e, d):
		try:
			return self.contract.functions.key_reveal(e, d).transact({'from': self.wallet_address})
		except:
			exit('Error while calling function "key_reveal".')
		
	def get_enc_keys(self):
		try:
			return self.contract.functions.get_enc_keys().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_enc_keys_call".')
		
	def get_dec_keys(self):
		try:
			return self.contract.functions.get_dec_keys().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_dec_keys_call".')

	def optimistic_verify(self, winner_index):
		try:
			return self.contract.functions.optimistic_verify(winner_index).transact({'from': self.wallet_address})
		except:
			exit('Error while calling function "optimistic_verify".')
