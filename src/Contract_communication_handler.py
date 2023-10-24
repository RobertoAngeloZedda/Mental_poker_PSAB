from web3 import Web3, HTTPProvider
import json
import time

class Contract_communication_handler:
	
	def __init__(self, addresses_file_path: str, abi_file_path: str, user_wallet_address: str, user_wallet_password: str):
		try:
			with open(addresses_file_path) as file:
				lines = [line for i, line in enumerate(file)]

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
			print('Addresses file not found.')
			exit()
		except Exception as e:
			print(str(e))
			exit()
		
		try:
			with open(abi_file_path) as file:
				self.abi = json.load(file)
		except FileNotFoundError:
			print('Abi file not found.')
			exit()

		try:
			self.connection = Web3(HTTPProvider(self.node_address))
		except:
			print('Connection to node "' + self.node_address + '" failed.')
			exit()
		
		try:
			self.wallet_address = user_wallet_address
			self.wallet_password = user_wallet_password
			self.connection.eth.defaultAccount = self.connection.eth.account.from_key(self.wallet_password)
		except:
			print('User\'s wallet address error.')
			exit()
		
		try:
			self.contract = self.connection.eth.contract(address=self.contract_address, abi=self.abi)
		except:
			print('Error during the creation of the "Contract" object.')
			exit()

	def catch_shuffle_event(self, turn_index):

		# check if my last transaction triggered the event
		transaction = self.connection.eth.get_transaction(self.last_transaction)
		block_number = transaction['blockNumber']
		logs = self.contract.events.shuffle_event.get_logs(fromBlock=block_number)
		if len(logs) >= 1:
			_turn_index = logs[-1]['args']['turn_index']

			print('Past event caught (from block', block_number, '). {turn_index:', _turn_index, '}')
			if _turn_index == turn_index:
				return
		
		# otherwise listen for it
		event_filter = self.contract.events.shuffle_event.create_filter(fromBlock='latest')

		while True:
			for event in event_filter.get_new_entries():
				_turn_index = event['args']['turn_index']

				print('New event caught. {turn_index:', _turn_index, '}')
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

			print('Past event caught (from block', block_number, ').',
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

				print('New event caught.',
		              ' {turn_index:', _turn_index,
					  ', draw_index:', draw_index,
					  ', topdeck_index:', topdeck_index,
					  ', hand_size:', hand_size, '}')
				if _turn_index == turn_index:
					return draw_index, topdeck_index, hand_size
				
			time.sleep(1)


	def transact(self, wei_amount: int):
		try:
			self.connection.eth.send_transaction(
				{'from': self.wallet_address,
				'to': self.contract_address,
				'value': wei_amount})
		except:
			print('Error during the transaction.')
			exit()

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
			print('Error while calling function "shuffle_dealer".')
			exit()
	
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