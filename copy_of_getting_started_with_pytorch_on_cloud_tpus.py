# -*- coding: utf-8 -*-
"""Copy of Getting Started with PyTorch on Cloud TPUs

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1cjqwlcFMeYCkz4pmykSWKNJyvFD78xqb

## Getting Started with PyTorch on Cloud TPUs

This notebook will show you how to:

* Install PyTorch/XLA on Colab, which lets you use PyTorch with TPUs.
* Run basic PyTorch functions on TPUs, like creating and adding tensors.
* Run PyTorch modules and autograd on TPUs.
* Run PyTorch networks on TPUs.

PyTorch/XLA is a package that lets PyTorch connect to Cloud TPUs and use TPU cores as devices. Colab provides a free Cloud TPU system (a remote CPU host + four TPU chips with two cores each) and installing PyTorch/XLA only takes a couple minutes. 

Even though Colab offers eight TPU cores, this notebook only uses one for simplicity. More information about running PyTorch on TPUs can be found on [PyTorch.org](http://pytorch.org/xla/), including how to run PyTorch networks on multiple TPU cores simultaneously. Other Colab notebooks also show how to use multiple TPU cores, including [this one](https://colab.research.google.com/github/pytorch/xla/blob/master/contrib/colab/mnist-training.ipynb#scrollTo=Afwo4H7kSd8P) which trains a network on the MNIST dataset and [this one](https://colab.research.google.com/github/pytorch/xla/blob/master/contrib/colab/resnet18-training.ipynb#scrollTo=_2nL4HmloEyl) which trains a ResNet18 architecture on CIFAR10. 

These and other Colab notebooks, as well as Google Cloud Platform (GCP) tutorials, can be found [here](https://github.com/pytorch/xla/tree/master/contrib/colab). Check out our [NeurIPS 2019 Fast Neural Style Transfer demo](https://colab.research.google.com/github/pytorch/xla/blob/master/contrib/colab/style_transfer_inference.ipynb#scrollTo=EozMXwIV9iOJ), where you can apply different styles (filters) to your own images!

To use PyTorch on Cloud TPUs in your own Colab notebook you can copy this one, or copy the setup cell below and configure your Colab environment to use TPUs. 

Finally, this notebook is intended for people already familiar with PyTorch, a popular open-source deep learning framework. If you haven't used PyTorch before you might want to review the tutorials at https://pytorch.org/ before continuing.

<h3>  &nbsp;&nbsp;Use Colab Cloud TPU&nbsp;&nbsp; <a href="https://cloud.google.com/tpu/"><img valign="middle" src="https://raw.githubusercontent.com/GoogleCloudPlatform/tensorflow-without-a-phd/master/tensorflow-rl-pong/images/tpu-hexagon.png" width="50"></a></h3>

* On the main menu, click Runtime and select **Change runtime type**. Set "TPU" as the hardware accelerator.
* The cell below makes sure you have access to a TPU on Colab.
"""

#import os
#assert os.environ['COLAB_TPU_ADDR'], 'Make sure to select TPU from Edit > Notebook settings > Hardware accelerator'

"""## Installing PyTorch/XLA

Run the following cell (or copy it into your own notebook!) to install PyTorch, Torchvision, and PyTorch/XLA. It will take a couple minutes to run.

The PyTorch/XLA package lets PyTorch connect to Cloud TPUs. (It's named PyTorch/XLA, not PyTorch/TPU, because XLA is the name of the TPU compiler.) In particular, PyTorch/XLA makes TPU cores available as PyTorch devices. This lets PyTorch create and manipulate tensors on TPUs.
"""

VERSION = "20200325"  #@param ["1.5" , "20200325", "nightly"]

"""## Creating and Manipulating Tensors on TPUs

PyTorch uses Cloud TPUs just like it uses CPU or CUDA devices, as the next few cells will show. Each core of a Cloud TPU is treated as a different PyTorch  device.
"""

# imports pytorch
#import torch

# imports the torch_xla package
#import torch_xla
#import torch_xla.core.xla_model as xm

from skimage.transform import resize
import json, os, pickle, matplotlib.pyplot as plt, numpy as np, pandas as pd
import torch, torchvision, torch.nn as nn, torch.optim as optim

from tqdm import tqdm_notebook as tqdm
from random import randint
from sklearn.model_selection import train_test_split
from imageio import imread
from collections import Counter
from imageio import imread
from PIL import Image
from torch.utils.data import TensorDataset, Dataset, DataLoader
from torch.utils.data._utils.collate import default_collate
from torchvision import models, transforms
from sklearn.metrics import roc_auc_score
from math import floor, sqrt
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
import atexit
import traceback
@atexit.register
def goodbye():
    traceback.print_exc()


