'''
Utilities for handling nifti files.
'''

import argparse
from glob import glob
import nibabel as nib
from nipy import save_image, load_image
import numpy as np
import os
from os import path
import pickle

from random import shuffle
import re
from scipy import io
from scipy.stats import kurtosis
from scipy.stats import skew
import sys
from sys import stdout


def find_niftis(source):
    return glob(path.join(source, '*.nii'))

def read_niftis(file_list):
    data0 = load_image(file_list[0]).get_data()

    x, y, z = data0.shape
    print 'Found %d files with data shape is %r' % (len(file_list), data0.shape)
    n = len(file_list)

    data = np.zeros((n, x, y, z))

    for i, f in enumerate(file_list):
        print 'Loading subject from file: %s' % f

        nifti = load_image(f)
        subject_data = nifti.get_data()

        if subject_data.shape != (x, y, z):
            raise ValueError('Shape mismatch')
        data[i] = subject_data

    return data

def save_mask(data, out_path):

    print 'Getting mask'

    n, x, y, z = data.shape
    mask = np.zeros((x, y, z))

    zero_freq = (data.reshape((n, x * y * z)) == 0).sum(1) * 1. / reduce(
        lambda x_, y_: x_ * y_, data.shape[1:])

    for freq in zero_freq:
        assert isinstance(freq, float), freq
        if abs(zero_freq.mean() - freq) > .05:
            raise ValueError("Spurious datapoint, mean zeros frequency is"
                             "%.2f, datapoint is %.2f"
                             % (zero_freq.mean(), freq))

    mask[np.where(np.invert((data < 0.07).sum(0) >
        .01 * data.shape[0]))] = 1

    print 'Masked out %d out of %d voxels' % ((mask == 0).sum(), reduce(
        lambda x_, y_: x_ * y_, mask.shape))

    np.save(out_path, mask)

def load_niftis(source_dir, out_dir, name='mri', patterns=None):
    '''
    Loads niftis from a directory.
    '''

    if patterns is not None:
        file_lists = []
        for i, pattern in enumerate(patterns):
            file_list = glob(path.join(source_dir, pattern))
            print('Found %r' % file_list)
            file_lists.append(file_list)
    else:
        file_lists = [find_niftis(source_dir)]
        print 'Found files: %r' % file_lists[0]

    datas = []
    for i, file_list in enumerate(file_lists):
        data = read_niftis(file_list)
        datas.append(data)
        np.save(path.join(out_dir, name + '_%d.npy' % i), data)

    mask = save_mask(np.concatenate(datas, axis=0), path.join(out_dir, name + '_mask.npy'))

def make_argument_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('source',
                        help='source directory for all subjects.')
    parser.add_argument('out_path',
                        help='output directory under args.out_prefix')
    parser.add_argument('-n', '--name', default='mri')
    parser.add_argument('-p', '--patterns', nargs='+', default=None)

    return parser

if __name__ == '__main__':

    parser = make_argument_parser()
    args = parser.parse_args()

    source_dir = path.abspath(args.source)
    out_dir = path.abspath(args.out_path)

    if not path.isdir(out_dir):
        raise ValueError('No output directory found (%s)' % out_dir)

    load_niftis(source_dir, out_dir, args.name, patterns=args.patterns)
