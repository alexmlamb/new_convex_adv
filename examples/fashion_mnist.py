#import waitGPU
#waitGPU.wait(utilization=20)#, available_memory=11000, interval=10)

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.autograd import Variable

import numpy as np
#import cvxpy as cp

import torchvision.transforms as transforms
import torchvision.datasets as datasets

#import setproctitle
import argparse

import problems as pblm
from trainer import *

if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch_size', type=int, default=20)
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--epsilon", type=float, default=0.1)
    parser.add_argument("--starting_epsilon", type=float, default=None)
    parser.add_argument('--prefix')
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--verbose', type=int, default='1')
    parser.add_argument('--alpha_grad', action='store_true')
    parser.add_argument('--scatter_grad', action='store_true')
    parser.add_argument('--l1_proj', type=int, default=None)
    parser.add_argument('--large', action='store_true')
    parser.add_argument('--vgg', action='store_true')
    args = parser.parse_args()
    args.prefix = args.prefix or 'fashion_mnist_conv_{:.4f}_{:.4f}_0'.format(args.epsilon, args.lr).replace(".","_")
    #setproctitle.setproctitle(args.prefix)

    train_log = open(args.prefix + "_train.log", "w")
    test_log = open(args.prefix + "_test.log", "w")

    train_loader, _ = pblm.fashion_mnist_loaders(args.batch_size)
    _, test_loader = pblm.fashion_mnist_loaders(2)

    torch.manual_seed(args.seed)
    torch.cuda.manual_seed(args.seed)

    if args.large: 
        model = pblm.mnist_model_large().cuda()
    elif args.vgg: 
        model = pblm.mnist_model_vgg().cuda()
    else: 
        model = pblm.mnist_model().cuda()

    opt = optim.Adam(model.parameters(), lr=args.lr)

    for t in range(args.epochs):
        if t <= args.epochs//2 and args.starting_epsilon is not None: 
            epsilon = args.starting_epsilon + (t/(args.epochs//2))*(args.epsilon - args.starting_epsilon)
        else: 
            epsilon = args.epsilon
        train_robust(train_loader, model, opt, epsilon, t, train_log, 
            args.verbose, 
            args.alpha_grad, args.scatter_grad, l1_proj=args.l1_proj)
        evaluate_robust(test_loader, model, args.epsilon, t, test_log, args.verbose)
        torch.save(model.state_dict(), args.prefix + "_model.pth")
