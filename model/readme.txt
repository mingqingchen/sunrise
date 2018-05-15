threshold_0.005
  model_classification_35: Model trained from 20180426 to 20180504,
    allow data before 6:30 coming in.
    Fine tuned on model_classification_25.
    Total number of samples: train: 232299, test: 143666
    Number of positive in training: 141713, in testing: 85371
    Ratio of positive in training: 0.610045673894, in testing: 0.594232455835
    train accuracy: 0.666688203812, test accuracy: 0.629376471043
    Train: TP: 0.542, FP: 0.266; Test: TP: 0.485, FP: 0.262
    Train: FN: 0.068, TN: 0.124; Test: FN: 0.109, TN: 0.144
  
  model_classification_25: Model trained from 20180416 to 20180420, with updated
  eligible list that requires dense time points and number of available timepoints
  range from 100 to 149.
    Total number of samples: train: 278950, test: 322276
      Number of positive in training: 110882, in testing: 148474
      Ratio of positive in training: 0.397497759455, in testing: 0.46070448932
    train accuracy: 0.677806079388, test accuracy: 0.571795582771
     TP: 0.167, FP: 0.092; Test: TP: 0.176, FP: 0.144
     FN: 0.230, TN: 0.511; Test: FN: 0.284, TN: 0.395

sell_classifier
  model_classification_34: Model trained from 20180426 to 20180504,
    Allow data before 6:30 coming in.
    Fine tuned on model_classification_28.
    Total number of samples: train: 1237364, test: 767935
    Number of positive in training: 254400, in testing: 175736
    Ratio of positive in training: 0.205598352627, in testing: 0.228842284829
    train accuracy: 0.823915183544, test accuracy: 0.805940628052
    Train: TP: 0.084, FP: 0.055; Test: TP: 0.106, FP: 0.071
    Train: FN: 0.121, TN: 0.739; Test: FN: 0.123, TN: 0.700

  model_classification_28: Model trained from 20180416 to 20180430, 
    Total number of samples: train: 3518026, test: 929565
    Number of positive in training: 770779, in testing: 194026
    Ratio of positive in training: 0.219094173835, in testing: 0.208727738243
    Train accuracy: 0.820596814156, test accuracy: 0.816714286804
    Train: TP: 0.115, FP: 0.076; Test: TP: 0.101, FP: 0.075
    Train: FN: 0.104, TN: 0.705; Test: FN: 0.108, TN: 0.716

  model_classification_25: Model trained from 20180416 to 20180420, with updated
  eligible list that requires dense time points. No restriction on number of time points.
    Total number of samples: train: 1443131, test: 1732727
    Number of positive in training: 335914, in testing: 350405
    Ratio of positive in training: 0.232767503435, in testing: 0.202227471494
    train accuracy: 0.821592748165, test accuracy: 0.824496328831
      TP: 0.157, FP: 0.102; Test: TP: 0.122, FP: 0.095
      FN: 0.076, TN: 0.665; Test: FN: 0.080, TN: 0.702


