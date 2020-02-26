from flask import Flask, jsonify, request
from uuid import uuid4
from time import time
import hashlib
import json
import sys


class blockchain:

    def __init__(self):

        self.node = {} 
        #initialize the blockchain
        self.chain = []
        #GENSIS BLOCK
        genesis_block_contents = {
            'blockNumber' : 0,
            'parentHash' : None,
            'timestamp': time(),
            'users_relation': {},
            'transactions': {}
        }


        gensis_hash = self.hash(genesis_block_contents)

        self.genesis_block = {'hash': gensis_hash, 'content': genesis_block_contents}
        self.genesis_block_str = json.dumps(self.genesis_block, sort_keys=True)
        self.chain = [self.genesis_block]


    def add_node(self,node_addr):
        print('123')



    def add_user_relation(self,sender,receiver,permission):
        tup = (sender, receiver)
        parentBlock = self.chain[-1]
        if len(list(parentBlock['content']['users_relation'].keys())) == 0:
            KEY = -1
        else:
            KEY = list(parentBlock['content']['users_relation'].keys())[-1]
        if KEY != -1:
            for i in range(len(parentBlock['content']['users_relation'])):
                if parentBlock['content']['users_relation'][i][0] == tup:
                    return -1
                else:
                    parentHash = parentBlock['hash']
                    parentTransaction = parentBlock['content']['transactions']
                    blockNumber = parentBlock['content']['blockNumber'] + 1
                    newUser = parentBlock['content']['users_relation'].copy()
                    newUser[KEY+1] = [tup,permission]
                    block_contents = {
                        'blockNumber' : blockNumber,
                        'parentHash' : parentHash,
                        'timestamp': time(),
                        'users_relation': newUser,
                        'transactions': parentTransaction
                    }
                    block_hash = self.hash(block_contents)
                    block = {'hash':block_hash,'content':block_contents}
                    self.chain.append(block)
                    return block
        else:
            parentHash = parentBlock['hash']
            parentTransaction = parentBlock['content']['transactions']
            blockNumber = parentBlock['content']['blockNumber'] + 1
            newUser = parentBlock['content']['users_relation'].copy()
            newUser[KEY+1] = [tup,permission]
            block_contents = {
                'blockNumber' : blockNumber,
                'parentHash' : parentHash,
                'timestamp': time(),
                'users_relation': newUser,
                'transactions': parentTransaction
            }
            block_hash = self.hash(block_contents)
            block = {'hash':block_hash,'content':block_contents}
            self.chain.append(block)
            return block
            

                
    def ret_id(self):
        # creates random identifier
        return str(uuid4()).replace('-', '')

    def add_transaction(self,ID,sender,receiver,permission):
        parentBlock = self.chain[-1]
        relation = (sender,receiver)
        print(relation)
        for i in range(len(parentBlock['content']['users_relation'])):
            if parentBlock['content']['users_relation'][i][0] == relation:
                flag = self.isValid([(sender,receiver),permission],i)
                if flag == 1:
                    block = self.make_block([ID,(sender,receiver),permission,'approved'])
                    self.chain.append(block)
                elif flag == -1:
                    block = self.make_block([ID,[(sender,receiver),permission,'rejected']])
                    self.chain.append(block)
            else:
                return -1
       
    def make_block(self,transaction):
        parentBlock = self.chain[-1]
        parentHash = parentBlock['hash']
        blockNumber = parentBlock['content']['blockNumber'] + 1
        userRelations = parentBlock['content']['users_relation']
        newTransaction = parentBlock['content']['transactions'].copy()
        newTransaction[transaction[0]] = transaction[1]
        block_contents = {
            'blockNumber' : blockNumber,
            'parentHash' : parentHash,
            'timestamp': time(),
            'users_relation': userRelations,
            'transactions': newTransaction
        }
        block_hash = self.hash(block_contents)
        block = {'hash':block_hash,'content':block_contents}
        return block


    def hash(self,block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def isValid(self,transaction,key):
        def split(word):
            return [char for char in word]
        parentBlock = self.chain[-1]
        GRANTED_permission = parentBlock['content']['users_relation'][key][1]
        REQ_permission = transaction[1]



        GRANTED_permission = split(GRANTED_permission)
        GRANTED_permission.sort()

        REQ_permission = split(REQ_permission)
        REQ_permission.sort()

        if(GRANTED_permission == REQ_permission):
            return 1
        else:
            return -1

    def checkHash(self,block):
        expectedHash = self.hash(block['contents'])
        if block['hash']!=expectedHash:
            raise Exception('Hash does not match contents of block %s'% block['contents']['blockNumber'])
        return True

    


blockChain = blockchain()

app = Flask(__name__)
blockChain = blockchain()
@app.route('/')
def hello_world():
    return 'DataWallet backend'


@app.route('/add/new', methods=['POST'])
def new_user():
    values = request.get_json()
    required = ['node_address']
    if not all(k in values for k in required):
        return jsonify('Missing values'), 400
    index = blockChain.add_node(values['node_address'])
    if index == -1:
        return jsonify('Node already exsist'), 400
    else:
        response = {'message': f'Node has been added to network'}
        return jsonify(response), 201

@app.route('/user/new', methods=['POST'])
def new_user():
    values = request.get_json()
    required = ['sender_ID','receiver_ID','permission_req']
    if not all(k in values for k in required):
        return jsonify('Missing values'), 400
    index = blockChain.add_user_relation(values['sender_ID'], values['receiver_ID'], values['permission_req'])
    if index == -1:
        return jsonify('User already exsist'), 400
    else:
        response = {'message': f'Added user relation to block'}
        return jsonify(response), 201


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['transaction_ID','sender_ID','receiver_ID','permission_req']
    if not all(k in values for k in required):
        return jsonify('Missing values'), 400
    index = blockChain.add_transaction(values['transaction_ID'],values['sender_ID'], values['receiver_ID'], values['permission_req'])
    if index == -1:
        return jsonify('User Relation not found'), 400
    else:
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
