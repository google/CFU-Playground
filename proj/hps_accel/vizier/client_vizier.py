import math
import random
import time

from google.cloud import storage
from googleapiclient import discovery, errors
from scipy.fftpack import idct

from vizier.client import OptimizerClient
from vizier.vapi import *

_OPTIMIZER_API_DOCUMENT_BUCKET = 'caip-optimizer-public'
_OPTIMIZER_API_DOCUMENT_FILE = 'api/ml_public_google_rest_v1.json'

random.seed()

def _read_api_document(project_id):
    client = storage.Client(project_id)
    bucket = client.get_bucket(_OPTIMIZER_API_DOCUMENT_BUCKET)
    blob = bucket.get_blob(_OPTIMIZER_API_DOCUMENT_FILE)
    return blob.download_as_string()

def _trial_name(project_id, region, study_id, trial_id):
  return f'projects/{project_id}/locations/{region}/studies/{study_id}/trials/{trial_id}'

def trial_from_gtrial(study: Study, id, gtrial):    
    trial = Trial(
        client_id = id,
        state = gtrial['state'],
        parameters = [],
        measurements = []
    )

    for param in gtrial['parameters']:
        pname = param['parameter']
        ptype = study.parameters[pname].type
        pval = None
        if ptype in ['DOUBLE', 'DISCRETE']:
            pval = param['floatValue']
        elif ptype == 'INTEGER':
            pval = param['intValue']
        elif ptype == 'CATEGORICAL':
            pval = param['stringValue']
        else:
            raise Exception('Unknown parameter type')

        p: Parameter = study.parameters[pname].trial(pname, pval)
        trial.parameters += [p]
    
    return trial

class VizierClient(OptimizerClient):
    def __init__(self, account, project_id, region):
        self.account = account
        self.project_id = project_id
        self.region = region
        self.client_id = f'client{"".join([str(random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])) for i in range(0, 8)])}'
        self.api = discovery.build_from_document(service=_read_api_document(self.project_id))
    
    def create_study(self, study: Study, concurrency: int):
        # study_id = f'{self.account}_study_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
        req = self.api.projects().locations().studies().create(
            parent=f'projects/{self.project_id}/locations/{self.region}',
            studyId=study.name,
            body={'study_config': study.to_json_dict()}
        )
        try:
            print(req.execute())
        except errors.HttpError as e:
            if e.resp.status == 409:
                print('Study already existed.')
            else:
                raise e
    
    def get_suggestions(self, study: Study, concurrency: int) -> 'list[Trial]':
        resp = self.api.projects().locations().studies().trials().suggest(
            parent = f'projects/{self.project_id}/locations/{self.region}/studies/{study.name}',
            body = { 'client_id': self.client_id, 'suggestion_count': concurrency }
        ).execute()
        op_id = resp['name'].split('/')[-1]
        get_op = self.api.projects().locations().operations().get(
            name = f'projects/{self.project_id}/locations/{self.region}/operations/{op_id}'
        )

        # Wait for GCloud to be done
        while True:
            op = get_op.execute()
            if 'done' in op and op['done']:
                break
            time.sleep(1)
        
        trials = []
        for suggestion in get_op.execute()['response']['trials']:
            id = int(suggestion['name'].split('/')[-1])
            gtrial = self.api.projects().locations().studies().trials().get(
                name=_trial_name(self.project_id, self.region, study.name, id)
            ).execute()

            if gtrial['state'] in ['COMPLETED', 'INFEASIBLE']:
                continue

            trial = trial_from_gtrial(study, id, gtrial)

            trials += [trial]
        
        print(f'Suggestions: {[t.to_json_dict() for t in trials]}')

        return trials
            
    def process_measurement(
        self,
        study: Study,
        measurement: Measurement
    ) -> Measurement:
        # Google Cloud Measurements don't require extra processing
        return measurement
    
    def complete_trial(self, study: Study, trial: Trial):
        trial_name = _trial_name(self.project_id, self.region, study.name, trial.client_id)
        for m in  [m.to_json_dict() for m in trial.measurements]:
            self.api.projects().locations().studies().trials().addMeasurement(
            name = trial_name,
            body={'measurement': m}
        ).execute()
        self.api.projects().locations().studies().trials().complete(
            name = trial_name
        ).execute()

    def get_best_trial(self, study: Study) -> Trial:
        resp = self.api.projects().locations().studies().trials().list(
            parent = f'projects/{self.project_id}/locations/{self.region}/studies/{study.name}'
        ).execute()

        trials: 'list[Trial]' = []
        
        for gtrial in resp['trials']:
            if 'finalMeasurement' in gtrial:
                id = int(gtrial['name'].split('/')[-1])
                trial = trial_from_gtrial(study, id, gtrial)
                trial.measurements += [Measurement()]
                for metric in gtrial['finalMeasurement']['metrics']:
                    # TODO: Cloud does not return the `value` field.
                    # Investigate what's going on.
                    trial.measurements[-1].metrics[metric['metric']] = metric['value']
                
                if trial is None:
                    continue
                trials += [trial]
        
        # Find minimums / maximums for each metric in order to construct
        # a space for optimizing length of a vector
        mins = {}
        maxs = {}
        for t in trials:
            # Dunno what to do with extra measuremenrs
            measurement = t.measurements[-1]
            for m_name, m_value in measurement.metrics:
                if mins.get(m_name) is None:
                    mins[m_name] = m_value
                elif mins[m_value] > m_value:
                    mins[m_value] = m_value
                if maxs.get(m_name) is None:
                    maxs[m_name] = m_value
                elif maxs[m_value] < m_value:
                    maxs[m_value] = m_value

        # Minimze length of a metrics vector
        maxlen = 0
        best_trial = None
        for t in trials:
            # Dunno what to do with extra measuremenrs
            measurement = t.measurements[-1]

            length = 0
            for m_name, m_value in measurement.metrics.items():
                v = 0 
                if study.metrics[m_name] == 'MINIMIZE':
                    v = maxs[m_name] - m_value
                else:
                    v = m_value - mins[m_name]

                length += v * v
            length = math.sqrt(length)
            if length > maxlen:
                maxlen = length
                best_trial = t
        
        return best_trial