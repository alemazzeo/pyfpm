#!/usr/bin/python
# -*- coding: utf-8 -*-
""" File simulate.py

Last update: 28/10/2016
Use to locally simulate FPM.

Usage:

"""
import time

import matplotlib.pyplot as plt
import numpy as np

import pyfpm.local as local
from pyfpm.fpmmath import set_iterator, recontruct, itertest
from pyfpm.data import json_savemeta, json_loadmeta
import pyfpm.data as dt

from scipy import misc
from StringIO import StringIO

# Simulation parameters
CONFIG_FILE = 'config.yaml'
cfg = dt.load_config(CONFIG_FILE)

input_image = cfg.input_mag
out_file = cfg.output_sim
json_file = './output_sim/out.json'
# Obs: pup_rad = nx*NA/n where n is the refraction index of the medium
# ns = 0.3  # Complement of the overlap between sampling pupils
# Simulation parameters
image_size = cfg.video_size
wavelength = cfg.wavelength
pixelsize = cfg.pixelsize  # See jupyter notebook
phi_min, phi_max, phi_step = cfg.phi
theta_min, theta_max, theta_step = cfg.theta
pupil_radius = cfg.pupil_size/2
image_dict = {}
mode = cfg.task
itertype = cfg.sweep

# Opens input image as if it was sampled at pupil_pos = (0,0) with high
# resolution details
client = local.SimClient(cfg=cfg)
iterator = set_iterator(cfg)

task = 'acquire'
if task is 'acquire':
    json_savemeta(json_file, image_size, pupil_radius, theta_min, theta_max,
                  theta_step, phi_min, phi_max, wavelength, pixelsize,
                  mode, itertype)
    for index, theta, phi, power in iterator:
        print(index, theta, phi, power)
        image_dict[(theta, phi)] = client.acquire(theta, phi, power)
    np.save(out_file, image_dict)

    start_time = time.time()
    data = json_loadmeta(json_file)
    rec = recontruct(out_file, iterator, cfg=cfg, debug=True)
    print('--- %s seconds ---' % (time.time() - start_time))
    plt.imshow(rec), plt.gray()
    plt.show()

elif task is 'reconstruct':
    start_time = time.time()
    data = json_loadmeta(json_file)
    rec = recontruct(out_file, iterator, cfg=cfg, debug=True)
    print('--- %s seconds ---' % (time.time() - start_time))
    plt.imshow(rec), plt.gray()
    plt.show()

if task is 'test_and_measure':
    image_dict = np.load(out_file)
    for index, theta, phi, power in iterator:
        if phi == 20 or phi == 40:
            im_array = image_dict[()][(theta, phi)]
            intensity = np.mean(im_array)
            print('int: %f, theta: %d, phi: %d' % (intensity, theta, phi))
            ax = plt.gca() or plt
            ax.imshow(im_array, cmap=plt.get_cmap('gray'))
            ax.get_figure().canvas.draw()
            plt.show(block=False)

if task is 'other':
    for (index, theta, phi, power) in iterator:
        print(index, theta, phi)
    print([i for i in set_iterator(theta_max=theta_max, phi_max=phi_max,
                            theta_step=theta_step, mode='simulation',
                            itertype='neopixels')])
