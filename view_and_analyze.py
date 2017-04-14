#!/usr/bin/python
# -*- coding: utf-8 -*-
""" File sample.py

Last update: 28/10/2016
To be used as a remote client for a microscope.
Before runing this file make sure there is a server running serve_microscope.py
hosted in some url.

Usage:

"""
from StringIO import StringIO
import time
import os
import datetime

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy import misc, signal
import numpy as np
import time
import yaml

import pyfpm.fpmmath as fpm
from pyfpm.data import save_yaml_metadata
# from pyfpm.data import json_savemeta, json_loadmeta
import pyfpm.data as dt
from pyfpm.coordinates import PlatformCoordinates
from pyfpm import implot
import pyfpm.local as local
# Simulation parameters
CONFIG_FILE = 'config.yaml'
cfg = dt.load_config(CONFIG_FILE)
simclient = local.SimClient(cfg=cfg)
pc = PlatformCoordinates(theta=0, phi=0, height=cfg.sample_height, cfg=cfg)

in_file = os.path.join(cfg.output_sample, '2017-04-05_113601.npy')
iterator = fpm.set_iterator(cfg)

image_dict = np.load(in_file)[()]
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(25, 15))
plt.grid(False)
fig.show()
cum_corr = 0

for index, theta, phi in iterator:
    # Coordinates math
    # time.sleep(0.5)
    pc.platform_tilt = [0, 2]
    pc.source_center = [0, 3] #[xcoord, ycoord] of the calibrated center
    pc.set_coordinates(theta=theta, phi=phi, units='degrees')
    t_corr, p_corr = pc.source_coordinates(mode='angular')
    theta_sim_offset = 20
    #####################################################################
    power = 100
    sim_im_array = simclient.acquire(t_corr+theta_sim_offset, p_corr, power)
    im_array = image_dict[(theta, phi)]
    im_array = fpm.crop_image(im_array, cfg.video_size, 170, 245)
    # im_array = sim_im_array
    # sim_im_array /= np.mean(sim_im_array)
    # im_array /= np.mean(im_array)

    corr = signal.correlate2d(im_array[40:110, 40:110], sim_im_array[40:110, 40:110], mode='same', boundary='fill', fillvalue=0)
    # corr /= (np.sum(im_array+sim_im_array))
    cum_corr += np.sum(corr)
    print(cum_corr, np.log10(cum_corr))
    if theta == 20 or theta == 340:
        print("Cummulative in circle", cum_corr, np.log10(cum_corr))
    # Showing the images
    ax1.cla(), ax2.cla(), ax3.cla()
    ax1.imshow(im_array, cmap=cm.hot)
    ax1.annotate('Mean value: %.4f \nPHI: %.1f THETA: %.1f'% (np.max(im_array), phi, theta),
                  xy=(0,0), xytext=(80,20), fontsize=12, color='white')
    ax2.imshow(sim_im_array, cmap=cm.hot)
    ax2.annotate('Mean value: %.4f \nPHI: %.1f THETA: %.1f'% (np.max(sim_im_array), phi, theta),
                 xy=(0,0), xytext=(80,20), fontsize=12, color='white')
    ax3.imshow(corr, cmap=cm.hot, vmin = 0)
    ax3.annotate('Mean value: %.2f \nMax value: %.2f'% (np.mean(corr), np.max(corr)),
                 xy=(0,0), xytext=(40,20), fontsize=12, color='white')

    fig.canvas.draw()

plt.show()
