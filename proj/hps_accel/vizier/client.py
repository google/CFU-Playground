from abc import abstractclassmethod;

from vizier.vapi import *

class OptimizerClient:
    def __init__(self):
        pass

    @abstractclassmethod
    def create_study(self, study: Study, concurrency: int):
        pass
    
    @abstractclassmethod
    def get_suggestions(self, study: Study, concurrency: int) -> 'list[Trial]':
        pass
    
    @abstractclassmethod
    def process_measurement(
        self,
        study: Study,
        measurement: Measurement
    ) -> Measurement:
        pass

    @abstractclassmethod
    def complete_trial(self, study: Study, trial: Trial):
        pass

    @abstractclassmethod
    def get_best_trial(self, study: Study) -> Trial:
        pass