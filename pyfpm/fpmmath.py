#!/usr/bin/python
# -*- coding: utf-8 -*-
""" File fpmmath.py

Last update: 28/10/2016

Usage:

"""
__version__ = "1.1.1"
__author__ = 'Juan M. Bujjamer'
__all__ = ['image_center', 'generate_pupil', 'fpm_reconstruct', 'calculate_pupil_radius', 'adjust_shutter_speed',
           'pixel_size_required', 'crop_image']

from io import BytesIO
from io import StringIO
import time
import yaml

import numpy as np
from numpy.fft import fft2, ifft2, fftshift, ifftshift
from scipy.optimize import fsolve
from PIL import Image
from scipy import ndimage
import random

import pyfpm.coordtrans as ct



def image_center(image_size=None):
    """ Center coordinates given the image size.

    Args:
        image_size (list): list with the image sizes

    Returns:
        (int): integers with each dimension's mean size
    """
    if image_size is not None:
        yc, xc = np.array(image_size)/2
    return int(xc), int(yc)

def resize_complex_image(im_array, final_shape):
    """ Complex image array resized to a final shape

    Args:

    Returns:
        (complex array)
    """
    scale_factor = max(float(final_shape[0])/np.shape(im_array)[0],
                       float(final_shape[1])/np.shape(im_array)[1])
    real_part = ndimage.zoom(np.real(im_array), scale_factor, order=0)
    im_part = ndimage.zoom(np.imag(im_array), scale_factor, order=0)
    rescaled_image = real_part+1j*im_part
    return rescaled_image

def calculate_max_phi(wavelength, pixel_size, na):
    """ The maximum phi allowed by the given configuration.
    """
    phi_max = np.arcsin(wavelength/(2*pixel_size)-na)
    phi_max = np.degrees(phi_max)
    return phi_max


def ps_required(phi_max=None, wavelength=None, na=None):
    """ The pixel size that would be required for a given maximum zenithal angle.

    Args:
        phi_max (float): The maximum zenithal sampled angle.
        wavelength (float): The wavelength of illumination.
        na (float): The numerical aperture of the optical system.

    Returns:
        (float): pixel size required (in the same units as input wavelength)
    """
    if phi_max is not None:
        phi_max_rad = np.radians(phi_max)
    if wavelength is not None:
        wavelength = float(wavelength)
    if na is not None:
        na = float(na)
    return wavelength/(np.sin(phi_max_rad)+na)/2


def test_similarity(image_ref, image_cmp):
    """ A measurement of the similarity between two images.
    """
    ref_mean = np.mean(image_ref)
    cmp_mean = np.mean(image_cmp)
    correction_factor = image_cmp/image_ref
    return

def calculate_pupil_radius(na, npx, pixel_size, wavelength):
    """ pupil radius from wavelength, numerical aperture, pixel size and
        magnification.

    Args:
        cfg (named tuple): tuple with the whole bunch of information.

    Returns:
        (int): pupil radius in pixels, relative to the image size.
    """
    pixel_radius = na*npx*pixel_size/float(wavelength)
    return int(pixel_radius)


def pupil_image(cx=None, cy=None, pup_rad=None, image_size=None):
    """ An array with a circular pupil with a defined center.

        Parameters:
            theta:   angle in degrees on the plane parallel to the sample plane
            phi:    angle in degrees perpendicular t othe sample plane
            power:  power of the leds used by imaging
    """
    pup_matrix = np.zeros(image_size, dtype=np.uint8)
    nx, ny = image_size
    # Coherent pupil generation
    xx, yy = np.meshgrid(range(ny), range(nx))
    c = (xx-cx)**2+(yy-cy)**2
    image_gray = [c < pup_rad**2][0]
    #     # focus test
    #     z = 10e-6;
    #     kzm = sqrt(k0^2-kxm.^2-kym.^2);
    #     pupil = exp(1i.*z.*real(kzm)).*exp(-abs(z).*abs(imag(kzm)));
    #     aberratedCTF = pupil.*CTF;
    # defocus = np.exp(-1j*ot.annular_zernike(4, 2, 0, np.sqrt(c)/pup_rad ))
    # # print(np.max(image_gray*np.sqrt((c-xx)**2+(c-yy)**2) ))
    # image_gray = 1.*image_gray + image_gray*defocus
    return image_gray

