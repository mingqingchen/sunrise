import numpy as np
import tensorflow as tf
import os
from random import shuffle
import logging

import util.data_provider as data_provider
import util.datetime_util as datetime_util

def SimpleFn(x, input_dimension, hidden_dimension = 32):
  """ A simple fully connected network with regression output
  :param x: input tensor
  :return: h_fc2: output tensor of regression
  """
  with tf.name_scope('fc1'):
    W_fc1 = weight_variable([input_dimension, hidden_dimension])
    b_fc1 = bias_variable([hidden_dimension])
    h_fc1 = tf.nn.relu(tf.matmul(x, W_fc1) + b_fc1)

  with tf.name_scope('fc2'):
    W_fc2 = weight_variable([hidden_dimension, 1])
    b_fc2 = bias_variable([1])
    h_fc2 = tf.nn.relu(tf.matmul(h_fc1, W_fc2) + b_fc2)

  return tf.squeeze(h_fc2)

def SimpleFn2(x, input_dimension, hidden_dimension = [128, 16]):
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

  with tf.name_scope('fc3'):
    W_fc3 = weight_variable([hidden_dimension[1], 1])
    b_fc3 = bias_variable([1])
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

    # After this time, we won't consider buying stocks. I.e. no data will be used for training
    self.latest_time_ = 1100

    # Timepoint interval to step to prepare training data
    self.sample_interval_ = 2

    # Parameters related to deep learning
    self.batch_size_ = 50
    self.learning_rate_ = 1e-5
    self.num_epochs_ = 50

    # Parameters of simple FN
    self.hidden_nodes_ = 32

    # whether the training uses previous model as a starter
    self.load_previous_model_ = False
    self.previous_model_ = 'model1'

    # place to save the model
    self.model_folder_ = './model/'
    self.output_model_name_prefix_ = 'model'
    self.log_file_ = './training_log.txt'

  def __prepare_one_data(self, one_symbol_data, start_index):
    one_data_x = np.zeros(self.num_time_points_)
    last_index = start_index + self.num_time_points_ - 1
    divider = one_symbol_data.data[last_index].open
    for i in range(start_index, last_index + 1):
      one_data_x[i - start_index] = (one_symbol_data.data[i].open - divider) / divider

    one_data_y = 0
    for i in range(last_index + 1, len(one_symbol_data.data)):
      if one_symbol_data.data[i].open > divider:
        val = (one_symbol_data.data[i].open - divider) / divider
        one_data_y = max(one_data_y, val)
    return one_data_x, one_data_y

  def __prepare_data(self, start_date, end_date):
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
        start_index = 0
        while True:
          while True:
            if start_index > len(one_symbol_data.data):
              break
            if (one_symbol_data.data[start_index].time_val >= self.open_time_):
              break
            start_index += 1

          if len(one_symbol_data.data) < start_index + self.num_time_points_:
            break

          if one_symbol_data.data[start_index + self.num_time_points_ - 1].time_val > self.latest_time_:
            break
          one_data_x, one_data_y = self.__prepare_one_data(one_symbol_data, start_index)
          data_x.append(one_data_x)
          data_y.append(one_data_y)
          start_index += self.sample_interval_
      current_day = datetime_util.increment_day(current_day, 1)
    return np.asarray(data_x), np.asarray(data_y)

  def __prepare_training_data(self):
    print ('Preparing training data ...')
    return self.__prepare_data(self.train_start_date_, self.train_end_date_)

  def __prepare_test_data(self):
    print ('Preparing testing data ...')
    return self.__prepare_data(self.test_start_date_, self.test_end_date_)

  def __create_network(self):
    x = tf.placeholder(tf.float32, [None, self.num_time_points_])

    # Define loss and optimizer
    y_regress_label = tf.placeholder(tf.float32, [None,])

    # Build the graph for the deep net
    y_regress_prediction = SimpleFn2(x, self.num_time_points_)
    #y_regress_prediction = SimpleCnn(x)

    with tf.name_scope('loss'):
      squared_loss = tf.losses.mean_squared_error(
        labels=y_regress_label, predictions=y_regress_prediction)

      squared_loss = tf.reduce_mean(squared_loss)

    with tf.name_scope('adam_optimizer'):
      train_step = tf.train.AdamOptimizer(self.learning_rate_).minimize(squared_loss)

    return x, y_regress_label, y_regress_prediction, squared_loss, train_step

  def __prepare_export_file(self):
    if not os.path.isdir(self.model_folder_):
      os.mkdir(self.model_folder_)
    model_index = 0
    while True:
      model_path = os.path.join(self.model_folder_, self.output_model_name_prefix_ + str(model_index) + '.ckpt')
      if not os.path.isfile(model_path + '.index'):
        break
      model_index += 1
    return model_path

  def train_and_test(self):
    logging.basicConfig(filename = self.log_file_, level = logging.DEBUG)
    message = 'New session of training starts at {0} on {1}'.format(datetime_util.get_cur_time_int(), datetime_util.get_today())
    print (message)
    logging.info(message)
    train_x, train_y = self.__prepare_training_data()
    test_x, test_y = self.__prepare_test_data()
    num_samples = len(train_y)

    message = 'Total number of samples: train: {0}, test: {1}'.format(len(train_y), len(test_y))
    print(message)
    logging.info(message)

    sample_index = range(num_samples)

    x, y_regress_label, y_regress_prediction, squared_loss, train_step = self.__create_network()

    model_path = self.__prepare_export_file()   
    train_writer = tf.summary.FileWriter(self.log_file_)
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

          train_step.run(feed_dict={x: batch_x, y_regress_label: batch_y})
          index += self.batch_size_
        train_regress_error = squared_loss.eval(feed_dict={
             x: train_x, y_regress_label: train_y})
        test_regress_error = squared_loss.eval(feed_dict={
             x: test_x, y_regress_label: test_y})
        message = 'Epoch {0}, train RMSE: {1}, test RMSE: {2}'.format(i, np.sqrt(train_regress_error), np.sqrt(test_regress_error))
        print(message)
        logging.info(message)

        save_path = saver.save(sess, model_path) # to restore, run saver.restore(sess, model_path)
        message = 'Model saved in path: {0}'.format(save_path)
        print(message)
        logging.info(message)

