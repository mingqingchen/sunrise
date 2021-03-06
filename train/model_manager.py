import numpy as np
import tensorflow as tf
import os
from random import shuffle
import logging

import util.data_provider as data_provider
import util.datetime_util as datetime_util
import proto.nn_train_param_pb2 as nn_train_param_pb2

def SimpleFn(x, x_additional, architecture = [100, 1, 32, 32, 1], context = 'buy_'):
  """ A simple fully connected network with regression output
  :param x: input tensor
  :return: h_fc2: output tensor of regression
  """
  with tf.name_scope(context + 'fc1'):
    W_fc1 = weight_variable([architecture[0], architecture[2]])
    b_fc1 = bias_variable([architecture[2]])
    h_fc1 = tf.nn.relu(tf.matmul(x, W_fc1) + b_fc1)

  with tf.name_scope(context + 'fc2'):
    W_fc2 = weight_variable([architecture[2] + architecture[1], architecture[3]])
    b_fc2 = bias_variable([architecture[3]])
    h_fc1_concat = tf.concat([h_fc1, x_additional], 1)
    h_fc2 = tf.nn.relu(tf.matmul(h_fc1_concat, W_fc2) + b_fc2)

  with tf.name_scope(context + 'fc3'):
    W_fc3 = weight_variable([architecture[3], architecture[4]])
    b_fc3 = bias_variable([architecture[4]])
    h_fc3 = tf.nn.relu(tf.matmul(h_fc2, W_fc3) + b_fc3)

  return tf.squeeze(h_fc3)

# default number of parameters:
def SimpleCnn(x, x_additional, architecture = [100, 1, 16, 32, 16, 8, 1], context = 'buy_'):
  # padding could be 'SAME' or 'VALID'
  x_reshape = tf.reshape(x, [-1, architecture[0], 1])
  x_additional_reshape = tf.reshape(x_additional, [-1, architecture[1]])
  conv_size = 5
  with tf.name_scope(context + 'cnn1'):
    W_conv1 = weight_variable([conv_size, 1, architecture[2]])
    b_conv1 = bias_variable([architecture[2]])
    h_conv1 = tf.nn.relu(tf.nn.conv1d(x_reshape, W_conv1, stride = 1, padding = 'VALID') + b_conv1)
    h_pool1 = tf.layers.max_pooling1d(h_conv1, pool_size = 2, strides = 2)
  with tf.name_scope(context + 'cnn2'):
    W_conv2 = weight_variable([conv_size, architecture[2], architecture[3]])
    b_conv2 = bias_variable([architecture[3]])
    h_conv2 = tf.nn.relu(tf.nn.conv1d(h_pool1, W_conv2, stride = 1, padding = 'VALID') + b_conv2)
    h_pool2 = tf.layers.max_pooling1d(h_conv2, pool_size = 2, strides = 2)
  with tf.name_scope(context + 'cnn3'):
    W_conv3 = weight_variable([conv_size, architecture[3], architecture[4]])
    b_conv3 = bias_variable([architecture[4]])
    h_conv3 = tf.nn.relu(tf.nn.conv1d(h_pool2, W_conv3, stride = 1, padding = 'VALID') + b_conv3)
    h_pool3 = tf.layers.max_pooling1d(h_conv3, pool_size = 2, strides = 2)
  with tf.name_scope(context + 'fc1'):
    fc_input_dim = np.prod(h_pool3.get_shape().as_list()[1:])
    W_fc1 = weight_variable([fc_input_dim + architecture[1], architecture[5]])
    b_fc1 = bias_variable([architecture[5]])
    h_pool3_flat = tf.reshape(h_pool3, [-1, fc_input_dim])
    h_pool3_concat = tf.concat([h_pool3_flat, x_additional_reshape], 1)
    h_fc1 = tf.nn.relu(tf.matmul(h_pool3_concat, W_fc1) + b_fc1)
  with tf.name_scope(context + 'fc2'):
    W_fc2 = weight_variable([architecture[5], architecture[6]])
    b_fc2 = bias_variable([architecture[6]])
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
  def set_training_data_folder(self, data_folder):
    self.data_folder_ = data_folder

  def set_training_use_eligible_list(self, use_eligible_list):
    self.use_eligible_list_ = use_eligible_list

  def set_training_dates(self, start_date, end_date):
    self.train_start_date_ = start_date
    self.train_end_date_ = end_date

  def set_test_dates(self, start_date, end_date):
    self.test_start_date_ = start_date
    self.test_end_date_ = end_date