# def generate_pupil(theta=None, phi=None, image_size=None,
#                    wavelength=None, pixel_size=None, na=None):
#     """ Pupil center in cartesian coordinates.
#
#     Args:
#         theta (int):      azimuthal angle
#         phi (int):        zenithal angle
#         image_size(list): size of the image of the pupil
#
#     Return:
#         (array) image of the pupil
#     """
#     if image_size is not None:
#         npx = image_size[0]  # Half image size  each side
#     if theta is not None:
#         theta_rad = np.radians(theta)
#     if phi is not None:
#         phi_rad = np.radians(phi)
#     if wavelength is not None:
#         wavelength = float(wavelength)
#     if pixel_size is not None:
#         pixel_size = float(pixel_size)
#     if na is not None:
#         na = float(na)
#     phi_max = np.arcsin(wavelength/(2*pixel_size)-na)
#     if phi_rad > phi_max:
#         print("Zenithal angle has come to a limit, consider to extend the image size.")
#         return None
#         # return np.zeros(image_size, dtype=np.uint8)
#     pupil_radius = calculate_pupil_radius(na, npx, pixel_size, wavelength)
#     coords = np.array([np.sin(phi_rad)*np.cos(theta_rad), np.sin(phi_rad)*np.sin(theta_rad)])
#     [fx, fy] = (1/wavelength)*coords*(pixel_size*npx)
#     xc, yc = image_center(image_size)
#     image_gray = pupil_image(xc+fx, yc+fy, pupil_radius, image_size)
#     return image_gray

# def generate_pupil(theta=None, phi=None, image_size=None,
#                    wavelength=None, pixel_size=None, na=None):
#     """ Pupil center in cartesian coordinates.
#
#     Args:
#         theta (int):      azimuthal angle
#         phi (int):        zenithal angle
#         image_size(list): size of the image of the pupil
#
#     Return:
#         (array) image of the pupil
#     """
#     if image_size is not None:
#         npx = image_size[0]  # Half image size  each side
#     if theta is not None:
#         theta_rad = np.radians(theta)
#     if phi is not None:
#         phi_rad = np.radians(phi)
#     if wavelength is not None:
#         wavelength = float(wavelength)
#     if pixel_size is not None:
#         pixel_size = float(pixel_size)
#     if na is not None:
#         na = float(na)
#         # return np.zeros(image_size, dtype=np.uint8)
#     pupil_radius = calculate_pupil_radius(na, npx, pixel_size, wavelength)
#     coords = np.array([np.sin(phi_rad)*np.cos(theta_rad), np.sin(phi_rad)*np.sin(theta_rad)])
#     [fx, fy] = (1/wavelength)*coords*(pixel_size*npx)
#     xc, yc = image_center(image_size)
#     image_gray = pupil_image(xc+fx, yc+fy, pupil_radius, image_size)
#     return image_gray

def generate_pupil(fx=None, fy=None, image_size=None,
                   pupil_radius=None):
    """ Pupil center in cartesian coordinates.

    Args:
        theta (int):      azimuthal angle
        phi (int):        zenithal angle
        image_size(list): size of the image of the pupil

    Return:
        (array) image of the pupil
    """
    if image_size is not None:
        npx = image_size[0]  # Half image size  each side
    if pupil_radius is not None:
        pupil_radius = float(pupil_radius)
        # return np.zeros(image_size, dtype=np.uint8)
    xc, yc = image_center(image_size)
    image_gray = pupil_image(xc+fx, yc+fy, pupil_radius, image_size)
    return image_gray

