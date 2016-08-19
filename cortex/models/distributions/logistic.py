'''Module for logistic distributions.

'''

from collections import OrderedDict
import numpy as np
from theano import tensor as T

from . import Distribution
from ... import utils
from ...utils import floatX


def _logistic(trng, p, size=None):
    dim = p.shape[p.ndim-1] // 2
    mu = utils.slice(p, 0, dim)
    log_s = utils.slice(p, 1, dim)
    if size is None:
        size = mu.shape
    epsilon = trng.uniform(size=size, dtype=floatX)
    return mu + T.log(epsilon / (1 - epsilon)) * T.exp(log_s)

def _neg_logistic_log_prob(x, p, sum_probs=True):
    dim = p.shape[p.ndim-1] // 2
    mu = utils.slice(p, 0, dim)
    log_s = utils.slice(p, 1, dim)
    g = (x - mu) / T.exp(log_s)
    energy = -g + log_s + 2 * T.log(1 + T.exp(g))
    if sum_probs:
        return energy.sum(axis=energy.ndim-1)
    else:
        return energy

def _logistic_entropy(p):
    dim = p.shape[p.ndim-1] // 2
    log_s = utils.slice(p, 1, dim)
    entropy = log_s + 2.0
    return entropy.sum(axis=entropy.ndim-1)


class Logistic(Distribution):
    '''Logistic distribution.

    :math:`p(x)=\\frac{e^{\\frac{x - \mu}{s}}}{s(1+e^{\\frac{x - \mu}{s}})^2}`

    Note:
        Not to be confused with logistic function.

    '''
    is_continuous = True
    scale = 2

    def __init__(self, dim, name='logistic', **kwargs):
        self.f_sample = _logistic
        self.f_neg_log_prob = _neg_logistic_log_prob
        self.f_entropy = _logistic_entropy
        super(Logistic, self).__init__(dim, name=name, **kwargs)

    def init_params(self):
        mu = np.zeros((self.dim,)) + self.inits.get('mu', 0.)
        log_s = np.zeros((self.dim,)) + self.inits.get('log_s', 0.)

        self.params = OrderedDict(
            mu=mu, log_s=log_s)

    def get_params(self):
        return [self.mu, self.log_s]

    def quantile(self, epsilon, P):
        mu, log_s = self.split_prob(P)
        return mu + T.log(epsilon / (1 - epsilon)) * T.exp(log_s)

    def random_variables(self, size):
        return self.trng.uniform(size=size, dtype=floatX)

    def standard_prob(self, x, p=None):
        if p is None: p = self.get_prob(*self.get_params())
        return T.exp(-self.neg_log_prob(x, p))

    def permute(self, scale=2.):
        h0 = self.mu
        s = T.nlinalg.AllocDiag()(T.exp(self.log_s)).astype(floatX)
        h = scale * s + h0[None, :]
        return OrderedDict(mean=h0, perm=h)

    def viz(self, P0, P=None):
        if P is None: P = self.get_prob(*self.get_params())

        y0_mu, y0_logs = self.split_prob(P0)
        y_mu, y_logs = self.split_prob(P)
        py = (y_mu - y0_mu) / T.exp(y0_logs)
        return py


_classes = {'logistic': Logistic}