class FixedNumTimePointsModelManager(ModelManager):
  def __init__(self, params):
    self.num_time_points_ = params.num_time_points
    self.upper_time_point_limit_ = params.upper_time_point_limit
    self.open_time_ = params.open_time
    self.close_time_ = params.close_time
    self.total_minutes_normalizer_ = params.total_minutes_normalizer

    self.sample_step_training_ = params.sample_step_training
    self.sample_step_testing_ = params.sample_step_testing

    self.learning_rate_ = params.learning_rate
    self.num_epochs_ = params.num_epochs
    self.batch_size_ = params.batch_size

    self.use_cnn_ = params.use_cnn
    self.architecture_ = [self.num_time_points_, 1]
    for num_hidden_nodes in params.architecture:
      self.architecture_.append(num_hidden_nodes)

    self.type_ = params.type
    self.classifify_threshold_ = params.classify_threshold

    self.load_previous_model_ = params.load_previous_model
    self.previous_model_ = params.previous_model

    self.model_folder_ = params.model_folder
    self.output_model_name_prefix_ = params.output_model_name_prefix
    self.log_file_ = params.log_file

    self.local_maximal_window_size_ = params.local_maximal_window_size;
    self.local_maximal_margin_ = params.local_maximal_margin;

    self.use_relative_price_percentage_to_buy_ = params.use_relative_price_percentage_to_buy
    self.relative_price_percentage_ = params.relative_price_percentage

    self.dense_ratio_ = params.dense_ratio
    self.average_cash_flow_per_min_ = params.average_cash_flow_per_min

    self.use_pre_market_data_ = params.use_pre_market_data

  def get_num_time_points(self):
    return self.num_time_points_

  def __prepare_one_data_x(self, one_symbol_data, start_index):
    one_data_x = np.zeros(self.num_time_points_)
    one_data_x_extra = np.zeros(1) # additional feature is time
    last_index = start_index + self.num_time_points_ - 1
    divider = one_symbol_data.data[last_index].open
    for i in range(start_index, last_index + 1):
      one_data_x[i - start_index] = (one_symbol_data.data[i].open - divider) / divider
    one_data_x_extra[0] = datetime_util.minute_diff(
      one_symbol_data.data[last_index].time_val, self.open_time_) / self.total_minutes_normalizer_
    return one_data_x, one_data_x_extra

  def __prepare_one_data_y(self, one_symbol_data, start_index):
    last_index = start_index + self.num_time_points_ - 1
    divider = one_symbol_data.data[last_index].open
    if self.type_ == nn_train_param_pb2.TrainingParams.CLASSIFY_FUTURE_HIGHEST_PRICE:
      one_data_y = 0
      for i in range(last_index + 1, len(one_symbol_data.data)):
        if one_symbol_data.data[i].time_val > self.close_time_:
          break
        if one_symbol_data.data[i].open > divider:
          val = (one_symbol_data.data[i].open - divider) / divider
          one_data_y = max(one_data_y, val)
      if one_data_y > self.classifify_threshold_:
        one_data_y = 1.0
      else:
        one_data_y = 0.0
    elif self.type_ == nn_train_param_pb2.TrainingParams.CLASSIFY_BUY_SELL_TIME:
      half_window_size = (self.local_maximal_window_size_ - 1) / 2
      i_start = max(0, last_index - half_window_size * 2)
      i_end = min(len(one_symbol_data.data), last_index + self.local_maximal_window_size_)
      this_price = one_symbol_data.data[last_index].open
      maximal_price, maximal_index = this_price, last_index
      one_data_y = 0
      for i in range(i_start, i_end):
        if one_symbol_data.data[i].open > maximal_price:
          maximal_price = one_symbol_data.data[i].open
          maximal_index = last_index
      if abs(maximal_index - last_index) <= half_window_size:
        if this_price > maximal_price * (1 - self.local_maximal_margin_):
          one_data_y = 1.0
    return one_data_y

  def __prepare_one_data(self, one_symbol_data, start_index):
    one_data_x, one_data_x_extra = self.__prepare_one_data_x(one_symbol_data, start_index)
    one_data_y = self.__prepare_one_data_y(one_symbol_data, start_index)
    return one_data_x, one_data_x_extra, one_data_y

  def is_eligible_to_be_fed_into_network(self, one_symbol_data, current_index):
    """ Given current_index of time slot, return whether this current time on one symbol can be fed into NN
    :param one_symbol_data: one symbol stock data
    :param current_index: index of the current time point you want to check
    :return: True/False whether the data can be fed into NN
    """
    if len(one_symbol_data.data) < self.num_time_points_:
      return False

    if current_index >= self.upper_time_point_limit_:
      return False

    if current_index < self.num_time_points_ - 1:
      return False

    if not self.use_pre_market_data_:
      if one_symbol_data.data[current_index - self.num_time_points_ + 1].time_val < self.open_time_:
        return False

    if one_symbol_data.data[current_index].time_val >= self.close_time_:
      return False

    max_price, min_price = one_symbol_data.data[0].open, one_symbol_data.data[0].open
    cash_flow = 0.0
    num_timepoint_after_open = 0
    for i in range(0, current_index):
      if self.type_ == nn_train_param_pb2.TrainingParams.CLASSIFY_FUTURE_HIGHEST_PRICE and self.use_relative_price_percentage_to_buy_:
        max_price = max(max_price, one_symbol_data.data[i].open)
        min_price = min(min_price, one_symbol_data.data[i].open)
      if one_symbol_data.data[i].time_val > self.open_time_:
        cash_flow += one_symbol_data.data[i].open * one_symbol_data.data[i].volume
        num_timepoint_after_open += 1

    num_min = datetime_util.minute_diff(self.open_time_, one_symbol_data.data[current_index].time_val)
    if num_min * self.dense_ratio_ > num_timepoint_after_open:
      return False

    if num_timepoint_after_open * self.average_cash_flow_per_min_ > cash_flow:
      return False

    if self.type_ == nn_train_param_pb2.TrainingParams.CLASSIFY_FUTURE_HIGHEST_PRICE and self.use_relative_price_percentage_to_buy_:
      threshold = (max_price - min_price) * self.relative_price_percentage_ + min_price
      if one_symbol_data.data[current_index].open > threshold:
        return False



    return True

  def __prepare_data(self, start_date, end_date, sample_step):
    available_dates = self.dm_.get_all_available_dates()
    data_x, data_x_extra, data_y = [], [], []
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

          if start_index >= self.upper_time_point_limit_:
            break

          if not self.is_eligible_to_be_fed_into_network(one_symbol_data, start_index):
            start_index += sample_step
            continue
          one_data_x, one_data_x_extra, one_data_y = self.__prepare_one_data(one_symbol_data, start_index - self.num_time_points_ + 1)
          data_x.append(one_data_x)
          data_x_extra.append(one_data_x_extra)
          data_y.append(one_data_y)
          start_index += sample_step
      current_day = datetime_util.increment_day(current_day, 1)
    return np.asarray(data_x), np.asarray(data_x_extra), np.asarray(data_y)

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
    self.input_feed_, self.input_feed_extra_, y_label, self.prediction_, loss, train_step, accuracy, tp, fn, fp, tn = self.__create_network()
    self.prediction_ = tf.nn.softmax(self.prediction_)

  def compute_prob(self, one_symbol_data, current_index):
    """ Compute buying probability for one symbol data at current timepoint index. This function is supposed to be used
    in serving. TF session should be called outside for efficiency
    :param one_symbol_data: one stock symbol
    :param current_index: current timepoint index
    :return: the score for buying a stock
    """
    data_x, data_x_extra = [], []
    one_data_x, one_data_x_extra, one_data_y = self.__prepare_one_data(one_symbol_data, current_index - self.num_time_points_ + 1)
    data_x.append(one_data_x)
    data_x_extra.append(one_data_x_extra)
    data_x = np.asarray(data_x)
    data_x_extra = np.asarray(data_x_extra)
    predict_value = self.prediction_.eval(feed_dict={self.input_feed_: data_x, self.input_feed_extra_: data_x_extra})
    return predict_value[1]

  def __create_network(self):
    x = tf.placeholder(tf.float32, [None, self.architecture_[0]])
    x_additional = tf.placeholder(tf.float32, [None, self.architecture_[1]])

    # Define loss and optimizer
    if self.type_ != nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
      y_label = tf.placeholder(tf.int64, [None,])
    else:
      y_label = tf.placeholder(tf.float32, [None,])

    # Build the graph for the deep net
    if self.type_ != nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
      self.architecture_.append(2)
    else:
      self.architecture_.append(1)

    if self.type_ != nn_train_param_pb2.TrainingParams.CLASSIFY_BUY_SELL_TIME:
      context = 'buy_'
    else:
      context = 'sell_'

    if self.use_cnn_:
      y_prediction = SimpleCnn(x, x_additional, self.architecture_, context=context)
    else:
      y_prediction = SimpleFn(x, x_additional, self.architecture_, context = context)
    
    with tf.name_scope('loss'):
      if self.type_ == nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
        loss = tf.losses.mean_squared_error(
          labels=y_label, predictions=y_prediction)      
      else:
        onehot_labels = tf.one_hot(indices=tf.cast(y_label, tf.int32), depth=2)
        loss = tf.losses.softmax_cross_entropy(
          onehot_labels=onehot_labels, logits=y_prediction)

      loss = tf.reduce_mean(loss)

    if self.type_ != nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
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

    if self.type_ != nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
      return x, x_additional, y_label, y_prediction, loss, train_step, accuracy, tp, fn, fp, tn
    else:
      return x, x_additional, y_label, y_prediction, loss, train_step

  def __prepare_export_file(self):
    if not os.path.isdir(self.model_folder_):
      os.mkdir(self.model_folder_)
    model_index = 0
    model_name = self.output_model_name_prefix_
    if self.type_ != nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
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
    self.dm_ = data_provider.DataProvider(self.data_folder_, self.use_eligible_list_)
    logging.basicConfig(filename = self.log_file_, level = logging.DEBUG)
    str_type = 'regression'
    if self.type_ != nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
      str_type = 'classification'
    message = 'New session of training {0} starts at {1} on {2}'.format(str_type, datetime_util.get_cur_time_int(),
                                                                        datetime_util.get_today())
    print (message)
    logging.info(message)
    train_x, train_x_extra, train_y = self.__prepare_training_data()
    test_x, test_x_extra, test_y = self.__prepare_test_data()

    num_samples = len(train_y)
    sample_index = range(num_samples)

    message = 'Total number of samples: train: {0}, test: {1}'.format(len(train_y), len(test_y))
    print(message)
    logging.info(message)
    if self.type_ != nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
      num_positive_train = np.sum(train_y == 1)
      num_positive_test = np.sum(test_y == 1)
      positive_ratio_train = float(num_positive_train) / len(train_y)
      positive_ratio_test = float(num_positive_test) / len(test_y)
      message = 'Number of positive in training: {0}, in testing: {1}'.format(num_positive_train, num_positive_test)
      print(message)
      logging.info(message)
      message = 'Ratio of positive in training: {0}, in testing: {1}'.format(positive_ratio_train, positive_ratio_test)
      print(message)
      logging.info(message)

    if self.type_ != nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
      x, x_additional, y_label, y_prediction, loss, train_step, accuracy, tp, fn, fp, tn = self.__create_network()
    else:
      x, x_additional, y_label, y_prediction, loss, train_step = self.__create_network()

    for variable in tf.trainable_variables():
      print variable

    model_path = self.__prepare_export_file()   
    train_writer = tf.summary.FileWriter(self.model_folder_)
    train_writer.add_graph(tf.get_default_graph()) 
  
    with tf.Session() as sess:
      sess.run(tf.global_variables_initializer())
      saver = tf.train.Saver(var_list=tf.trainable_variables())
      if self.load_previous_model_:
        prev_model_path = os.path.join(self.model_folder_, self.previous_model_ + '.ckpt')
        saver.restore(sess, prev_model_path)
        message = 'Load from previous model {0}'.format(prev_model_path)
        print(message)
        logging.info(message)

      for i in range(self.num_epochs_):
        shuffle(sample_index)
        index = 0

        while index < num_samples:
          last_index = min(num_samples, index + self.batch_size_)
          batch_x = train_x[sample_index[index : last_index]]
          batch_x_extra = train_x_extra[sample_index[index : last_index]]
          batch_y = train_y[sample_index[index : last_index]]          

          train_step.run(feed_dict={x: batch_x, x_additional: batch_x_extra, y_label: batch_y})
          index += self.batch_size_

        feed_dict_train = {x: train_x, x_additional: train_x_extra, y_label: train_y}
        feed_dict_test = {x: test_x, x_additional: test_x_extra, y_label: test_y}

        if self.type_ != nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
          train_error = accuracy.eval(feed_dict = feed_dict_train)
          test_error = accuracy.eval(feed_dict = feed_dict_test)
          true_positive_train = tp.eval(feed_dict = feed_dict_train)
          false_negative_train = fn.eval(feed_dict = feed_dict_train)
          false_positive_train = fp.eval(feed_dict = feed_dict_train)
          true_negative_train = tn.eval(feed_dict = feed_dict_train)
          true_positive_test = tp.eval(feed_dict = feed_dict_test)
          false_negative_test = fn.eval(feed_dict = feed_dict_test)
          false_positive_test = fp.eval(feed_dict = feed_dict_test)
          true_negative_test = tn.eval(feed_dict = feed_dict_test)
        else:
          train_error = loss.eval(feed_dict = feed_dict_train)
          test_error = loss.eval(feed_dict = feed_dict_test)
        if self.type_ != nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
          message = 'Epoch {0}, train accuracy: {1}, test accuracy: {2}'.format(i, train_error, test_error)
        else:
          message = 'Epoch {0}, train RMSE: {1}, test RMSE: {2}'.format(i, np.sqrt(train_error), np.sqrt(test_error))
        print(message)
        logging.info(message)

        if self.type_ != nn_train_param_pb2.TrainingParams.REGRESS_FUTURE_HIGHEST_PRICE:
          message = 'Train: TP: {0:.3f}, FP: {1:.3f}; Test: TP: {2:.3f}, FP: {3:.3f}'.format(
            true_positive_train, false_positive_train, true_positive_test, false_positive_test)
          print(message)
          logging.info(message)
          message = 'Train: FN: {0:.3f}, TN: {1:.3f}; Test: FN: {2:.3f}, TN: {3:.3f}'.format(
            false_negative_train, true_negative_train, false_negative_test, true_negative_test)
          print(message)
          logging.info(message)

        saver.save(sess, model_path) # to restore, run saver.restore(sess, model_path)
        print('model saved to: {0}'.format(model_path))

