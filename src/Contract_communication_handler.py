from web3 import Web3, HTTPProvider
import json

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

	def transact(self, wei_amount: int):
			try:
				self.connection.eth.send_transaction(
					{'from': self.wallet_address,
					'to': self.contract_address,
					'value': wei_amount})
			except:
				print('Error during the transaction.')
				exit()

	def participate(self):
		try:
			self.contract.functions.participate().transact({'from': self.wallet_address})
		except:
			exit('Error while calling function "participate".')
	
	def get_my_turn_index(self):
		try:
			return self.contract.functions.get_my_turn_index().call({'from': self.wallet_address})
		except:
			exit('Error while calling function "get_my_turn_index".')