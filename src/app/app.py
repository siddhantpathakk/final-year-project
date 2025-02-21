import json
import os
import streamlit as st
import pandas as pd

from plot import make_ctbg, make_ctbg_with_recommendations
from src.components.trainer.trainer import Trainer
from src.components.utils.parse import parse_training_args
from src.components.trainer.trainer_utils import setup_model, setup_optimizer
from src.components.utils.utils import EarlyStopMonitor, set_seed
from src.components.data.data import Data
from src.components.utils.consts import *


@st.cache_data(show_spinner=False)
def get_output(dataset, user_id):
    args = parse_training_args(dataset=dataset)
    DATASET = args.data

    BATCH_SIZE = args.bs
    NUM_NEIGHBORS = args.n_degree
    NUM_EPOCH = args.n_epoch
    NUM_HEADS = args.n_head
    DROP_OUT = args.drop_out
    GPU = args.gpu
    USE_TIME = args.time
    AGG_METHOD = args.agg_method
    ATTN_MODE = args.attn_mode
    SEQ_LEN = NUM_NEIGHBORS
    NUM_LAYER = args.n_layer
    LEARNING_RATE = args.lr
    NODE_DIM = args.node_dim
    TIME_DIM = args.time_dim if DATASET != 'ml-100k' else 8
    infer_mode = True 
    USER_ID = user_id

    cwd = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    set_seed(args.seed)

    data = Data(DATASET, args)
    user_history = data.get_user_history(USER_ID)

    # pretrain = pretrain_app_path_scse(args, cwd)
    # pretrain = pretrain_app_path_slab(args, cwd)
    pretrain = pretrain_app_path_new(args, cwd) if DATASET != 'ml-100k' else pretrain_ml100k_slab(args, cwd)

    # show spinner
    with st.spinner("\tCreating model instance..."):
        model = setup_model(data, args, data.max_idx, GPU, NUM_LAYER, USE_TIME, AGG_METHOD, ATTN_MODE, SEQ_LEN, NUM_HEADS, DROP_OUT, NODE_DIM, TIME_DIM,
                            load_pretrain=pretrain)
        optimizer = setup_optimizer(model, LEARNING_RATE, load_pretrain=pretrain)
        early_stopper = EarlyStopMonitor(max_round=5, higher_better=True)
        trainer = Trainer(data, model, optimizer, early_stopper,
                        NUM_EPOCH, BATCH_SIZE, args)

    if infer_mode:
        with st.spinner("\tRunning inference..."):
            _, output = trainer.test(user_id=USER_ID)
    
    return user_history, output


# Streamlit UI
# Set page configuration
st.set_page_config(page_title='TAGON',
                   page_icon=":material/sdk:",
                   layout='centered',
                   initial_sidebar_state='expanded',
                   menu_items={
                       "Get Help": "https://www.github.com/siddhantpathakk/tagon",
                       'About': "This is a final year project demonstration for TAGON."
                   })

st.title('FYP Demonstration for TAGON')

# Load user set
userset_path = 'src/app/userset.json'
userset_map = json.load(open(userset_path, 'r'))

# Sidebar UI - Dataset and User ID Selection
dataset_names = ['ml-100k', 'Baby', 'Digital_Music', 'Toys_and_Games', 'Tools_and_Home_Improvement']
selected_dataset = st.sidebar.selectbox("Select dataset", dataset_names, index=dataset_names.index(
    st.session_state.get('selected_dataset', dataset_names[0])))

default_user_id = userset_map[selected_dataset][0]
user_id = st.sidebar.selectbox("Select User ID", userset_map[selected_dataset], index=userset_map[selected_dataset].index(
    st.session_state.get('user_id', default_user_id)))
# user_id = st.sidebar.text_input("Enter User ID (randomly chosen by default)", str(st.session_state.get('user_id', default_user_id)))
user_id = int(user_id)

# Validity check for User ID
valid_user_id_flag = user_id in userset_map[selected_dataset]
if not valid_user_id_flag:
    st.error(f"User ID {user_id} not found in the dataset")
    st.toast("Please enter a valid User ID", icon="🚫")

# Additional Settings
st.sidebar.subheader("CTBG Settings")
trim = st.sidebar.slider("Trim (for CTBG)", 1, 20, 4)
show_csv = st.sidebar.checkbox("Show CSV Data", value=True, disabled=True)

# Prediction Button
n_recs = st.sidebar.slider("Number of recommendations to make", 1, 20, 5)
predict_button = st.sidebar.button('Predict', 
                                #    disabled=not valid_user_id_flag, 
                                   )

# Process predictions
if predict_button and valid_user_id_flag and n_recs > 0:
# if predict_button and n_recs > 0:
    st.toast("Running predictions...", icon="⏳")
    user_hist, output = get_output(selected_dataset, user_id)
    st.session_state['user_hist'] = user_hist
    st.session_state['output'] = output
    st.toast("Predictions completed!", icon="✅")

# Display Results
if 'output' in st.session_state and valid_user_id_flag:
# if 'output' in st.session_state:
    st.header("Continuous Time Bipartite Graph (CTBG)")
    fig = make_ctbg(st.session_state['user_hist'], selected_dataset, trim=trim, theme=st.get_option("theme.backgroundColor"))
    st.plotly_chart(fig)

    dataframe = pd.DataFrame(st.session_state['user_hist'])
    dataframe['ts'] = pd.to_datetime(dataframe['ts'], unit='s')
    dataframe = dataframe.sort_values(by='ts', ascending=False)
    dataframe = dataframe[['u', 'i', 'ts']].head(trim)
    user_hist = dataframe.copy()
    if show_csv:
        st.dataframe(dataframe, hide_index=True, width=1000)

    out_dataframe = pd.DataFrame(st.session_state['output']).rename(columns={'u_pos_gd': 'i', 'u_ind': 'u', 'timestamp': 'ts'})
    out_dataframe['ts'] = pd.to_datetime(out_dataframe['ts'], unit='s')
    # st.dataframe(out_dataframe, hide_index=True, width=1000)
    ts_list_historical = user_hist['i'].values
    ts_list_new = out_dataframe['i'].values
    common_items = list(set(ts_list_historical) & set(ts_list_new))
    
    out_df2 = out_dataframe.copy()
    
    reference_point = st.selectbox("Choose reference point for next-item prediction", [None]+common_items, index=0)
    if reference_point:
        st.header("Recommendations")
        # st.dataframe(out_dataframe, hide_index=True, width=1000)
        st.write(f"Top {n_recs} recommendations:")
        recs = out_dataframe[out_dataframe['i'] == reference_point]['predicted'].iloc[0][:n_recs]
        # st.write(' - '.join(str(x) for x in recs))
        fig_rec = make_ctbg_with_recommendations(user_hist, selected_dataset, trim=trim, 
                                                reference_id=reference_point, 
                                                recommendations=recs)
        st.plotly_chart(fig_rec)
        
        if show_csv:
            rec_df = pd.merge(dataframe, out_dataframe, on=['u', 'ts', 'i'], how='outer').dropna()
            rec_df['ts'] = pd.to_datetime(rec_df['ts'], unit='s')
            rec_df['predicted'] = rec_df['predicted'].apply(lambda x: x[:5])
            st.dataframe(rec_df, hide_index=True, width=1000)