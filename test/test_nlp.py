from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt
from sklearn import manifold

from pyamihtmlx.ami_nlp import AmiNLP
from test.resources import Resources
from test.test_all import AmiAnyTest


class NLPTest(AmiAnyTest):
    import nltk, string

    def test_compute_similarity(self):
        ami_nlp = AmiNLP()
        print(f"sim00 {ami_nlp.cosine_sim('a little bird', 'a little bird')}")
        print(f"sim01 {ami_nlp.cosine_sim('a little bird', 'a little bird chirps')}")
        print(f"sim02 {ami_nlp.cosine_sim('a little bird', 'a big dog barks')}")

    def test_plot_scatter_noel_oboyle(self):

        # Distance file available from RMDS project:
        #    https://github.com/cheind/rmds/blob/master/examples/european_city_distances.csv
        data = []
        input = Path(Resources.TEST_RESOURCES_DIR, "misc", "european_city_distances.csv")
        delimiter = ';'
        reader = csv.reader(open(input, "r"), delimiter=delimiter)
        data = list(reader)

        dists = []
        labels = []
        for d in data:
            labels.append(d[0])
            dists.append([float(dd) for dd in d[1:-1]])

        AmiNLP.plot_points_labels(dists, labels)

