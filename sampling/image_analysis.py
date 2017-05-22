#!/usr/bin/python
# -*- coding: utf-8 -*-
""" File acquire_complete_set.py

Last update: 28/10/2016
Use to locally simulate FPM.

Usage:

"""
from StringIO import StringIO
import time

import numpy as np
import itertools as it
import pygame
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy import misc
from skimage import measure
import h5py

import pyfpm.fpmmath as fpm
from pyfpm import web
from pyfpm.fpmmath import set_iterator
import pyfpm.data as dt
from pyfpm.coordinates import PlatformCoordinates

# Simulation parameters
images, comp_cfg = dt.open_sampled('2017-05-22_172249.npy')
blank_images, comp_cfg = dt.open_sampled('2017-05-22_172249_blank.npy')

cfg = dt.load_config()
out_file = dt.generate_out_file(cfg.output_sample)
# Connect to a web client running serve_microscope.py
client = web.Client(cfg.server_ip)
pc = PlatformCoordinates(cfg=cfg)
pc.generate_model(cfg.plat_model)
iterator = set_iterator(cfg)

# Start analysis
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(25, 15))
plt.grid(False)
fig.show()

image_dict = dict()
iterator = fpm.set_iterator(cfg)
corr_ims = list()

for index, theta, shift in iterator:
    print(theta, shift)
    im_array = images[(theta, shift)]
    bkim_array = blank_images[(theta, shift)]
    corr_ims.append(im_array - bkim_array)
    # ax1.cla(), ax2.cla()
    # # im_array = acquire_image(pc, client, 0, 0, 0, 0)
    # ax1.imshow(im_array, cmap=cm.hot)
    # ax2.imshow(im_array - bkim_array, cmap=cm.hot)
    # fig.canvas.draw()
ax1.imshow(np.mean(corr_ims,  axis=0))
fig.canvas.draw()
plt.show()
