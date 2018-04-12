#!/usr/bin/python
# -*- coding: utf-8 -*-
""" File reconstruct.py

Last update: 03/03/2017
FPM reconstruction methods. Originally based as an implementation of the
alternating projections (Gerchberg-Saxton) method.

Usage:

"""
import time
import yaml

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
from numpy.fft import fft2, ifft2, fftshift
from PIL import Image
from scipy import ndimage

from pyfpm.coordinates import PlatformCoordinates
import pyfpm.fpmmath as fpmm
from . import coordtrans as ct

# from . import implot
# import fpmmath.optics_tools as ot

def get_mask(samples, backgrounds=None, xoff=None, yoff=None, cfg=None):
    """ Returns a thresholded mask where an imaged object is suspected to be.
    It could be useful in high contrast images where object borders are
    sufficiently well determined.

    Args:
    -----
        samples: the acquired samples as a dictionary with angles as keys.
        backgrounds: the acquired background as a dictionary with angles as
                     keys. They must be acquired right after or before taking
                     the samples.
        xoff: offset in the 'x' direction of this sample's center.
        yoff: offset in the 'y' direction of this sample's center.
        cfg: configuration (named tuple)
    Returns:
    --------
        (ndarray) mask containing the object to be reconstructed.
    """
    corr_ims = list()
    iterator = fpmm.set_iterator(cfg)
    for index, theta, shift in iterator:
        image = samples[(theta, shift)]
        image = fpmm.crop_image(image, cfg.patch_size, xoff, yoff)
        # image, image_size = image_rescaling(image, cfg)
        background = backgrounds[(theta, shift)]
        background = fpmm.crop_image(background, cfg.patch_size, xoff, yoff)
        # background, image_size = image_rescaling(background, cfg)
        corr_ims.append(image_correction(image, background, mode='background'))
    mask = np.mean(corr_ims, axis=0)
    #
    thres = 140 # hardcoded
    mask[mask < thres] = 1
    mask[mask > thres] = 0
    # print(Et[np.abs(Et) > .1])
    return mask


def image_correction(sample, background, mask=None, mode='threshold'):
    """ A set of image correction methods. They use backround sampled images
    or masks to perform the correction.

    Args:
    -----
        sample: the (xpy, npx) image to be corrected.
        background: the (xpy, npx) background corresonding to the sample.
        mask: object mast (see the get_mask() method).
        mode: the method to be applied for correction:
            * threshold: aplies a threshold to the sampled image.
            * background: substracst or corrects background intensity.
            * mask: only corrects inside a mask.

    Returns:
    --------
        (ndarray) upsampled image and final high resolution shape
    """
    if mode == 'threshold':
        image_corrected = sample
    elif mode == 'background':
        # image *= (255.0/image.max())
        # background *= (255.0/background.max())
        image_corrected = sample / background
        # image_corrected *= (255.0/image_corrected.max())
        # image_corrected -= np.min(image_corrected[:])-1
    elif mode == 'mask':
        image_corrected = sample - 1.*background
        image_corrected -= np.min(image_corrected[:])-5
        image_corrected = sample*mask+10
    # im_array = (im_array-.1*blank_array)
    # im_array -= np.min(im_array[:])
    # im_array[im_array < np.min(im_array)+2] = 0
    # image_corrected /= np.max(image_corrected)
    return image_corrected


def image_rescaling(lr_image, cfg):
    """ Image rescaling acording to sampling requirements. The numerical
    aperture, wavelength, pixel size and maximum sampling are used to calculate
    the upsampled image size to contain all the new information.

    Args:
    -----
        image: the (xpy, npx) image to be rescaled
        cfg: configuration (named tuple)

    Returns:
    --------
        (ndarray) upsampled image and final high resolution shape
    """
    phi_max = float(cfg.phi[1])
    wavelength = float(cfg.wavelength)
    na = float(cfg.objective_na)
    ps_required = fpmm.ps_required(phi_max, wavelength, na)
    scale_factor = cfg.pixel_size/ps_required
    Ih = ndimage.zoom(lr_image, scale_factor, order=0)  # HR image
    hr_shape = np.shape(Ih)
    return Ih, hr_shape


