from abc import abstractclassmethod
from concurrent.futures import ThreadPoolExecutor

from  vizier.vapi import *
from vizier.client import OptimizerClient

class Optimizer:
    def __init__(self, study: Study, concurrency: int):
        self.study = study
        self.concurrency = concurrency
    
    @abstractclassmethod
    def run_blackbox(self, instance: int, **params) -> 'list[Measurement]':
        pass

    def optimize(self, client: OptimizerClient) -> Trial:
        i_trial = 0
        while i_trial < self.study.max_trials:
            suggested_trials = client.get_suggestions(self.study, self.concurrency)

            if len(suggested_trials) == 0:
                break

            trial_nos = [str(i) for i in range(i_trial, i_trial + len(suggested_trials))]
            print(f'Running trials {", ".join(trial_nos)}...\n')

            def suggested_params():
                for trial in suggested_trials:
                    yield dict((p.name, p.value) for p in trial.parameters)
            def run_bb(instancee, params):
                return self.run_blackbox(instancee, **params)
            
            with ThreadPoolExecutor(max_workers=len(suggested_trials)) as executor:
                instances = range(0, len(suggested_trials))
                threads = executor.map(run_bb, instances, suggested_params())
                for ms, t in zip(threads, suggested_trials):
                    t.measurements = [client.process_measurement(self.study, m) for m in ms]
                    print(f'Completing trial {t.to_json_dict()}\n')
                    client.complete_trial(self.study, t)
            
            i_trial += len(suggested_trials)

        return client.get_best_trial(self.study)
