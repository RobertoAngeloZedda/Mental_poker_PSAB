from Contract_communication_handler import *

cch = Contract_communication_handler(addresses_file_path='./addresses.txt', 
                                     abi_file_path='./abi.json',
                                     user_wallet_address='0xAC2444B1e48b6024f6d11c2a67584fe706C4FF9B',
                                     user_wallet_password='0x66957c694c0ff3661f6716a5befa7ba2466f159fa2b4a040780dfa263a90e96e')

cch.participate()
assigned_index = cch.get_my_turn_index()
print('Assigned index:', assigned_index)

print('Listening for events')
cch.catch_event(1, 0)

print('Can start shuffling..')