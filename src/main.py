import os

from data.data import Data

from trainer.trainer_utils import setup_model, setup_optimizer
from trainer.trainer import Trainer

from utils.parse import parse_training_args
from utils.utils import EarlyStopMonitor, set_seed
from utils.consts import *

if __name__ == '__main__':

    args = parse_training_args()

    BATCH_SIZE = args.bs
    NUM_NEIGHBORS = args.n_degree
    NUM_NEG = 1
    NUM_EPOCH = args.n_epoch
    NUM_HEADS = args.n_head
    DROP_OUT = args.drop_out
    GPU = args.gpu
    UNIFORM = args.uniform
    NEW_NODE = args.new_node
    USE_TIME = args.time
    AGG_METHOD = args.agg_method
    ATTN_MODE = args.attn_mode
    SEQ_LEN = NUM_NEIGHBORS
    DATASET = args.data
    NUM_LAYER = args.n_layer
    LEARNING_RATE = args.lr
    NODE_DIM = args.node_dim
    TIME_DIM = args.time_dim
    test_mode = True if args.test_mode else False
    print('Please note that the test mode is set to True. This means that the model will not be trained, but only tested on the test set/user.') if test_mode else print('Testing mode is set to False. The model will be trained only.')

    os.mkdir(RANK_RESULTS_DIR) if not os.path.isdir(RANK_RESULTS_DIR) else None
    os.mkdir(SAVE_MODEL_DIR(args)) if not os.path.isdir(SAVE_MODEL_DIR(args)) else None

    data = Data(DATASET, args)
    n_nodes = data.max_idx
    n_edges = data.num_total_edges

    set_seed(args.seed)
    
    pretrain = pretrain_path(args) if not test_mode else None
    
    model = setup_model(data, args, data.max_idx, GPU, NUM_LAYER, USE_TIME, AGG_METHOD, ATTN_MODE, SEQ_LEN, NUM_HEADS, DROP_OUT, NODE_DIM, TIME_DIM, 
                        load_pretrain=pretrain)
    optimizer = setup_optimizer(model, LEARNING_RATE, load_pretrain=pretrain)
    early_stopper = EarlyStopMonitor(max_round=5, higher_better=True)
    trainer = Trainer(data, model, optimizer, early_stopper, NUM_EPOCH, BATCH_SIZE, args)
    
    if not test_mode:
        trainer.train()
    
    if test_mode:
        result, output = trainer.test()
        print(result)
        print(output)
        
    trainer.save_model(SAVE_MODEL_DIR(args))