def preprocess_images(samples, backgrounds, xoff, yoff, cfg, corr_mode='background'):
    """ Applies a correction method to all the sampled images. Some of the
    methods need backroung images to substract illumination inhomogeneities.

    Args:
    -----
        samples: the acquired samples as a dictionary with angles as keys.
        backgrounds: the acquired background as a dictionary with angles as
                     keys. They must be acquired right after or before taking
                     the samples.
        xoff: offset in the 'x' direction of this sample's center.
        yoff: offset in the 'y' direction of this sample's center.
        cfg: configuration (named tuple)
        corr_mode: the correction method
            * background: substracts  backround from samples.
            * bypass: does nothing (what a wonderful method!)

    Returns:
    --------
        (dictionary) dictionary with teh corrected samples.
    """
    iterator = ct.set_iterator(cfg)
    if corr_mode == 'background':
        for index, theta, shift, aqcpars in iterator:
            sample = fpmm.crop_image(samples[(theta, shift)],
                                     cfg.patch_size, xoff, yoff)
            background = fpmm.crop_image(backgrounds[(theta, shift)],
                                         cfg.patch_size, xoff, yoff)
            im_array = image_correction(sample, background, mode=corr_mode)
            im_array, resc_size = image_rescaling(im_array, cfg)
            samples[(theta, shift)] = im_array
    if corr_mode == 'bypass':
        do_nothing = 1
    return samples


def initialize(samples, backgrounds=None, xoff=None, yoff=None, cfg=None,
               mode='zero'):
    """ Initializes the algorithm using one of various modalities.

    Args:
    -----
        samples: the acquired samples as a dictionary with angles as keys.
        backgrounds: the acquired background as a dictionary with angles as
                     keys. They must be acquired right after or before taking
                     the samples.
        xoff: offset in the 'x' direction of this sample's center.
        yoff: offset in the 'y' direction of this sample's center.
        cfg: configuration (named tuple)
        mode: the modality according to which the algorithm is going to be
        initilized. Can be one of the following options:
            * zero: constant phase and zero amplitude.
            * transmission: the transmitted image at (0, 0) angles.
            * mean: takes all the samples and substracts the (measured)
                    backround. Then takes the mean of all of them.

    Returns:
    --------
        (ndarray) a complex image with the same size of the samples.
    """
    image = fpmm.crop_image(samples[(0, 0)], cfg.patch_size, xoff, yoff)
    image, image_size = image_rescaling(image, cfg)
    if mode == 'zero':
        Ih_sq = 0.5 * np.ones_like(image)  # Homogeneous amplitude
        Ph = np.zeros_like(Ih_sq)          # and null phase
        Et = Ih_sq * np.exp(1j*Ph)
    elif mode == 'transmission':
        background = fpmm.crop_image(backgrounds[(0, 0)], cfg.patch_size, xoff, yoff)
        background, image_size = image_rescaling(background, cfg)
        image = image_correction(image, background, mode='background')
        Ih_sq = np.sqrt(image)
        Ph = np.zeros_like(Ih_sq)  # and null phase
        Et = Ih_sq * np.exp(1j*Ph)
    elif mode == 'mean':
        corr_ims = list()
        iterator = fpmm.set_iterator(cfg)
        for index, theta, shift in iterator:
            # Final step: squared inverse fft for visualization
            image = fpmm.crop_image(samples[(theta, shift)],
                                       cfg.patch_size, xoff, yoff)
            background = fpmm.crop_image(backgrounds[(theta, shift)],
                                         cfg.patch_size, xoff, yoff)
            image, image_size = image_rescaling(image, cfg)
            background, image_size = image_rescaling(background, cfg)
            corr_ims.append(image_correction(image, background, mode='background'))
        Ih = np.mean(corr_ims, axis=0)
        # Ph = 0.5+np.pi*np.abs(Et)/np.max(Et)
        Et = np.sqrt(Ih) * np.exp(1j*0)
    return Et


