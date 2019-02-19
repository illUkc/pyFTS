'''
Time Variant/Incremental Ensemble of FTS methods
'''


import numpy as np
import pandas as pd
from pyFTS.common import FuzzySet, FLR, fts, flrg
from pyFTS.partitioners import Grid
from pyFTS.models import hofts
from pyFTS.models.ensemble import ensemble


class IncrementalEnsembleFTS(ensemble.EnsembleFTS):
    """
    Time Variant/Incremental Ensemble of FTS methods
    """
    def __init__(self, **kwargs):
        super(IncrementalEnsembleFTS, self).__init__(**kwargs)
        self.shortname = "IncrementalEnsembleFTS"
        self.name = "Incremental Ensemble FTS"

        self.order = kwargs.get('order',1)

        self.partitioner_method = kwargs.get('partitioner_method', Grid.GridPartitioner)
        """The partitioner method to be called when a new model is build"""
        self.partitioner_params = kwargs.get('partitioner_params', {'npart': 10})
        """The partitioner method parameters"""

        self.fts_method = kwargs.get('fts_method', hofts.WeightedHighOrderFTS)
        """The FTS method to be called when a new model is build"""
        self.fts_params = kwargs.get('fts_params', {})
        """The FTS method specific parameters"""

        self.window_length = kwargs.get('window_length', 100)
        """The memory window length"""

        self.batch_size = kwargs.get('batch_size', 10)
        """The batch interval between each retraining"""

        self.is_high_order = True
        self.uod_clip = False
        #self.max_lag = self.window_length + self.max_lag

    def train(self, data, **kwargs):

        partitioner = self.partitioner_method(data=data, **self.partitioner_params)
        model = self.fts_method(partitioner=partitioner, **self.fts_params)
        if self.model.is_high_order:
            self.model = self.fts_method(partitioner=partitioner, order=self.order, **self.fts_params)
        model.fit(data, **kwargs)
        self.models.pop(0)
        self.models.append(model)

    def _point_smoothing(self, forecasts):
        l = len(self.models)

        ret = np.nansum([np.exp(-(l-k)) * forecasts[k] for k in range(l)])

        return ret

    def forecast(self, data, **kwargs):
        l = len(data)

        data_window = []

        ret = []

        for k in np.arange(self.max_lag, l):

            data_window.append(data[k - self.max_lag])

            if k >= self.window_length:
                data_window.pop(0)

            if k % self.batch_size == 0 and k >= self.window_length:
                self.train(data_window, **kwargs)

            sample = data[k - self.max_lag: k]
            tmp = self.get_models_forecasts(sample)
            point = self._point_smoothing(tmp)
            ret.append(point)

        return ret





