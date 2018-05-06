import numpy as np
import tensorflow as tf
import os
from random import shuffle
import logging

import util.data_provider as data_provider
import util.datetime_util as datetime_util

def SimpleFn(x, input_dimension, hidden_dimension = [128, 1]):
  """ A simple fully connected network with regression output
  :param x: input tensor
  :return: h_fc2: output tensor of regression
  """
  with tf.name_scope('fc1'):
    W_fc1 = weight_variable([input_dimension, hidden_dimension[0]])
    b_fc1 = bias_variable([hidden_dimension[0]])
    h_fc1 = tf.nn.relu(tf.matmul(x, W_fc1) + b_fc1)

  with tf.name_scope('fc2'):
    W_fc2 = weight_variable([hidden_dimension[0], hidden_dimension[1]])
    b_fc2 = bias_variable([hidden_dimension[1]])
    h_fc2 = tf.nn.relu(tf.matmul(h_fc1, W_fc2) + b_fc2)

  return tf.squeeze(h_fc2)

def SimpleFn2(x, architecture = [101, 32, 32, 1]):
  """ A simple fully connected network with regression output
  :param x: input tensor
  :return: h_fc2: output tensor of regression
  """
  with tf.name_scope('fc1'):
    W_fc1 = weight_variable([architecture[0], architecture[1]])
    b_fc1 = bias_variable([architecture[1]])
    h_fc1 = tf.nn.relu(tf.matmul(x, W_fc1) + b_fc1)

  with tf.name_scope('fc2'):
    W_fc2 = weight_variable([architecture[1], architecture[2]])
    b_fc2 = bias_variable([architecture[2]])
    h_fc2 = tf.nn.relu(tf.matmul(h_fc1, W_fc2) + b_fc2)

  with tf.name_scope('fc3'):
    W_fc3 = weight_variable([architecture[2], architecture[3]])
    b_fc3 = bias_variable([architecture[3]])
    h_fc3 = tf.nn.relu(tf.matmul(h_fc2, W_fc3) + b_fc3)

  return tf.squeeze(h_fc3)

def SimpleCnn(x, hidden_dimension = 32):
  # padding could be 'SAME' or 'VALID'
  x_reshape = tf.reshape(x, [-1, 100, 1])
  with tf.name_scope('cnn1'):
    W_conv1 = weight_variable([5, 1, 4])
    b_conv1 = bias_variable([4])
    h_conv1 = tf.nn.relu(tf.nn.conv1d(x_reshape, W_conv1, stride = 2, padding = 'VALID') + b_conv1)
  with tf.name_scope('cnn2'):
    W_conv2 = weight_variable([5, 4, 8])
    b_conv2 = bias_variable([8])
    h_conv2 = tf.nn.relu(tf.nn.conv1d(h_conv1, W_conv2, stride = 2, padding = 'VALID') + b_conv2)
  with tf.name_scope('cnn3'):
    W_conv3 = weight_variable([5, 8, 4])
    b_conv3 = bias_variable([4])
    h_conv3 = tf.nn.relu(tf.nn.conv1d(h_conv2, W_conv3, stride = 2, padding = 'VALID') + b_conv3)
  with tf.name_scope('fc1'):
    W_fc1 = weight_variable([36, hidden_dimension])
    b_fc1 = bias_variable([hidden_dimension])
    h_conv3_flat = tf.reshape(h_conv3, [-1, 36])
    h_fc1 = tf.nn.relu(tf.matmul(h_conv3_flat, W_fc1) + b_fc1)
  with tf.name_scope('fc2'):
    W_fc2 = weight_variable([hidden_dimension, 1])
    b_fc2 = bias_variable([1])
    h_fc2 = tf.nn.relu(tf.matmul(h_fc1, W_fc2) + b_fc2)

  return tf.squeeze(h_fc2)

def max_pool_2(x):
  """max_pool_2 downsamples a feature map by 2X."""
  return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                        strides=[1, 2, 2, 1], padding='SAME')
def weight_variable(shape):
  """weight_variable generates a weight variable of a given shape."""
  initial = tf.truncated_normal(shape, stddev=0.1)
  return tf.Variable(initial, tf.float32)


def bias_variable(shape):
  """bias_variable generates a bias variable of a given shape."""
  initial = tf.constant(0.1, shape=shape)
  return tf.Variable(initial, tf.float32)


