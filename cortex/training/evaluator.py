'''Trainer class.

Does typical training work.

'''

from collections import OrderedDict
import logging
import numpy as np
from progressbar import (
    Bar,
    ProgressBar,
    Percentage,
    Timer
)
import theano
from theano import tensor as T
import time

from .op import _ops
from ..utils.logger import get_class_logger
from ..utils.tools import check_bad_nums, update_dict_of_lists


class Evaluator(object):
    def __init__(self, session, valid_stat='cost', valid_sign=1):
        if valid_sign not in [-1, 1]:
            raise TypeError('valid_sign must be either 1 or -1.')
        self.session = session
        self.best_value = None
        self.best_epoch = 0
        self.valid_sign = valid_sign
        self.valid_stat = valid_stat
        self.set_f_stats()

    def set_f_stats(self):
        stats = OrderedDict()
        stats.update(**self.session.stats)
        stats.update(**self.session.costs)
        stats['total_cost'] = self.session.cost
        self.f_stats = theano.function(self.session.inputs, stats)

        '''
        if out_path is not None:
            bestfile = path.join(out_path, '{name}_best.npz'.format(name=name))
        else:
            bestfile = None
        '''

    def __call__(self, batch_size=None, data_mode=None):
        widgets = ['Testing (%s set): ' % data_mode, Percentage(),
                   ' (', Timer(), ')']
        self.session.reset_data(mode=data_mode)
        n = self.session.get_dataset_size(mode=data_mode)
        pbar    = ProgressBar(widgets=widgets, maxval=n).start()
        results = OrderedDict()
        if batch_size is None:
            batch_size = n

        while True:
            try:
                inputs = self.session.next_batch(
                    mode=data_mode, batch_size=batch_size)
                r = self.f_stats(*inputs)

                for k, v in r.iteritems():
                    if isinstance(v, theano.sandbox.cuda.CudaNdarray):
                        r[k] = np.asarray(v)
                update_dict_of_lists(results, **r)
                pbar.update(self.session.data_pos)

            except StopIteration:
                print
                break

        for k, v in results.iteritems():
            try:
                results[k] = np.mean(v)
            except Exception as e:
                logging.error(k)
                logging.error(v)
                raise e

        print
        return results

    def validate(self, results, epoch):

        if self.valid_stat not in results.keys():
            raise KeyError('valid_stat `%s` not found. Available: %s'
                           % (self.valid_stat, results.keys()))
        valid_value = results[self.valid_stat]
        valid_value *= self.valid_sign

        if self.best_value is None or valid_value < self.best_value:
            print 'Found best %s: %.2f' % (self.valid_stat, valid_value)
            self.best_value = valid_value
            self.best_epoch = epoch
            return True
        else:
            return False