def generate_il(im_array, f_ih, theta, phi, cfg):
    """ Returns the low resolution sampled image with added reconstructed phase
    in the according spectral position. More detailed explanation:
    Takes the high resolution spectrum, calculates a low resolution sample in
    the spectral area occupied by the sampled image (im_array) by cuting it
    with the pupil at the (theta, phi), takes just the phase information in
    this area and replaces its modulus with the acquired im_array.
    Why this is outside the main function? Because it is also used in the
    quality metric (to be reimpemented here).
    """
    ps = fpmm.ps_required(cfg.phi[1], cfg.wavelength, cfg.na)
    image_size = np.shape(im_array)
    pupil = fpmm.generate_pupil(theta=theta, phi=phi, image_size=image_size,
                                wavelength=cfg.wavelength, pixel_size=ps,
                                na=cfg.na)
    pupil_shift = fftshift(pupil)
    # Step 2: lr of the estimated image using the known pupil
    f_il = ifft2(f_ih*pupil_shift)  # space pupil * fourier image
    Phl = np.angle(f_il)
    # Step 3: spectral pupil area replacement
    Il = np.sqrt(im_array) * np.exp(1j*Phl)  # Spacial update
    Iupdate = Il
    # Iupdate /= np.max(Iupdate)
    # Iupdate *= 150
    return Iupdate

def fpm_reconstruct(samples=None, backgrounds=None, it=None, init_point=None,
                    cfg=None,  debug=False):
    """ FPM reconstructon using the alternating projections algorithm. Here
    the complete samples and (optional) background images are loaded and Then
    cropped according to the patch size set in the configuration tuple (cfg).

    Args:
    -----
        samples: the acquired samples as a dictionary with angles as keys.
        backgrounds: the acquired background as a dictionary with angles as
                     keys. They must be acquired right after or before taking
                     the samples.
        it: iterator with additional sampling information for each sample.
        init_point: [xoff, yoff] center of the patch to be reconstructed.
        cfg: configuration (named tuple)
        debug: set it to 'True' if you want to see the reconstruction proccess
               (it slows down the reconstruction).

    Returns:
    --------
        (ndarray) The reconstructed modulus and phase of the sampled image.
    """
    # pc = PlatformCoordinates(theta=0, phi=0, height=cfg.sample_height, cfg=cfg)
    xoff, yoff = init_point  # Selection of the image patch
    ps_required = fpmm.ps_required(cfg.phi[1], cfg.wavelength, cfg.na)
    # mask = get_mask(samples, backgrounds, xoff, yoff, cfg)
    # Getting the maximum angle by the given configuration
    # Step 1: initial estimation
    Et = initialize(samples, backgrounds, xoff, yoff, cfg, 'zero')
    f_ih = fft2(Et)  # unshifted transform, shift is later applied to the pupil
    if debug:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(25, 15))
        fig.show()
        # fig, axes = implot.init_plot(4)
    # Steps 2-5
    samples = preprocess_images(samples, backgrounds, xoff, yoff, cfg,
                                corr_mode='bypass')
    for iteration in range(cfg.n_iter):
        iterator = ct.set_iterator(cfg)
        print('Iteration n. %d' % iteration)
        # Patching for testing
        # for index, theta, phi, acqpars in iterator:
        for it in iterator:
            index, theta, phi = it['index'], it['theta'], it['phi']
            print(it['theta'], it['phi'], it['indexes'])
            # theta, phi = ct.corrected_coordinates(theta=theta, shift=shift,
            #                                       cfg=cfg)
            # Final step: squared inverse fft for visualization
            im_array = fpmm.crop_image(samples[it['indexes']],
                                        cfg.patch_size, xoff, yoff)
            # background = fpmm.crop_image(backgrounds[(theta, shift)],
            #                              cfg.patch_size, xoff, yoff)
            #
            # im_array = image_correction(im_array, background, mode='background')
            im_array, resc_size = image_rescaling(im_array, cfg)

            Il = generate_il(im_array, f_ih, theta, phi, cfg)
            pupil = fpmm.generate_pupil(theta=theta, phi=phi,
                                        image_size=np.shape(im_array),
                                        wavelength=cfg.wavelength,
                                        pixel_size=ps_required,
                                        na=cfg.objective_na)
            pupil_shift = fftshift(pupil)  # Shifts pupil to match unshifted fft
            f_il = fft2(Il)
            f_ih = f_il*pupil_shift + f_ih*(1 - pupil_shift)
            # If debug mode is on
            if debug and index % 1 == 0:
                fft_rec = np.log10(np.abs(f_ih)+1)
                fft_rec *= (255.0/fft_rec.max())
                fft_rec = fftshift(fft_rec)
                # Il = Image.fromarray(np.uint8(Il), 'L')
                im_rec = ifft2(f_ih)
                im_rec *= (255.0/im_rec.max())
                def plot_image(ax, image, title):
                    ax.cla()
                    ax.imshow(image, cmap=plt.get_cmap('gray'))
                    ax.set_title(title)
                axiter = iter([(ax1, 'Reconstructed FFT'), (ax2, 'Reconstructed magnitude'),
                            (ax3, 'Acquired image'), (ax4, 'Reconstructed phase')])
                for image in [np.abs(fft_rec), np.abs(im_rec), im_array, np.angle(ifft2(f_ih))]:
                    ax, title = next(axiter)
                    plot_image(ax, image, title)
                fig.canvas.draw()
            # print("Testing quality metric", fpmm.quality_metric(samples, Il, cfg))
    return np.abs(np.power(ifft2(f_ih), 2)), np.angle(ifft2(f_ih+1))


