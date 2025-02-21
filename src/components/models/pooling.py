import torch
# torch.cuda.empty_cache()
from src.components.models.layers import MergeLayer


class LSTMPool(torch.nn.Module):
    """
    LSTMPool is a class for merging and concatenating the input features, instead of using attention.
    """
    def __init__(self, feat_dim, time_dim):
        super(LSTMPool, self).__init__()
        self.feat_dim = feat_dim
        self.time_dim = time_dim
        
        self.att_dim = feat_dim + time_dim
        
        self.act = torch.nn.ReLU()
        
        self.lstm = torch.nn.LSTM(input_size=self.att_dim, 
                                  hidden_size=self.feat_dim, 
                                  num_layers=1, 
                                  batch_first=True)
        self.merger = MergeLayer(feat_dim, feat_dim, feat_dim, feat_dim)

    def forward(self, src, src_t, seq, seq_t,  mask):
        seq_x = torch.cat([seq, seq_t], dim=2)
            
        _, (hn, _) = self.lstm(seq_x)
        
        hn = hn[-1, :, :] #hn.squeeze(dim=0)

        out = self.merger.forward(hn, src)
        return out, None
    

class MeanPool(torch.nn.Module):
    """
    MeanPool is a class for merging and concatenating the input features, instead of using attention.
    """
    def __init__(self, feat_dim):
        super(MeanPool, self).__init__()
        self.feat_dim = feat_dim
        self.act = torch.nn.ReLU()
        self.merger = MergeLayer(feat_dim, feat_dim, feat_dim, feat_dim)
        
    def forward(self, src, src_t, seq, seq_t, mask):
        src_x = src
        seq_x = torch.cat([seq], dim=2) #[B, N, D]
        hn = seq_x.mean(dim=1) #[B, D]
        output = self.merger(hn, src_x)
        return output, None

