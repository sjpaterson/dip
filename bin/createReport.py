import os
import sys
import pandas as pd

report = pd.DataFrame(columns=['obsid', 'generateCalibration', 'applyCalibration', 'flagUV', 'uvSub', 'image', 'postImage_0000', 'postImage_0001', 'postImage_0002', 'postImage_0003', 'postImage_MFS', 'sourcecount_0000', 'sourcecount_0001', 'sourcecount_0002', 'sourcecount_0003', 'sourcecount_MFS', 'rms_0000', 'rms_0001', 'rms_0002', 'rms_0003', 'rms_MFS', 'obsDir'])
report.set_index('obsid', inplace=True)
report.to_csv('dip_report.csv')
