from concurrent import futures
import grpc
import portpicker

from vizier.service import clients
from vizier.service import pyvizier as vz
from vizier.service import vizier_server
from vizier.service import vizier_service_pb2_grpc

from dse_framework import dse

NUM_TRIALS = 2

problem = vz.ProblemStatement()
problem.search_space.select_root().add_bool_param(name='bypass')
problem.search_space.select_root().add_bool_param(name='cfu')
problem.search_space.select_root().add_bool_param(name='hardwareDiv')
problem.search_space.select_root().add_bool_param(name='mulDiv')
problem.search_space.select_root().add_bool_param(name='singleCycleShift')
problem.search_space.select_root().add_bool_param(name='singleCycleMulDiv')
problem.search_space.select_root().add_bool_param(name='safe')
problem.search_space.select_root().add_categorical_param(
    name='prediction', feasible_values=['none', 'static', 'dynamic', 'dynamic_target'])
problem.search_space.select_root().add_discrete_param(
    name='iCacheSize', feasible_values=[0, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384])
problem.search_space.select_root().add_discrete_param(
    name='dCacheSize', feasible_values=[0, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384])

problem.metric_information.append(
    vz.MetricInformation(
        name='cycles', goal=vz.ObjectiveMetricGoal.MINIMIZE))

problem.metric_information.append(
    vz.MetricInformation(
        name='cells', goal=vz.ObjectiveMetricGoal.MINIMIZE))

def evaluate(bypass, cfu, dCacheSize, hardwareDiv, iCacheSize, mulDiv, prediction, safe, singleCycleShift, singleCycleMulDiv):
  csrPluginConfig = "mcycle"
  TARGET = "digilent_arty"  
  cycles, cells = dse(csrPluginConfig, bypass, cfu, str(int(dCacheSize)), hardwareDiv, str(int(iCacheSize)), mulDiv, prediction, safe, singleCycleShift, singleCycleMulDiv, TARGET)
  return (cycles, cells)

study_config = vz.StudyConfig.from_problem(problem)
study_config.algorithm = vz.Algorithm.NSGA2

port = portpicker.pick_unused_port()
address = f'localhost:{port}'

# Setup server.
server = grpc.server(futures.ThreadPoolExecutor(max_workers=100))

# Setup Vizier Service.
servicer = vizier_server.VizierService()
vizier_service_pb2_grpc.add_VizierServiceServicer_to_server(servicer, server)
server.add_secure_port(address, grpc.local_server_credentials())

# Start the server.
server.start()

clients.environment_variables.service_endpoint = address  # Server address.
study = clients.Study.from_study_config(
    study_config, owner='owner', study_id='example_study_id')

suggestions = study.suggest(count=NUM_TRIALS)
for suggestion in suggestions:
  bypass = suggestion.parameters['bypass']
  cfu =  suggestion.parameters['cfu']
  dCacheSize =  suggestion.parameters['dCacheSize']
  hardwareDiv = suggestion.parameters['hardwareDiv']
  iCacheSize = suggestion.parameters['iCacheSize']
  mulDiv = suggestion.parameters['mulDiv']
  prediction = suggestion.parameters['prediction']
  safe = suggestion.parameters['safe']
  singleCycleShift = suggestion.parameters['singleCycleShift']
  singleCycleMulDiv = suggestion.parameters['singleCycleMulDiv']
  print('Suggested Parameters (bypass, cfu, dCacheSize, hardwareDiv, iCacheSize, mulDiv, prediction, safe, singleCycleShift, singleCycleMulDiv):', bypass, cfu, dCacheSize, hardwareDiv, iCacheSize, mulDiv, prediction, safe, singleCycleShift, singleCycleMulDiv)
  cells, cycles = evaluate(bypass, cfu, dCacheSize, hardwareDiv, iCacheSize, mulDiv, prediction, safe, singleCycleShift, singleCycleMulDiv)
  final_measurement = vz.Measurement({'cycles': cycles, 'cells':cells})
  suggestion.complete(final_measurement)

for optimal_trial in study.optimal_trials():
  optimal_trial = optimal_trial.materialize()
  print("Optimal Trial Suggestion and Objective:", optimal_trial.parameters,
        optimal_trial.final_measurement)
