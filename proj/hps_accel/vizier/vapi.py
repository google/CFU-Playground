import json
from abc import abstractclassmethod;


class ToJsonDict:
    @abstractclassmethod
    def to_json_dict(self) -> dict:
        pass

    def to_json(self) -> str:
        return json.dumps(self.to_json_dict())

class MetricSpec(ToJsonDict):
    def __init__(self, goal: str, metric: str):
        self.metric = metric
        self.goal = goal
    
    def to_json_dict(self):
        return {
            'metric': self.metric,
            'goal': self.goal,
        }

class NumericalValueSpec(ToJsonDict):
    def __init__(self, min, max):
        self.min_value = min
        self.max_value = max
    
    def to_json_dict(self):
        return {
            'min_value': self.min_value,
            'max_value': self.max_value,
        }

class DiscreteValueSpec(ToJsonDict):
    def __init__(self, values: 'list[int] | list[str]'):
        self.values: 'list[int] | list[str]' = values

CategoricalValueSpec = DiscreteValueSpec

class TrialParameter(ToJsonDict):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.ufield = 'value'
    
    def to_json_dict(self) -> dict:
        return {
            'parameter': self.name,
            self.ufield: self.value
        }

class TrialParameterDouble(TrialParameter):
    def __init__(self, name, value):
        super().__init__(name, value)
        self.ufield = 'float_value'

TrialParameterDiscrete = TrialParameterDouble

class TrialParameterInt(TrialParameter):
    def __init__(self, name, value):
        super().__init__(name, value)
        self.ufield = 'int_value'

class TrialParameterCategorical(TrialParameter):
    def __init__(self, name, value):
        super().__init__(name, value)
        self.ufield = 'string_value'

def _abstract_param_trial(name, value):
    raise Exception('Abstract parameter')

class Parameter:
    def __init__(self):
        self.type: str = 'PARAMETER_TYPE_UNSPECIFIED'
        self.value_spec: 'DiscreteValueSpec | NumericalValueSpec' = None
        self.scale = None
        self.trial = _abstract_param_trial

class ParameterInt(Parameter):
    def __init__(self, min, max, scale='UNSPECIFIED'):
        self.type = 'INTEGER'
        self.value_spec = NumericalValueSpec(min, max)
        self.scale = scale
        self.trial = TrialParameterInt
    
    def trial(self, name: str, value) -> TrialParameter:
        TrialParameterInt(name, value)

class ParameterDouble(Parameter):
    def __init__(self, min, max, scale='UNSPECIFIED'):
        self.type = 'DOUBLE'
        self.value_spec = NumericalValueSpec(min, max)
        self.scale = scale
        self.trial = TrialParameterDouble

class ParameterCategorical(Parameter):
    def __init__(self, *values):
        self.type = 'CATEGORICAL'
        self.value_spec = DiscreteValueSpec(*values)
        self.trial = TrialParameterCategorical

class ParameterDiscrete(Parameter):
    def __init__(self, *values, scale='UNSPECIFIED'):
        self.type = 'DISCRETE'
        self.value_spec = DiscreteValueSpec(*values)
        self.scale = scale
        self.trial = self.trial = TrialParameterDiscrete

class DecayCurveStoppingConfig(ToJsonDict):
    def __init__(self, use_elapsed_time=False):
        self.use_elapsed_time = use_elapsed_time

    def to_json_dict(self) -> dict:
        return { 
            'DecayCurveAutomatedStoppingConfig': {
                'useElapsedTime': self.use_elapsed_time
            }
        }

class MedianAutomatedStoppingConfig(ToJsonDict):
    def __init__(self, use_elapsed_time=False):
        self.use_elapsed_time = use_elapsed_time

    def to_json_dict(self) -> dict:
        return { 
            'MedianAutomatedStoppingConfig': {
                'useElapsedTime': self.use_elapsed_time
            }
        }

_vizier_scale_map = {
    'UNSPECIFIED': 'SCALE_TYPE_UNSPECIFIED',
    'LINEAR': 'UNIT_LINEAR_SCALE',
    'LOG': 'UNIT_LOG_SCALE',
    'REVERSE_LOG': 'UNIT_REVERSE_LOG_SCALE'
}

class Study(ToJsonDict):
    def __init__(
        self,
        name: str,
        max_trials: int,
        metrics: 'list[MetricSpec]',
        parameters: 'dict[str, Parameter]',
        algorithm: str = 'ALGORITHM_UNSPECIFIED',
        asconfig: 'MedianAutomatedStoppingConfig | None' = None
    ):
        self.name = name
        self.algorithm: str = algorithm
        self.metrics: 'dict[str, str]' = metrics
        self.parameters: 'dict[str, Parameter]' = parameters
        self.asconfig: 'MedianAutomatedStoppingConfig | None' = asconfig
        self.max_trials = max_trials
    
    def to_json_dict(self):
        parameters = []
        for name, spec in self.parameters.items():
            p = {
                'parameter': name,
                'type': spec.type,
                f'{spec.type.lower()}_value_spec': spec.value_spec.to_json_dict()
            }
            if spec.scale:
                p['scale_type'] = _vizier_scale_map[spec.scale]
            parameters += [p]

        d = {
            'metrics': [MetricSpec(goal, name).to_json_dict() for name, goal in self.metrics.items()],
            'parameters': parameters,
            'algorithm': self.algorithm,
        }
        if self.asconfig is not None:
            d['automatedStoppingConfig'] = self.asconfig.to_json_dict()
        return d

class Metric(ToJsonDict):
    def __init__(self, metric, value):
        self.metric = metric
        self.value = value
    
    def to_json_dict(self) -> dict:
        return {
            'metric': self.metric,
            'value': self.value
        }
        

class Measurement(ToJsonDict):
    def __init__(self,
        step_count: int = 1,
        metrics: 'dict[str, ]' = {}
    ) -> None:
        self.step_count = step_count
        self.metrics = metrics
    
    def to_json_dict(self) -> dict:
        return {
            'step_count': self.step_count,
            'metrics': [Metric(name, val).to_json_dict() for name, val in self.metrics.items()]
        }

class Trial(ToJsonDict):
    def __init__(
        self,
        client_id = None,
        state: str = 'STATE_UNSPECIFIED',
        parameters: 'list[TrialParameter]' = [],
        measurements: 'list[Measurement]' = [],
        final_measurement: 'int | None' = None
    ):
        self.state = state
        self.client_id = client_id
        self.parameters: 'list[TrialParameter]' = parameters
        self.measurements: 'list[Measurement]' = measurements
        self.final_measurement: 'int | None' = final_measurement
        
        # See https://cloud.google.com/ai-platform/optimizer/docs/reference/rest/v1/projects.locations.studies.trials
        # description of measurements[] field
        self.measurements.sort(key=lambda m: (m.step_count, m.elapsed_time))
    
    def to_json_dict(self) -> dict:
        return {
            'state': self.state,
            'parameters': [p.to_json_dict() for p in self.parameters],
            'measurements': [m.to_json_dict() for m in self.measurements],
        }
