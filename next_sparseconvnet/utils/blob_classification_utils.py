import numpy    as np
import pandas   as pd
import tables   as tb
import networkx as nx

import itertools

from next_sparseconvnet.utils.data_loaders             import DataGen, LabelType
from next_sparseconvnet.data_io_scripts.plotting_utils import read_event

def number_of_blobs(pred_dataset_path, dataset_id, threshold, class_type = 'class_2', max_distance = np.sqrt(3)):
    '''
    For a prediction, returns the number of blobs for data above a threshold using graphs
    '''
    event_df = read_event(pred_dataset_path, dataset_id, table='VoxelsPred')
    selected_hits = pd.DataFrame()
    selected_hits[['xbin', 'ybin', 'zbin']] = event_df[['xbin', 'ybin', 'zbin']][event_df[class_type]>threshold]
    voxels = [tuple(x) for x in selected_hits.to_numpy()]
    vox_graph = nx.Graph()
    for va, vb in itertools.combinations(voxels, 2):
        va_arr, vb_arr = np.array(va), np.array(vb)
        dis = np.linalg.norm(va_arr-vb_arr)
        if dis < max_distance:
            vox_graph.add_edge(va, vb, distance = dis)
    nblobs = nx.algorithms.components.number_connected_components(vox_graph)
    return nblobs

def segmentation_blob_classification(orig_dataset_path, pred_dataset_path, threshold, nevents = None):
    '''
    Adds a column to the events dataframe where depending on the number of blobs the predicted data had,
    events are classified as signal or background
    '''
    original_events = DataGen(orig_dataset_path, LabelType.Segmentation, nevents = nevents).events
    original_events['pred_class'] = ''
    for i in range(len(original_events)):
        nblobs = number_of_blobs(pred_dataset_path, i, threshold)
        if nblobs == 2:
            original_events.at[i, 'pred_class'] = 1 #signal
        else:
            original_events.at[i, 'pred_class'] = 0 #background
    return original_events

def success_rates(true_class, predicted_class):
    TP, TN, FP, FN = 0, 0, 0, 0
    for i in range(len(true_class)):
        if predicted_class[i] == 1 and true_class[i] == 1:
            TP += 1
        if predicted_class[i] == 0 and true_class[i] == 0:
            TN += 1
        if predicted_class[i] == 1 and true_class[i] == 0:
            FP += 1
        if predicted_class[i] == 0 and true_class[i] == 1:
            FN += 1

    good = TP + TN
    bad = FP + FN
    total = good + bad
    accuracy = good/total

    tpr = TP / (TP + FN)
    fpr = FP / (FP +TN)
    tnr = 1 - fpr
    return accuracy, tpr, tnr