def filter_by_pupil_simulate(im_array, theta, phi, lrsize,
                             pupil_radius, kdsc):
    """ Filtered image by a pupil calculated using generate_pupil
    """
    if im_array is not None:
        npx = im_array.shape[0]  # Half image size  each side
    if theta is not None:
        theta_rad = np.radians(theta)
    if phi is not None:
        phi_rad = np.radians(phi)

    # calculares low res image size
    xc, yc = image_center(im_array.shape)
    factor = (lrsize/im_array.shape[0])**2

    [kx, ky] = ct.angles_to_k(theta, phi, kdsc)
    # coords = np.array([np.sin(phi_rad)*np.cos(theta_rad),
    #                    np.sin(phi_rad)*np.sin(theta_rad)])
    #[kx, ky] = (1/wavelength)*coords*(pixel_size*npx)
    # [kx, ky] = coords*kdsc

    pupil = generate_pupil(0, 0, [lrsize-1, lrsize-1], pupil_radius)
    f_ih_shift = fftshift(fft2(im_array))
    kyl = int(np.round(yc+ky-(lrsize)/2))
    kyh = kyl + lrsize - 1
    kxl = int(np.round(xc+kx-(lrsize)/2))
    kxh = kxl + lrsize - 1
    # print(im_array.shape, pupil_radius, kyl, kyh, kxl, kxh)
    f_ih_shift = f_ih_shift[kyl:kyh, kxl:kxh]
    # Step 2: lr of the estimated image using the known pupil
    proc_array = pupil * f_ih_shift  # space pupil * fourier im
    proc_array = ifft2(ifftshift(proc_array))
    # proc_array = resize_complex_image(proc_array, original_shape)
    # proc_array = np.abs(proc_array*np.conj(proc_array))
    return proc_array

def filter_by_pupil(im_array, theta, phi, power, cfg):
    """ Filtered image by a pupil calculated using generate_pupil
    """
    phi_max = cfg.phi[1]
    wavelength = cfg.wavelength
    na = float(cfg.na)
    ps_req = ps_required(phi_max, wavelength, na)
    original_shape = np.shape(im_array)
    scale_factor = cfg.pixel_size/ps_req
    processing_shape = np.array(original_shape)*scale_factor
    processing_shape = processing_shape.astype(int)
    im_array = resize_complex_image(im_array, processing_shape)
    pupil = generate_pupil(theta, phi, power, processing_shape,
                           wavelength, ps_req, na)
    if pupil is None:
        print("Invalid pupil.")
        return None
    # objectAmplitude = np.sqrt(im_array)
    f_ih = fft2(im_array)
    # Step 2: lr of the estimated image using the known pupil
    shifted_pupil = fftshift(pupil)
    proc_array = shifted_pupil * f_ih  # space pupil * fourier im
    proc_array = ifft2(proc_array)
    proc_array = resize_complex_image(proc_array, original_shape)
    proc_array = np.real(proc_array*np.conj(proc_array))
    return proc_array

def show_filtered_image(self, image, theta, phi, power, pup_rad):
    """ Image in bytearray format to use with the flask response function
    """
    img = self.filter_by_pupil(image, theta, phi, power, pup_rad)
    img = Image.fromarray(np.uint8((proc_array)*255))
    with BytesIO() as output:
        img.save(output, 'png')
        proc_image = output.getvalue()
    return bytearray(proc_image)


def show_pupil(theta, phi, power, pup_rad):
    pup_matrix = generate_pupil(theta, phi, power, pup_rad)
    # Converts the image to 8 bit png and stores it into ram
    img = Image.fromarray(pup_matrix*255, 'L')
    with BytesIO() as output:
        img.save(output, 'png')
        pupil = output.getvalue()
    return pupil


def array_as_image(image_array):
    image_array *= (1.0/image_array.max())
    # Converts the image to 8 bit png and stores it into ram
    img = Image.fromarray(image_array*255, 'L')
    with BytesIO() as output:
        img.save(output, 'png')
        output = output.getvalue()
    return output


def show_image(imtype='original', image=None, theta=0, phi=0,
               power=0, pup_rad=0):
    arg_dict = {'pupil': show_pupil(theta, phi, power, pup_rad),
                'filtered': show_filtered_image(image, theta, phi, power, pup_rad)}
    return bytearray(arg_dict[imtype])


def resample_image(image_array, new_size):
    """ Image resampled to fit the specified dimensions.

    Args:
        (array) The image to be resampled
        (list) The final dimensions
    """
    return np.resize(image_array, new_size)


