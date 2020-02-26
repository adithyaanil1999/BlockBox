from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from time import time
from urllib.parse import urlparse
import hashlib
import json
import sys
import pprint as pp


class blockchain:

    def __init__(self):
        self.chain = []
        self.difficulty = 2
        self.transactions = []
        self.create_genesis()

        # self.add_user_relation('alice','bob','rwx')
        # self.add_transaction('ID1','alice','bob','rwx')
        # print(self.transactions)
        # self.mine()
        # pp.pprint(self.chain)

    
    def create_genesis(self):
        #GENSIS BLOCK
        genesis_block_contents = {
            'blockNumber' : 1,
            'parentHash' : None,
            'timestamp': time(),
            'users_relation': {},
            'user_reqs': {},
            'hashcash': 0
        }
        genesis_block = {'hash': None, 'content': genesis_block_contents}
        genesis_block = self.proof_of_work(genesis_block)
        self.chain = [genesis_block]

    def mine(self):
        if not self.transactions:
            return False
        for i in self.transactions:
            last_block = self.chain[-1]
            new_block = self.make_block(i)
            if new_block[0] == 'user_rel':
                new_block = self.proof_of_work(new_block[1])
                flag = self.add_to_chain(new_block)
                if flag != True:
                    print("ERROR")
                    return -1
            elif new_block[0] == 'req':
                
                if len(last_block['content']['users_relation']) == 0:
                    new_block[1]['content']['user_reqs'][i[1]] = [i[2],i[3],'DENIED']
                else:
                    for j in range(len(last_block['content']['users_relation'])):
                        # print(j)
                        if last_block['content']['users_relation'][j][0] == i[2]:
                            flag = self.isValid(i,j)
                            # print(flag)
                            if flag == 1:
                                new_block[1]['content']['user_reqs'][i[1]] = [i[2],i[3],'APPROVED']
                            elif flag == -1:
                                new_block[1]['content']['user_reqs'][i[1]] = [i[2],i[3],'DENIED']
                new_block = self.proof_of_work(new_block[1])
                self.add_to_chain(new_block)

            self.transactions = []
        
        return new_block


    def is_valid_block(self,content,hash):
        return (hash.startswith('0' * self.difficulty) and hash == self.hash(content))

    def add_to_chain(self,block_req):
        parentBlock = self.chain[-1]
        parentHash = parentBlock['hash']
        expectedHash = block_req['content']['parentHash']
        if parentHash != expectedHash:
            return 1
        if not self.is_valid_block(block_req['content'].copy(), block_req['hash']):
            return 2
        self.chain.append(block_req)
        return True


    def proof_of_work(self, block):

        newBlock = block.copy()
        newBlock['hash'] = self.hash(newBlock)
        while not newBlock['hash'].startswith('0' * self.difficulty):
            newBlock['content']['hashcash'] += 1
            newBlock['hash'] = self.hash(newBlock['content'])
        return newBlock

    def add_user_relation(self,sender,receiver,permission):
        self.transactions.append(['user_rel',(sender,receiver),permission])
            

    def add_transaction(self,ID,sender,receiver,permission): 
        self.transactions.append(['req',ID,(sender,receiver),permission])
       
    def make_block(self,transaction):
        parentBlock = self.chain[-1]
        parentHash = parentBlock['hash']
        blockNumber = parentBlock['content']['blockNumber'] + 1
        if transaction[0] == 'req':
            userRelations = parentBlock['content']['users_relation']
            newreq = parentBlock['content']['user_reqs'].copy()
            newreq[transaction[1]] = [transaction[2], transaction[3]]
            block_contents = {
                'blockNumber' : blockNumber,
                'parentHash' : parentHash,
                'timestamp': time(),
                'users_relation': userRelations,
                'user_reqs': newreq,
                'hashcash': 0
            }
        if transaction[0] == 'user_rel':
            parentTransaction = parentBlock['content']['user_reqs']
            newUser = parentBlock['content']['users_relation'].copy()
            flag = False
            if len(list(parentBlock['content']['users_relation'].keys())) == 0:
                KEY = -1
            else:
                KEY = list(parentBlock['content']['users_relation'].keys())[-1]

            if KEY != -1:

                for i in range(len(newUser)):
                    if transaction[1] == newUser[i][0]:
                        newUser[i] = [transaction[1],transaction[2]]
                        flag = True
                
                if flag == False:
                    newUser[KEY+1] = [transaction[1],transaction[2]]

                
                block_contents = {
                    'blockNumber' : blockNumber,
                    'parentHash' : parentHash,
                    'timestamp': time(),
                    'users_relation': newUser,
                    'user_reqs': parentTransaction,
                    'hashcash': 0
                }
            else:
                newUser = parentBlock['content']['users_relation'].copy()
                newUser[KEY+1] = [transaction[1],transaction[2]]
                block_contents = {
                    'blockNumber' : blockNumber,
                    'parentHash' : parentHash,
                    'timestamp': time(),
                    'users_relation': newUser,
                    'user_reqs': parentTransaction,
                    'hashcash': 0
                }
            
            
        block = {'hash':None,'content':block_contents}
        return [transaction[0],block]


    def hash(self,block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def isValid(self,transaction,key):
        def split(word):
            return [char for char in word]
        parentBlock = self.chain[-1]
    
        GRANTED_permission = parentBlock['content']['users_relation'][key][1]
        REQ_permission = transaction[3]
        GRANTED_permission = split(GRANTED_permission)
        GRANTED_permission.sort()

        REQ_permission = split(REQ_permission)
        REQ_permission.sort()

        if(GRANTED_permission == REQ_permission):
            return 1
        else:
            return -1

blockChain = blockchain()

peers = set()
def add_node(node):
    peers.add(node)
    return blockChain.chain



app = Flask(__name__)
@app.route('/')
def hello_world():
    return 'DataWallet backend'

@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    node_address = request.get_json()["node_address"]
    # data = {"node_address": request.host_url}
    if not node_address:
        return "Invalid data", 400
    data = {"node_address": request.host_url}   
    headers = {'Content-Type': "application/json"}
    response = requests.post(node_address + "/add/new",data=json.dumps(data), headers=headers)
    print(response.json())
    if response.status_code == 201:
        global blockChain
        global peers
        blockChain.chain = response.json()['chain']
        peers.update(response.json()['peers'])
    response = {'message': 'SYNCED'}
    return jsonify(response), 200


@app.route('/add/new', methods=['POST'])
def new_node():
    values = request.get_json()
    required = ['node_address']
    if not all(k in values for k in required):
        return jsonify('Missing values'), 400
    chain = add_node(values['node_address'])
    response = {'peers': list(peers),'chain': chain,'message': f'Node has been added to network'}
    return jsonify(response), 201

@app.route('/block/mine', methods=['GET'])
def call_mine():
    block = blockChain.mine()
    response = {
        
        'message': 'Block Mined!',
        'block' : block,
        'chain_length': len(blockChain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    global blockChain
    longest_chain = None
    current_len = len(blockChain.chain)
    # print(current_len)
    for node in peers:
        response = requests.get('{}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len:
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockChain = longest_chain
        return True
    response = {
        'message': 'Resolved!',
        'block' : blockChain.chain,
        'chain_length': len(blockChain.chain),
    }
    return jsonify(response), 200


@app.route('/user/new', methods=['POST'])
def new_user_relation():
    values = request.get_json()
    required = ['sender_ID','receiver_ID','permission_req']
    if not all(k in values for k in required):
        return jsonify('Missing values'), 400
    blockChain.add_user_relation(values['sender_ID'], values['receiver_ID'], values['permission_req'])
    response = {'message': f'Added user relation to block'}
    return jsonify(response), 201


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['transaction_ID','sender_ID','receiver_ID','permission_req']
    if not all(k in values for k in required):
        return jsonify('Missing values'), 400
    blockChain.add_transaction(values['transaction_ID'],values['sender_ID'], values['receiver_ID'], values['permission_req'])
    response = {'message': values}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockChain.chain,
        'length': len(blockChain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':

    if(len(sys.argv) != 1):
        if sys.argv[1] == "-P":
            if len(sys.argv) < 3:
                raise Exception("ERROR : No port specfied")
            else:
                runPort = sys.argv[2]
                app.run(host='0.0.0.0', port=runPort)
    else:
        print("Running on default port 5000")
        app.run(host='0.0.0.0', port=5000)
