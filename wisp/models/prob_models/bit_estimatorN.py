from wisp.models.prob_models.bit_estimator import *
from wisp.models.prob_models import *

class Conv1DBit(nn.Conv1d):
    def __init__(self, act, width, **kwargs):
        super(Conv1DBit, self).__init__(**kwargs)
        self.act = act
        self.width = width

    def forward(self, input: Tensor, dims:tuple = None) -> Tensor:
        if dims is None:
            return self._conv_forward(input, self.act(self.weight), self.bias)
        else:
            return F.conv1d(input, self.act(self.weight[dims[0]:dims[1],:,:]), \
                            self.bias[dims[0]:dims[1]] if self.bias is not None else None,
                            groups=dims[2])

class BitparmN(nn.Module):
    '''
    save params
    '''
    def __init__(self, channel, width=1, final=False, initial=False):
        super(BitparmN, self).__init__()
        assert not (initial and final)
        self.final = final
        self.width = width
        in_channel = channel if initial else channel*width
        out_channel = channel if final else channel*width
        self.conv1 = Conv1DBit(F.sigmoid, width, in_channels=in_channel, out_channels=out_channel, \
                               kernel_size=1, groups=channel, bias=True)
        if not final:
            self.conv2 = Conv1DBit(torch.tanh, width, in_channels=out_channel,out_channels=out_channel,\
                                   kernel_size=1,groups=out_channel,bias=False)

    def forward(self, x, single_channel=None):
        if single_channel is not None:
            mult = 1 if self.final else self.width
            dims1 = (single_channel * mult, (single_channel+1) * mult,1)
            dims2 = (single_channel * self.width, (single_channel+1)*self.width,self.width)
        else:
            dims1 = None
            dims2 = None
        x = self.conv1(x, dims1)

        if self.final:
            return torch.sigmoid(x)
        else:
            return x + self.conv2(torch.tanh(x), dims2)

class BitEstimatorN(nn.Module):
    '''
    Estimate bit
    '''
    def __init__(self, channel, width):
        super(BitEstimatorN, self).__init__()
        self.f1 = BitparmN(channel, width, False, True)
        self.f2 = BitparmN(channel, width, False, False)
        self.f3 = BitparmN(channel, width, False, False)
        self.f4 = BitparmN(channel, width, True, False)
        
    def forward(self, x, single_channel=None):
        x = x.unsqueeze(-1)
        x = self.f1(x, single_channel)
        x = self.f2(x, single_channel)
        x = self.f3(x, single_channel)
        x = self.f4(x, single_channel)
        return x.squeeze(-1)
