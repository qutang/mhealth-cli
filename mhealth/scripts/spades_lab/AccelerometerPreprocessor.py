"""
  preprocess pipeline for multilocation paper 2017

  1. calibration
  2. timestamp syncing
  3. clipping

  [Insert citation]
  Usage:
     Production
        `mh -r . process --par --verbose --pattern SPADES_*/MasterSynced/**/Actigraph*.sensor.csv spades_lab.AccelerometerPreprocessor --setname Preprocessed`
        `mh -r . -p SPADES_1 process --par --verbose --pattern MasterSynced/**/Actigraph*.sensor.csv spades_lab.AccelerometerPreprocessor --setname Preprocessed`

    Debug
         `mh -r . -p SPADES_1 process --verbose --pattern MasterSynced/**/Actigraph*.sensor.csv spades_lab.AccelerometerPreprocessor --setname Preprocessed`
"""

import os
import pandas as pd
import mhealth.scripts as ms
import mhealth.api as mhapi
import mhealth.api.utils as mu
from .TimestampSyncer import TimestampSyncer
from ..BaseProcessor import SensorProcessor

def build(**kwargs):
    return AccelerometerProcessor(**kwargs).run_on_file

class AccelerometerProcessor(SensorProcessor):
    def __init__(self, verbose=True, independent=True, setname='Proprocessed'):
        SensorProcessor.__init__(self, verbose=verbose, independent=independent)
        self.name = 'AccelerometerProcessor'
        self.setname = setname

    def _build_pipeline(self):
        self.pipeline = list()
        calibrator = ms.AccelerometerCalibrator(verbose=self.verbose, independent=self.independent, static_chunk_file='DerivedCrossParticipants/static_chunks.csv')
        self.pipeline.append(calibrator)

        syncer = TimestampSyncer(verbose=self.verbose, independent=self.independent, sync_file='DerivedCrossParticipants/offset_mapping.csv')
        self.pipeline.append(syncer)

        clipper = ms.SensorClipper(verbose=self.verbose, independent=self.independent, session_file='DerivedCrossParticipants/sessions.csv')
        self.pipeline.append(clipper)

    def _run_on_data(self, combined_data, data_start_indicator, data_stop_indicator):
        result_data = combined_data.copy(deep=True)
        self._build_pipeline()
        for pipe in self.pipeline:
            print('Execute ' + str(pipe) + " on file: " + self.file)
            pipe.set_meta(self.meta)
            result_data = pipe._run_on_data(result_data, data_start_indicator, data_stop_indicator)
            print(result_data.shape)
        return result_data

    def _post_process(self, result_data):
        output_file = mu.generate_output_filepath(self.file, self.setname, 'sensor')
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))
        result_data.to_csv(output_file, index=False, float_format='%.3f')
        if self.verbose:
            print('Saved preprocessed accelerometer data to ' + output_file)
        
        # we don't need to concatenate results, so return an empty dataframe
        return pd.DataFrame()

def main(file, verbose=True, **kwargs):
  file = os.path.abspath(file)
  df = pd.read_csv(file, parse_dates=[0], infer_datetime_format=True)

  pid = mh.extract_pid(file)
  sid = mh.extract_id(file)
  date = mh.extract_date(file)
  hour = mh.extract_hour(file)

  pipeline = list()

  pipeline.append({
    'name': 'calibration',
    'func': scripts.calibrate_accel.run_calibrate_accel,
    'kwargs': {
      'static_chunk_file': 'DerivedCrossParticipants/static_chunks.csv',
      'pid': pid,
      'sid': sid
    }
  })

  pipeline.append({
    'name': 'sync',
    'func': sync_timestamp.run_sync_timestamp,
    'kwargs': {
      'sync_file': 'DerivedCrossParticipants/offset_mapping.csv',
      'pid': int(pid.split("_")[1])
    }
  })

  pipeline.append({
    'name': 'clip',
    'func': scripts.clipper.run_clipper,
    'kwargs': {
      'session_file': 'DerivedCrossParticipants/sessions.csv',
      'pid': pid
    }
  })

  result = df.copy(deep=True)
  for pipe in pipeline:
    print('Execute ' + pipe['name'] + " on file: " + file)
    print(result.shape)
    func = pipe['func']
    kwargs = pipe['kwargs']
    result = func(result, verbose=verbose, **kwargs)
    print(result.shape)

  # save to individual file
  output_file = file.replace('MasterSynced', 'Derived/preprocessed')
  if not os.path.exists(os.path.dirname(output_file)):
    os.makedirs(os.path.dirname(output_file))
  result.to_csv(output_file, index=False, float_format='%.3f')
  if verbose:
    print('Saved preprocessed data to ' + output_file)
  
  # we don't need to concatenate results, so return an empty dataframe
  return pd.DataFrame()