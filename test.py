# -*- coding: utf-8 -*-
"""test.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Y2E4XwlQdL5cu6RY1UMulmRkBQEpLdiN
"""

import os
import sys
import numpy as np
from sklearn.metrics import confusion_matrix
from scipy.spatial.distance import cdist
from skimage.measure import label, regionprops, moments, moments_central, moments_normalized, moments_hu
from skimage import io, exposure
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pickle
from collections import Counter
from train import getFeatures


def testFeatures(filename, display_plot=False):
    
    th = 225
    result = {}
    Features = []
    coordinate = []
    img = io.imread(filename)

    # print img.shape

    # latest version of numpy remove np.double
    img_binary = (img < th).astype(np.double)
    result['img_binary'] = img_binary
        
    img_label = label(img_binary, background=0) # neighbors default = 8 use connectivity=1 neighbors=4
    # output number of labeled sub image
    # print np.amax(img_label)

    # show plots
    if display_plot:
        io.imshow(img)
        plt.title('Original Image')
        io.show()

        hist = exposure.histogram(img)
        plt.bar(hist[1], hist[0])
        plt.title('Histogram')
        plt.show()
            
        io.imshow(img_binary)
        plt.title('Binary Image')
        io.show()

        io.imshow(img_label)
        plt.title('Labeled Image')
        io.show()

    regions = regionprops(img_label)
    # find the threshold used to remove the small noise
    thre_noise = {'height':[10.0, 80.0], 'width':[12.0, 85.0]}
    io.imshow(img_binary)
    ax = plt.gca()
    for props in regions:
        # coordinate of the pixels
        minr, minc, maxr, maxc = props.bbox

        # use if to remove too small or too large region
        if (maxr - minr < thre_noise['height'][0] or maxc - minc < thre_noise['width'][0] 
        or maxr - minr > thre_noise['height'][1] or maxc - minc > thre_noise['width'][1]):
            continue

        if display_plot:
            ax.add_patch(Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, 
                        edgecolor='red', linewidth=1))
        #print minc, minr, maxc, maxr, maxr-minr, maxc-minc
        roi = img_binary[minr:maxr, minc:maxc]
        m = moments(roi)
        cr = m[0, 1] / m[0, 0]
        cc = m[1, 0] / m[0, 0]
        mu = moments_central(roi, center=(cr, cc))
        nu = moments_normalized(mu)
        hu = moments_hu(nu)

        Features.append(hu)
        coordinate.append([minr, minc, maxr, maxc])

    if display_plot:
        plt.title('Bounding Boxes')
        io.show()

    result['Features'] = Features
    result['Coordinate'] = coordinate

    return result


def normalized(features, mean, std):
    # normalization
    feature_array = np.array(features)
    norm_features = []
    for i in range(feature_array.shape[0]):
        feature_array[i] -= mean
        feature_array[i] /= std
        norm_features.append(feature_array[i])

    return norm_features


def predict(test_filename, file_path, display_plot):
    train_features, Label, mean, std = getFeatures(file_path, display_plot)
    dataset = testFeatures(test_filename, display_plot)

    # normalization for test data features
    test_features = normalized(dataset['Features'], mean, std)

    D = cdist(test_features, train_features)
    if display_plot:
        io.imshow(D)
        plt.title('Distance Matrix')
        io.show()

    D_index = np.argsort(D, axis=1)
    Ypred = [Label[i[0]] for i in D_index]
    if display_plot:
        TestBound(dataset['img_binary'], Ypred, dataset['Coordinate'])

    return Ypred, dataset['Coordinate'], D


def TestBound(img_binary, Ypred, Coordinate):

    io.imshow(img_binary)
    ax = plt.gca()    
    for i in range(len(Ypred)):
        y = Ypred[i]
        c = Coordinate[i]
        minr, minc, maxr, maxc = c[0], c[1], c[2], c[3]

        ax.add_patch(Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, 
                    edgecolor='red', linewidth=1))
        plt.text(maxc, minr, y, bbox=dict(facecolor='red', alpha=0.5))
    plt.title('Bounding Boxes for test image')
    io.show()


def score(testName, Ypred, Coordinate):
    pkl_file = open(file_path+testName, 'rb')
    #print(pickle.load(open(file_path+testName, 'rb')))
    mydict = pickle.load(pkl_file)
    pkl_file.close() 
    classes = mydict[b'classes'] 
    location = mydict[b'locations'] 

    
    num_correct = 0.0
    num_total = len(classes)
    for i in range(num_total):
        for j in range(len(Coordinate)):
            cenc = location[i][0]
            cenr = location[i][1]
            minr, minc = Coordinate[j][0], Coordinate[j][1]
            maxr, maxc = Coordinate[j][2], Coordinate[j][3]
            if cenr < minr or cenr > maxr or cenc < minc or cenc > maxc:
                continue

            if classes[i] == Ypred[j]:
                num_correct += 1
                break
    accuracy_rate = num_correct / num_total

    return accuracy_rate



if __name__ == "__main__":
    #file_path = sys.argv[1]
    file_path='/content/images/'
    display_plot = True
    test_1 = file_path + 'test.bmp'
    test_result = 'test_gt_py3.pkl'

    Ypred, Coordinate, D = predict(test_1, file_path, display_plot)

    accuracy = score(test_result, Ypred, Coordinate)
    print(accuracy)



"""# New Section"""