chexpert = pd.read_csv('mimic-cxr-2.0.0-chexpert.csv', index_col='study_id')

###############

split = pd.read_csv('mimic-cxr-2.0.0-split.csv', index_col='study_id')

negbio = pd.read_csv('mimic-cxr-2.0.0-negbio.csv', index_col='study_id')

metadata = pd.read_csv('mimic-cxr-2.0.0-metadata.csv', index_col='study_id')

recordlist = pd.read_csv('cxr-record-list.csv')
studylist = pd.read_csv('cxr-study-list.csv')

paOnly = metadata[metadata['ViewPosition']=='AP']
paOnlyRL = paOnly.set_index('dicom_id').join(recordlist.set_index('dicom_id'), lsuffix='', rsuffix='_rl')
rlsplit = paOnlyRL.join(split.set_index('dicom_id'), lsuffix='',rsuffix='_split')
rlsplit = rlsplit.set_index('study_id').join(chexpert, lsuffix='_l', rsuffix='_r')
pn = rlsplit[rlsplit['Pneumothorax'].notnull()]

rlsplit=pn

print(split['split'].value_counts())
print(rlsplit['split'].value_counts())
print(rlsplit['Pneumothorax'].value_counts())

trainset = rlsplit[rlsplit['split']=='train']
testset = rlsplit[rlsplit['split']=='test']
validset = rlsplit[rlsplit['split']=='validate']

import os
import torch
import torchvision.transforms as transforms
import torchvision.datasets as dset
import torch.utils.data as data

normalize_transform = transforms.Compose([transforms.ToTensor(),
                                              transforms.Normalize((0.485, 0.456, 0.406),
                                                                   (0.229, 0.224, 0.225))])
#normalize_transform = transforms.Compose([transforms.ToTensor(),
#                                              transforms.Normalize((0.485),
#                                                                   (0.229))])
train_large_transform = transforms.Compose([transforms.RandomResizedCrop(224),
                                                transforms.RandomHorizontalFlip()])
val_large_transform = transforms.Compose([transforms.Resize(256),
                                              transforms.CenterCrop(224)])
train_small_transform = transforms.Compose([transforms.Pad(4),
                                                transforms.RandomCrop(32),
                                                transforms.RandomHorizontalFlip()])

train_transform = transforms.Compose([train_large_transform, normalize_transform])
val_transform = transforms.Compose([val_large_transform, normalize_transform])

import numpy as np

class mimicDataset(torch.utils.data.Dataset):

    def __init__(self, pdframe, root_dir, transform):
        """
        Args:
            text_file(string): path to text file
            root_dir(string): directory with all train images
        """
        self.pdframe = pdframe
        self.root_dir = root_dir
        self.transform = transform

    def __len__(self):
        return len(self.pdframe)

    def __getitem__(self, idx):
        img_name = os.path.join(self.root_dir, self.pdframe.iloc[idx, 11]).replace('.dcm','.jpg')
        image = Image.open(img_name).convert('RGB')
        image = self.transform(image)
        label_raw = self.pdframe.iloc[idx, 27] #.astype(np.float64)
        
        if False: # np.isnan(label_raw):
          label = np.int64(3)
        elif label_raw < 0:
          label = np.int64(2)
        #elif label == 0.:
        #  label = 0
        else:
          label = label_raw.astype(np.int64)
          #print('label', label)
          #assert(False)
        #assert(label>=0 and label < 4)
        return image, label

import sys
sys.path.insert(1, './L2T-ww')

trainset.head()

#prepare dataloader
batchSize = 32 # 128

pdDatasets = [trainset, testset, validset]
pdsts = [
         torch.utils.data.DataLoader(mimicDataset(trainset, root_dir='./data', transform=train_transform), batch_size=batchSize, shuffle=True, num_workers=0),
         torch.utils.data.DataLoader(mimicDataset(testset, root_dir='./data', transform=train_transform), batch_size=batchSize, shuffle=True, num_workers=0),
         torch.utils.data.DataLoader(mimicDataset(validset, root_dir='./data', transform=val_transform), batch_size=batchSize, shuffle=True, num_workers=0),
        ]

import importlib
import train_l2t_ww

import os
os.environ['CUDA_LAUNCH_BLOCKING']='1'


train_l2t_ww.main(mimicLoader=pdsts, arguments=['--num-classes', '3', '--dataroot', 'data', '--wnet-path', 'logs/chpk-1-1800.pth']) # , given_dev=xm.xla_device())
sys.exit(0)