def crop_image(im_array, image_size, osx, osy):
    return im_array[osx:(osx+image_size[0]), osy:(osy+image_size[1])]


def quality_metric(image_dict, image_lowq, cfg):
    import coordtrans as ct

    iterator = set_iterator(cfg)
    accum = 0
    for index, theta, shift in iterator:
        theta, phi = ct.corrected_coordinates(theta=theta, shift=shift,
                                              cfg=cfg)
        im_i = image_dict[(theta, shift)]
        il_i = filter_by_pupil(image_lowq, theta, phi, 255, cfg)
        accum += np.sqrt(np.mean(im_i))/ \
                 (np.sum(np.abs(np.sqrt(il_i)-np.sqrt(im_i))))
    return accum


def laser_beam_simulation(xx, yy, theta, phi, acqpars, cfg):
    """ Simulates a laser beam on the sample image.

    Args:
        theta (int):      azimuthal angle
        phi (int):        zenithal angle
        acqpars (list):    [iso, shutter_speed, led_power]

    Return:
        (array) image of the pupil
    """
    def phase_on_sample(xx, yy):
        sample_height = .1*np.exp(-(2*(xx-cx)**2 + (yy-cy)**2)/rad**2)/(rad**2)-.1
        sample_height[sample_height < 0] = 0
        sample_height[sample_height > 0] += .1
        return sample_height

    # Plane beam
    t, p = np.radians(theta), np.radians(phi)
    k_mod = 2.*np.pi/float(cfg.wavelength)
    kx, ky = np.array([np.sin(p)*np.cos(t), np.sin(p)*np.sin(t)])*k_mod
    lb_phase = np.exp(1j*xx*kx+1j*yy*ky)
    lb = 1.*lb_phase
    return lb



def simulate_sample(cfg):
    """ Returns 2D meshes with physical information about the sample and its
    coordinates. Simulates some shapes and generates their height, refractive
    index and absorption coefficient. It is hardcoded at maximum.
    Args:

    """
    nx, ny = cfg.simulation_size
    wlen = float(cfg.wavelength)
    """Test surf on regularly spaced co-ordinates like MayaVi."""
    xx, yy = np.mgrid[-1.:1:nx*1j, -1.:1:ny*1j]*1E-3
    def sample_height(xx, yy, cx, cy, rad):
        sample_height = .05*np.exp(-(2*(xx-cx)**2 + (yy-cy)**2)/rad**2)/(rad**2)-.1
        sample_height[sample_height < 0] = 0
        sample_height[sample_height > 0] += .1
        return sample_height

    def refraction_index(xx, yy):
        refraction_index = 1.5*np.ones_like((xx, yy))
        return refraction_index

    def transference(xx, yy, cx, cy, rad):
        ref_ind = 1.
        transmittance = 1.
        h0 = 10E-6
        sample_height = h0*np.exp(-((xx-cx)**2 + (yy-cy)**2)/rad**2)-.5*h0
        print(sample_height.min(), sample_height.max())

        sample_height[sample_height < 0] = 0
        # sample_height[sample_height > 0] += h0/2
        phase = np.exp(1j*ref_ind*sample_height*2*np.pi/wlen)
        print(ref_ind*sample_height.max()*2*np.pi, sample_height.max())
        return phase*transmittance

    sample_transference = transference(xx, yy, 0, 0, 1E-3)
#     h += height(xx, yy, .1, .2, .5)
    return xx, yy, sample_transference


def simulate_acquisition(theta, phi, acqpars):
    """
    """
    return

def generate_il(im_array, f_ih, theta, phi, power, image_size,
                wavelength, pixel_size, na):
    pupil = generate_pupil(theta, phi, power, image_size, wavelength,
                           pixel_size, na)
    pupil_shift = fftshift(pupil)
    # Step 2: lr of the estimated image using the known pupil
    f_il = ifft2(f_ih*pupil_shift)  # space pupil * fourier image
    Phl = np.angle(f_il)
    Expl = np.exp(1j*Phl)
    # Step 3: spectral pupil area replacement
    # OBS: OPTIMIZE
    Im = np.resize(im_array, image_size)
    Im_sq = np.sqrt(Im)
    # Il_sq update in the pupil area using Im_sq
    # Step 3 (cont.): Fourier space hr image update
    Il = Im_sq * Expl  # Spacial update
    return Il, Im