def dpc_init(samples=None, backgrounds=None, it=None, init_point=None,
             cfg=None,  debug=False):
    """ Absolutely experimental reconstruction function. Virtually analog to
    fpm_reconstruct() to be used as a test sandbox.
    """
    # pc = PlatformCoordinates(theta=0, phi=0, height=cfg.sample_height, cfg=cfg)
    xoff, yoff = init_point  # Selection of the image patch
    ps_required = fpmm.ps_required(cfg.phi[1], cfg.wavelength, cfg.na)
    # mask = get_mask(samples, backgrounds, xoff, yoff, cfg)
    # Getting the maximum angle by the given configuration
    # Step 1: initial estimation
    Et = initialize(samples, backgrounds, xoff, yoff, cfg, 'zero')
    f_ih = fft2(Et)  # unshifted transform, shift is later applied to the pupil
    if debug:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(25, 15))
        fig.show()
        # fig, axes = implot.init_plot(4)
    # Steps 2-5
    for iteration in range(cfg.n_iter):
        iterator = ct.set_iterator(cfg)
        print('Iteration n. %d' % iteration)
        # Patching for testing
        for index, theta, shift in iterator:
            theta, phi = ct.corrected_coordinates(theta=theta, shift=shift,
                                                  cfg=cfg)
            print(theta, phi)
            # Final step: squared inverse fft for visualization
            im_array = fpmm.crop_image(samples[(theta, shift)],
                                       cfg.patch_size, xoff, yoff)
            background = fpmm.crop_image(backgrounds[(theta, shift)],
                                         cfg.patch_size, xoff, yoff)

            im_array = image_correction(im_array, background, mode='background')
            im_array, resc_size = image_rescaling(im_array, cfg)
            Il = generate_il(im_array, f_ih, theta, phi, cfg)
            #     print("Testing quality metric", quality_metric(image_dict, Il, cfg), phi)
            pupil = fpmm.generate_pupil(theta=theta, phi=phi,
                                        image_size=resc_size, wavelength=cfg.wavelength,
                                        pixel_size=ps_required, na=cfg.objective_na)
            pupil_shift = fftshift(pupil)
            f_il = fft2(Il)
            f_ih = f_il*pupil_shift + f_ih*(1 - pupil_shift)
            if debug and index % 1 == 0:
                fft_rec = np.log10(np.abs(f_ih)+1)
                fft_rec *= (255.0/fft_rec.max())
                fft_rec = fftshift(fft_rec)
                # fft_rec = Image.fromarray(np.uint8(fft_rec*255), 'L')
                im_rec = ifft2(f_ih)
                # im_rec *= (255.0/im_rec.max())
                im_rec_abs = np.sqrt(np.real(im_rec*np.conj(im_rec)))
                def plot_image(ax, image):
                    ax.cla()
                    ax.imshow(image, cmap=plt.get_cmap('hot'))
                ax = iter([ax1, ax2, ax3, ax4])
                for image in [np.abs(fft_rec), im_rec_abs, im_array, np.angle(im_rec)]:
                    plot_image(ax.next(), image)
                fig.canvas.draw()
        # print("Testing quality metric", quality_metric(image_dict, Il, cfg, max_phi))
    return np.abs(np.power(ifft2(f_ih), 2)), np.angle(ifft2(f_ih+1))