class ModelManager:
  def __init__(self, data_folder, use_eligible_list):
    self.dm_ = data_provider.DataProvider(data_folder, use_eligible_list)

  def set_training_dates(self, start_date, end_date):
    self.train_start_date_ = start_date
    self.train_end_date_ = end_date

  def set_test_dates(self, start_date, end_date):
    self.test_start_date_ = start_date
    self.test_end_date_ = end_date

class FixedNumTimePointsModelManager(ModelManager):
  def __init__(self, data_folder, use_eligible_list):
    ModelManager.__init__(self, data_folder, use_eligible_list)

    # Fixed length of input vector
    self.num_time_points_ = 100

    # We should only select data after market open
    self.open_time_ = 630
    self.close_time_ = 1300
    self.total_minutes_normalizer_ = 390

    # Timepoint interval to step to prepare training data
    self.sample_step_training_ = 1
    self.sample_step_testing_ = 10

    # Parameters related to deep learning
    self.learning_rate_ = 3e-5
    self.num_epochs_ = 250
    self.batch_size_ = 32

    # Parameters of the network.
    self.architecture_ = [101, 32, 32]

    # Is classification or regression model
    self.is_classification_model_ = True
    self.classifify_threshold_ = 0.005

    # whether the training uses previous model as a starter
    self.load_previous_model_ = False
    self.previous_model_ = 'model_classification_0'

    # place to save the model
    self.model_folder_ = './model/'
    self.output_model_name_prefix_ = 'model'
    self.log_file_ = './training_log.txt'

  def get_num_time_points(self):
    return self.num_time_points_

  def __prepare_one_data(self, one_symbol_data, start_index):
    one_data_x = np.zeros(self.num_time_points_ + 1) # additional feature is time
    last_index = start_index + self.num_time_points_ - 1
    divider = one_symbol_data.data[last_index].open
    for i in range(start_index, last_index + 1):
      one_data_x[i - start_index] = (one_symbol_data.data[i].open - divider) / divider
    one_data_x[-1] = datetime_util.minute_diff(
      one_symbol_data.data[last_index].time_val, self.open_time_) / self.total_minutes_normalizer_

    one_data_y = 0
    for i in range(last_index + 1, len(one_symbol_data.data)):
      if one_symbol_data.data[i].time_val > self.close_time_:
        break
      if one_symbol_data.data[i].open > divider:
        val = (one_symbol_data.data[i].open - divider) / divider
        one_data_y = max(one_data_y, val)
    if self.is_classification_model_:
      if one_data_y > self.classifify_threshold_:
        one_data_y = 1.0
      else:
        one_data_y = 0.0
    return one_data_x, one_data_y

  def is_eligible_to_be_fed_into_network(self, one_symbol_data, current_index):
    """ Given current_index of time slot, return whether this current time on one symbol can be fed into NN
    :param one_symbol_data: one symbol stock data
    :param current_index: index of the current time point you want to check
    :return: True/False whether the data can be fed into NN
    """
    if len(one_symbol_data.data) < self.num_time_points_:
      return False

    if current_index < self.num_time_points_ - 1:
      return False

    if one_symbol_data.data[current_index - self.num_time_points_ + 1].time_val < self.open_time_:
      return False

    if one_symbol_data.data[current_index].time_val >= self.close_time_:
      return False

    return True

  def __prepare_data(self, start_date, end_date, sample_step):
    available_dates = self.dm_.get_all_available_subfolder()
    data_x, data_y = [], []
    current_day = start_date
    while True:
      if current_day > end_date:
        break

      if str(current_day) not in available_dates:
        current_day = datetime_util.increment_day(current_day, 1)
        continue

      print('Preparing day {0}'.format(current_day))
      self.dm_.load_one_day_data(current_day)
      symbol_list = self.dm_.get_symbol_list_for_a_day(current_day)
      for symbol in symbol_list:
        one_symbol_data = self.dm_.get_one_symbol_data(symbol)
        start_index = self.num_time_points_ - 1
        while True:
          if start_index >= len(one_symbol_data.data):
            break
          if not self.is_eligible_to_be_fed_into_network(one_symbol_data, start_index):
            start_index += sample_step
            continue
          one_data_x, one_data_y = self.__prepare_one_data(one_symbol_data, start_index - self.num_time_points_ + 1)
          data_x.append(one_data_x)
          data_y.append(one_data_y)
          start_index += sample_step
      current_day = datetime_util.increment_day(current_day, 1)
    return np.asarray(data_x), np.asarray(data_y)

  def __prepare_training_data(self):
    print ('Preparing training data ...')
    return self.__prepare_data(self.train_start_date_, self.train_end_date_, self.sample_step_training_)

  def __prepare_test_data(self):
    print ('Preparing testing data ...')
    return self.__prepare_data(self.test_start_date_, self.test_end_date_, self.sample_step_testing_)

  def init_for_serving(self):
    """ Initialize network and load saved model for serving
    :param model_path: file path of model
    :return:
    """
    self.input_feed_, y_label, self.prediction_, loss, train_step, accuracy, tp, fn, fp, tn = self.__create_network()
    self.prediction_ = tf.nn.softmax(self.prediction_)

  def compute_prob(self, one_symbol_data, current_index):
    """ Compute buying probability for one symbol data at current timepoint index. This function is supposed to be used
    in serving. TF session should be called outside for efficiency
    :param one_symbol_data: one stock symbol
    :param current_index: current timepoint index
    :return: the score for buying a stock
    """
    data_x = []
    one_data_x, one_data_y = self.__prepare_one_data(one_symbol_data, current_index - self.num_time_points_ + 1)
    data_x.append(one_data_x)
    data_x = np.asarray(data_x)
    predict_value = self.prediction_.eval(feed_dict={self.input_feed_: data_x})
    return predict_value[1]

  def __create_network(self):
    x = tf.placeholder(tf.float32, [None, self.architecture_[0]])

    # Define loss and optimizer
    if self.is_classification_model_:
      y_label = tf.placeholder(tf.int64, [None,])
    else:
      y_label = tf.placeholder(tf.float32, [None,])

    # Build the graph for the deep net
    if self.is_classification_model_:
      self.architecture_.append(2)
    else:
      self.architecture_.append(1)
    if self.is_classification_model_:
      y_prediction = SimpleFn2(x, self.architecture_)
    else:
      y_prediction = SimpleFn(x, self.num_time_points_, [128, 1])

    with tf.name_scope('loss'):
      if self.is_classification_model_:
        onehot_labels = tf.one_hot(indices=tf.cast(y_label, tf.int32), depth=2)
        loss = tf.losses.softmax_cross_entropy(
          onehot_labels=onehot_labels, logits=y_prediction)
      else:
        loss = tf.losses.mean_squared_error(
          labels=y_label, predictions=y_prediction)

      loss = tf.reduce_mean(loss)

    if self.is_classification_model_:
      with tf.name_scope('accuracy'):
        correct_prediction = tf.equal(tf.argmax(y_prediction, 1), y_label)
        correct_prediction = tf.cast(correct_prediction, tf.float32)
        y_label_cast = tf.cast(y_label, tf.float32)
        tp = correct_prediction * y_label_cast
        fn = (1 - correct_prediction) * y_label_cast
        fp = (1 - correct_prediction) * (1 - y_label_cast)
        tn = correct_prediction * (1 - y_label_cast)
        accuracy = tf.reduce_mean(correct_prediction)
        tp = tf.reduce_mean(tp)
        fn = tf.reduce_mean(fn)
        fp = tf.reduce_mean(fp)
        tn = tf.reduce_mean(tn)

    with tf.name_scope('adam_optimizer'):
      train_step = tf.train.AdamOptimizer(self.learning_rate_).minimize(loss)

    if self.is_classification_model_:
      return x, y_label, y_prediction, loss, train_step, accuracy, tp, fn, fp, tn
    else:
      return x, y_label, y_prediction, loss, train_step

  def __prepare_export_file(self):
    if not os.path.isdir(self.model_folder_):
      os.mkdir(self.model_folder_)
    model_index = 0
    model_name = self.output_model_name_prefix_
    if self.is_classification_model_:
      model_name += '_classification_'
    else:
      model_name += '_regression_'
    while True:
      model_path = os.path.join(self.model_folder_, model_name + str(model_index) + '.ckpt')
      if not os.path.isfile(model_path + '.index'):
        break
      model_index += 1
    return model_path

  def train_and_test(self):
    logging.basicConfig(filename = self.log_file_, level = logging.DEBUG)
    str_type = 'regression'
    if self.is_classification_model_:
      str_type = 'classification'
    message = 'New session of training {0} starts at {1} on {2}'.format(str_type, datetime_util.get_cur_time_int(),
                                                                        datetime_util.get_today())
    print (message)
    logging.info(message)
    train_x, train_y = self.__prepare_training_data()
    test_x, test_y = self.__prepare_test_data()

    num_samples = len(train_y)
    sample_index = range(num_samples)

    message = 'Total number of samples: train: {0}, test: {1}'.format(len(train_y), len(test_y))
    print(message)
    logging.info(message)
    if self.is_classification_model_:
      message = 'Number of positive in training: {0}, in testing: {1}'.format(np.sum(train_y == 1), np.sum(test_y == 1))
      print(message)
      logging.info(message)

    if self.is_classification_model_:
      x, y_label, y_prediction, loss, train_step, accuracy, tp, fn, fp, tn = self.__create_network()
    else:
      x, y_label, y_prediction, loss, train_step = self.__create_network()

    model_path = self.__prepare_export_file()   
    train_writer = tf.summary.FileWriter(self.model_folder_)
    train_writer.add_graph(tf.get_default_graph()) 
  
    with tf.Session() as sess:
      saver = tf.train.Saver()
      if self.load_previous_model_:
        prev_model_path = os.path.join(self.model_folder_, self.previous_model_ + '.ckpt')
        saver.restore(sess, prev_model_path)
        message = 'Load from previous model {0}'.format(prev_model_path)
        print(message)
        logging.info(message)
      else:
        sess.run(tf.global_variables_initializer())

      for i in range(self.num_epochs_):
        shuffle(sample_index)
        index = 0
        while index < num_samples:
          last_index = min(num_samples, index + self.batch_size_)
          batch_x = train_x[sample_index[index : last_index]]
          batch_y = train_y[sample_index[index : last_index]]          

          train_step.run(feed_dict={x: batch_x, y_label: batch_y})
          index += self.batch_size_
        if self.is_classification_model_:
          train_error = accuracy.eval(feed_dict={x: train_x, y_label: train_y})
          test_error = accuracy.eval(feed_dict={x: test_x, y_label: test_y})
          true_positive_train = tp.eval(feed_dict={x: train_x, y_label: train_y})
          false_negative_train = fn.eval(feed_dict={x: train_x, y_label: train_y})
          false_positive_train = fp.eval(feed_dict={x: train_x, y_label: train_y})
          true_negative_train = tn.eval(feed_dict={x: train_x, y_label: train_y})
          true_positive_test = tp.eval(feed_dict={x: test_x, y_label: test_y})
          false_negative_test = fn.eval(feed_dict={x: test_x, y_label: test_y})
          false_positive_test = fp.eval(feed_dict={x: test_x, y_label: test_y})
          true_negative_test = tn.eval(feed_dict={x: test_x, y_label: test_y})
        else:
          train_error = loss.eval(feed_dict={x: train_x, y_label: train_y})
          test_error = loss.eval(feed_dict={x: test_x, y_label: test_y})
        if self.is_classification_model_:
          message = 'Epoch {0}, train accuracy: {1}, test accuracy: {2}'.format(i, train_error, test_error)
        else:
          message = 'Epoch {0}, train RMSE: {1}, test RMSE: {2}'.format(i, np.sqrt(train_error), np.sqrt(test_error))
        print(message)
        logging.info(message)

        if self.is_classification_model_:
          message = 'Train: TP: {0:.3f}, FP: {1:.3f}; Test: TP: {2:.3f}, FP: {3:.3f}'.format(
            true_positive_train, false_positive_train, true_positive_test, false_positive_test)
          print(message)
          logging.info(message)
          message = 'Train: FN: {0:.3f}, TN: {1:.3f}; Test: FN: {2:.3f}, TN: {3:.3f}'.format(
            false_negative_train, true_negative_train, false_negative_test, true_negative_test)
          print(message)
          logging.info(message)

        save_path = saver.save(sess, model_path) # to restore, run saver.restore(sess, model_path)

