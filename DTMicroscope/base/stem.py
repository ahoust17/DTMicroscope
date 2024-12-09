from DTMicroscope.base.microscope import BaseMicroscope
import SciFiReaders
import pyTEMlib


import pdb
import gdown
import os
import sidpy as sid

# the Autoscript packages --- waiting for Utkarsh
# from autoscript_tem_microscope_client import TemMicroscopeClient
# from autoscript_tem_microscope_client.enumerations import *
# from autoscript_tem_microscope_client.structures import *
# import Pyro5.api

# General packages
import os, time, sys, math, io
import matplotlib.pyplot as plt
import numpy as np


# The DTSTEM and RealSTEM classes should be interchangeable in the notebooks
# Also, we should inherit the BaseMicroscope class eventually, but I'm not sure how compatible the methods are
# Or we should delete the BaseMicroscope class, it doesn't seem to do much at the moment - AH


class DTSTEM():
    def __init__(self, data_mode):
        if data_mode.lower() == 'simulation':
            self.data_mode = 'simulation'
        elif data_mode.lower() == 'preloaded':
            self.data_mode = 'preloaded'
        else:
            raise ValueError('Invalid data_mode. Please choose "simulation" or "preloaded"')


        aberration_dict = None
        probe = self.make_probe()

        self.optics={'mode': 'STEM', # or TEM in the future'aberrations': None,
                     'accelerating_voltage': 200e3, # V
                     'convergence_angle': 30, # mrad
                     'beam_current': 100, # pA
                     'fov': None,
                     'aberrations' : aberration_dict,
                     'probe': None}
        
        self.detectors={'haadf': {'inserted': False},
                        'camera': {'inserted': False},
                        'maadf': {'inserted': False},
                        'bf': {'inserted': False},
                        'flucamera': {'inserted': False,
                                      'screen_current': None,
                                      'exposure_time': None}}
        
#
    #
    def connect(self, ip, port):
        print('Connected to Digital Twin')
        return
    
    def set_field_of_view(self, fov):
        self.optics['fov'] = fov
        return self.optics['fov']

    def get_scanned_image(self, size, dwell_time, detector='haadf'):
        if data_mode == 'preloaded':
            return self.haadf_image

        elif data_mode == 'simulation':
            probe = self.optics['probe']

            if self.fov is None:
                raise ValueError('Field of view not set, run microscope.set_field_of_view()')
            

            probe = self.probe

            if self.fov < 100: # Angstroms, arbitrary for now
                # simulate atomic resolution WS2


            elif self.fov > 1000: # Angstroms, arbitrary for now
                # simulate blobs


            else:
                raise ValueError('Field of view should be < 100 or > 1000 Angstroms')


        
    def make_probe(self):
        abbs = self.optics['aberrations']
        # here we make the probe w gerd's notebook

        return 

    def set_aberrations(self, aberrations):
        if aberrations is not None:
            self.aberrations = aberrations
        else:
            self.aberrations = {'C10': np.random.rand(), # defocus
                                'C12': np.random.rand(), # 2-fold astigmatism
                                'C21': np.random.rand(), # 3-fold astigmatism
                                'C23': np.random.rand(), # coma
                                }

# Watining for Utkarsh
# class RealSTEM():
#     def __init__(self):
#         self.microscope = TemMicroscopeClient()
# 
#     def connect(self, ip, port):
#         self.microscope.connect(ip, port)
# 
#     def load_data(self, dataset):
#         print("This function is not needed for the RealSTEM object")
# 
#     def get_haadf(size, dwell_time):
#         image = microscope.acquisition.acquire_stem_image(DetectorType.HAADF, size, dwell_time)
#         return image
# 
#     def get_probe(self):
#         print("This function is not needed for the RealSTEM object")
# 
#     def set_aberrations(self, aberrations):
#         # implement the button presser here
#         print("This function is not needed for the RealSTEM object")




