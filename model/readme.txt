threshold_0.005
  model_classification_1: Model trained from 20180416 to 20180420, with all possible points

  model_classification_3: Model trained from 20180416 to 20180420, with points before 11:00am

  model_classification_2: Model trained from 20180416 to 20180430, with all
    possible points and buy time finishes before 1255
    Test on 20180501 to 20180504:
      Total number of samples: train: 4489274, test: 186665
      Number of positive in training: 1388413, in testing: 74113
      positive in training: 30.927%, in testing: 39.704%
      Epoch 249, train accuracy: 0.713840126991, test accuracy: 0.647995054722
        Train: TP: 0.084, FP: 0.061; Test: TP: 0.107, FP: 0.062
        Train: FN: 0.225, TN: 0.630; Test: FN: 0.290, TN: 0.541

  model_classification_0: Model trained from 20180416 to 20180420, 
    Number of timepoints range from 100 to 149
    Total number of samples: train: 413987, test: 47330
      Number of positive in training: 157518, in testing: 20918
      Ratio of positive in training: 0.38049020863, in testing: 0.441960701458
    Epoch 249, train accuracy: 0.664924263954, test accuracy: 0.597992837429
      Train: TP: 0.133, FP: 0.088; Test: TP: 0.173, FP: 0.133
      Train: FN: 0.247, TN: 0.532; Test: FN: 0.269, TN: 0.425

  model_classification_4: Model trained from 20180416 to 20180420,
    Number of timepoints range from 150 to 199
    Total number of samples: train: 394320, test: 45467
      Number of positive in training: 140848, in testing: 17837
      Ratio of positive in training: 0.357192128221, in testing: 0.392306508017
    train accuracy: 0.676876664162, test accuracy: 0.620208084583
      Train: TP: 0.113, FP: 0.079; Test: TP: 0.142, FP: 0.130
      Train: FN: 0.244, TN: 0.564; Test: FN: 0.250, TN: 0.478
  
  model_classification_9: Model trained from 20180416 to 20180420, with updated
  eligible list that requires dense time points.
    Number of all the samples: train: 278950, test: 31467
    Number of positive in training: 110881, in testing: 14647
    Ratio of positive in training: 0.397494174583, in testing: 0.46547176407
    train accuracy: 0.663979232311, test accuracy: 0.580608248711
    Train: TP: 0.158, FP: 0.097; Test: TP: 0.183, FP: 0.137
    Train: FN: 0.239, TN: 0.506; Test: FN: 0.282, TN: 0.397

  model_classification_12: Model trained from 20180416 to 20180420, with updated
  eligible list that requires dense time points and number of available timepoints
  range from 100 to 149.
    Total number of samples: train: 278950, test: 31467
    Number of positive in training: 110881, in testing: 14647
    Ratio of positive in training: 0.397494174583, in testing: 0.46547176407
    Train accuracy: 0.659946203232, test accuracy: 0.577557444572
    Train: TP: 0.144, FP: 0.086; Test: TP: 0.168, FP: 0.125
    Train: FN: 0.254, TN: 0.516; Test: FN: 0.298, TN: 0.410

sell_classifier
  model_classification_17: Model trained from 20180416 to 20180420, with updated
  eligible list that requires dense time points. No restriction on number of time points.
  Total number of samples: train: 1443131, test: 1732727
    Number of positive in training: 335914, in testing: 350405
    Ratio of positive in training: 0.232767503435, in testing: 0.202227471494
    train accuracy: 0.821592748165, test accuracy: 0.824496328831
      TP: 0.157, FP: 0.102; Test: TP: 0.122, FP: 0.095
      FN: 0.076, TN: 0.665; Test: FN: 0.080, TN: 0.702