def fpm_reconstruct(input_file,  iterator, cfg=None, debug=False):
    """ FPM reconstructon from pupil images

        Parameters:
            input_file:     the sample images dictionary
            blank_images:   images taken on the same positions as the sample images
    """
    image_dict = np.load(input_file)[()]
    image_size = cfg.video_size
    n_iter = cfg.n_iter
    pc = PlatformCoordinates(theta=0, phi=0, height=cfg.sample_height, cfg=cfg)

    # Getting the maximum angle by the given configuration
    # Step 1: initial estimation
    phi_max = cfg.phi[1]
    wavelength = cfg.wavelength
    na = cfg.objective_na
    ps_required = pixel_size_required(phi_max, wavelength, na)
    scale_factor = cfg.pixel_size/ps_required
    Ih = ndimage.zoom(np.ones(image_size), scale_factor, order=0) # HR image
    hr_shape = np.shape(Ih)
    # Ih_sq = 0.5 * np.ones(image_size)  # Constant amplitude
    Ih_sq = 0.5 * Ih

    # Ih_sq = np.sqrt(image_dict[(0, 0)])
    Ph = np.ones_like(Ih_sq)  # and null phase
    Ih = Ih_sq * np.exp(1j*Ph)
    f_ih = fft2(Ih)  # unshifted transform, shift is applied to the pupil
    if debug:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(25, 15))
        fig.show()
        # fig, axes = implot.init_plot(4)
    # Steps 2-5
    for iteration in range(n_iter):
        iterator = set_iterator(cfg)
        print('Iteration n. %d' % iteration)
        # Patching for testing
        for index, theta, phi in iterator:
            # Final step: squared inverse fft for visualization
            im_array = image_dict[(theta, phi)]
            pc.set_coordinates(theta, phi, units='degrees')
            [theta_plat, phi_plat, shift_plat, power] = pc.parameters_to_platform()
            # print("Mean intensity", np.mean(im_array), phi)
            # im_array = (im_array-.1*blank_array)
            # im_array -= np.min(im_array[:])
            im_array[im_array < np.min(im_array)+2] = 1
            im_array = crop_image(im_array, image_size, 180, 265)*255./(power)
            #
            Il, Im = generate_il(im_array, f_ih, theta, phi, power, image_size,
                                cfg.wavelength, cfg.pixel_size, cfg.objective_na)
            # for phi in np.arange(phi-5,phi+5,1):
            #     Il, Im = generate_il(im_array, f_ih, theta, phi, power, pupil_radius,
            #                        image_size)
            #     print("Testing quality metric", quality_metric(image_dict, Il, cfg), phi)
            pupil = generate_pupil(theta, phi, power, image_size, cfg.wavelength,
                                   cfg.pixel_size, cfg.objective_na)
            pupil_shift = fftshift(pupil)
            f_il = fft2(Il)
            f_ih = f_il*pupil_shift + f_ih*(1 - pupil_shift)
            if debug and index % 1 == 0:
                fft_rec = np.log10(np.abs(f_ih)+1)
                fft_rec *= (1.0/fft_rec.max())
                fft_rec = fftshift(fft_rec)
                fft_rec = Image.fromarray(np.uint8(fft_rec*255), 'L')
                im_rec = np.power(np.abs(ifft2(f_ih)), 2)
                im_rec *= (1.0/im_rec.max())
                def plot_image(ax, image):
                    ax.cla()
                    ax.imshow(image, cmap=plt.get_cmap('gray'))
                ax = iter([ax1, ax2, ax3, ax4])
                for image in [pupil, im_rec, Im]:
                    plot_image(ax.next(), image)
                fig.canvas.draw()
                # image_plotter.update_plot([pupil, im_rec, Im, np.angle(ifft2(f_ih))])
                # implot.update_plot([pupil, im_rec, Im, np.angle(ifft2(f_ih))], fig, axes)
        # print("Testing quality metric", quality_metric(image_dict, Il, cfg, max_phi))
    return np.abs(np.power(ifft2(f_ih), 2))