# Deprecated code
class STEM(BaseMicroscope):
    def __init__(self):
        super().__init__()
        self.name = 'STEM Microscope'
        self.instrument_vendor = 'generic'
        self.instrument_type = 'STEM'
        self.data_source = 'None'  # enable people to provide it, generate it or use pre-acquired existing data
        

    def _load_dataset(self, data_source = 'test.h5'):
        ###e.g., generate the data if required at this step
        reader = SciFiReaders.NSIDReader(data_source)
        self.dataset = reader.read()
        # reader.close()
        try:
            # Attempt to access keys attribute to check if dataset is already a dictionary
            dataset_keys = self.dataset.keys()

        except AttributeError:
            # AttributeError is raised because 'dataset' is a list, so convert it to a dictionary
            dataset_dict = {}
            for i, item in enumerate(self.dataset):
                key = f"Channel_{i:03}"  # Format key with zero-padding, e.g., 'channel_000'
                dataset_dict[key] = item
            self.dataset = dataset_dict
        print("Dataset loaded", self.dataset)
        return None

    def get_overview_image(self, channel_key = "Channel_000"):
        print("channel_key", channel_key)
        return np.array(self.dataset[channel_key])
        #return np.array(self.datasets[0])

    def _parse_dataset(self):
        """
        Parses the dataset to identify and index different data types (IMAGE, SPECTRUM, POINT_CLOUD),
        and processes the scan data accordingly.

        This method creates three dictionaries to store indices for the different types of data:
        - `_im_ind`: stores indices for IMAGE data.
        - `_sp_ind`: stores indices for SPECTRUM data.
        - `_pc_ind`: stores indices for POINT_CLOUD data.
        - `_spi_ind`: stores indices for SPECTRAL_IMAGE data.

        It compiles the image data into a numpy array (`scan_ar`), extracts spatial coordinates from the first
        image dataset, and places the scanning tip at the center of the scan.

        Attributes:
            self._im_ind (dict): Dictionary mapping IMAGE dataset keys to their respective indices.
            self._sp_ind (dict): Dictionary mapping SPECTRUM dataset keys to their respective indices.
            self._pc_ind (dict): Dictionary mapping POINT_CLOUD dataset keys to their respective indices.
            self.scan_ar (numpy.ndarray): Array of computed image data.
            self.x_coords (numpy.ndarray): Array of x-coordinates for spatial positioning.
            self.y_coords (numpy.ndarray): Array of y-coordinates for spatial positioning.
            self.x (float): x-coordinate of the scanning tip, placed at the center of the scan.
            self.y (float): y-coordinate of the scanning tip, placed at the center of the scan.
        """

        _keys = list(self.dataset.keys())
        #index dict
        self._im_ind, self._sp_ind, self._pc_ind, self._spi_ind = {}, {}, {}, {}
        self.scan_ar = []# scan area?

        for i, (key, value) in enumerate(self.dataset.items()):
            data_type = value.data_type

            # Store indices and data based on the data type
            if data_type == sid.DataType['IMAGE']:
                self._im_ind[key] = i
                self.scan_ar.append(value.compute())
            elif data_type == sid.DataType['SPECTRUM']:
                self._sp_ind[key] = i
            elif data_type == sid.DataType['POINT_CLOUD']:
                self._pc_ind[key] = i
            elif data_type == sid.DataType['SPECTRAL_IMAGE']:
                self._spi_ind[key] = i



    def get_dataset_info(self):
        """
        TODO: add metadata info like: pixel size, accelaration voltage, convergence angle, etc.

        # so user can use this info to query the data
        """
        _keys = self.dataset.keys()
        info_list = [
            ('channel_keys', list(_keys)),
            ('signals', [self.dataset[k].quantity for k in _keys]),
            ('units', [self.dataset[k].units for k in _keys]),
            ('scans_channel_index', list(self._im_ind.values())), # eg: HAADF
            ('spectra_channel_index', list(self._sp_ind.values())), #
            ('point_clouds_channel_index', list(self._pc_ind.values())),
            ('spectral_image_channel_index', list(self._spi_ind.values())), # eg: EELS at each pixel in scan
            ('indexing', "image data['CHannel_000'] top left corner is (0,0)"),
            
        ]
        return info_list
    
    def get_point_data(self, spectrum_image_key, x, y):
        """emulates the data acquisition at a specific point

        Args:
            spectrum_image_key: Which index in sidpy dataset is spectrum index
            x : position in x
            y : position in y

        Returns:
            numpy array: data at that
            
        >>>spectrum = mic.datasets([1][0][0])
        >>>spectrum  is of shape 1496
        """
        return np.array(self.dataset[spectrum_image_key][x][y])
    
    
    def get_spectrum_image(self, spectrum_image_key="Channel_001"):
        """
        We need to calculate Errors for active learning experiments(DKL)
        Args:
            spectrum_image_index: Which index in sidpy dataset is spectrum index
            
        Returns: np.array -> shape is 3 dimensional
        """

        return np.array(self.dataset[spectrum_image_key])
    
    def get_spectrum_image_e_axis(self, spectrum_image_key = "Channel_001"):
        """
        To figure out scalarizers for active learning experiments(DKL). We need the energy range.
        TODO: This is more application oriented so need to think of a better structure
        Args:
            spectrum_image_index (str, optional)
        Returns: np.array
        """
        return self.dataset[spectrum_image_key].dim_2.values
    
        
    def pixel_size_X(self):
        return

    def pixel_size_Y(self):
        return 
    
    def get_acceleration_voltage(self):
        return 
        
        
    
    
    

    