import numpy as np
import tensorflow as tf
from random import shuffle

import util.data_provider as data_provider
import util.datetime_util as datetime_util

def SimpleFn(x):
  """ A simple fully connected network with regression output
  :param x: input tensor
  :return: h_fc2: output tensor of regression
  """
  with tf.name_scope('fc1'):
    W_fc1 = weight_variable([100, 256])
    b_fc1 = bias_variable([256])
    h_fc1 = tf.nn.relu(tf.matmul(x, W_fc1) + b_fc1)

  with tf.name_scope('fc2'):
    W_fc2 = weight_variable([256, 1])
    b_fc2 = bias_variable([1])
    h_fc2 = tf.nn.relu(tf.matmul(h_fc1, W_fc2) + b_fc2)

  return tf.squeeze(h_fc2)

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
    self.sample_interval_ = 10

    # Batch size during training
    self.batch_size_ = 50

    # Number of epochs for training
    self.num_epochs_ = 50

    # How many epochs to print once
    self.num_print_epochs_ = 5

    # place to save the model
    self.model_path_ = './model.ckpt'

  def train_and_test(self):
    self.__train()
    self.__test()

  def __prepare_one_data(self, one_symbol_data, start_index):
    one_data_x = np.zeros(self.num_time_points_)
    last_index = start_index + self.num_time_points_ - 1
    divider = one_symbol_data.data[last_index].open
    for i in range(start_index, last_index + 1):
      one_data_x[i - start_index] = one_symbol_data.data[i].open / divider

    one_data_y = 0
    for i in range(last_index + 1, len(one_symbol_data.data)):
      if one_symbol_data.data[i].open > divider:
        val = (one_symbol_data.data[i].open - divider) / divider
        one_data_y = max(one_data_y, val)
    return one_data_x, one_data_y

  def __prepare_training_data(self):
    print ('Preparing training data ...')
    available_dates = self.dm_.get_all_available_subfolder()
    train_x, train_y = [], []
    current_day = self.train_start_date_
    while True:
      if current_day > self.train_end_date_:
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
          train_x.append(one_data_x)
          train_y.append(one_data_y)
          start_index += self.sample_interval_
      current_day = datetime_util.increment_day(current_day, 1)
    return np.asarray(train_x), np.asarray(train_y)

  def __prepare_test_data(self):
    available_dates = self.dm_.get_all_available_subfolder()
    test_x, test_y = [], []
    current_day = self.test_start_date_
    while True:
      if current_day > self.test_end_date_:
        break

      if str(current_day) not in available_dates:
        current_day = datetime_util.increment_day(current_day, 1)
        continue

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
          test_x.append(one_data_x)
          test_y.append(one_data_y)
          start_index += self.sample_interval_
      current_day = datetime_util.increment_day(current_day, 1)

    return np.asarray(test_x), np.asarray(test_y)

  def __create_network(self):
    x = tf.placeholder(tf.float32, [None, self.num_time_points_])

    # Define loss and optimizer
    y_regress_label = tf.placeholder(tf.float32, [None,])

    # Build the graph for the deep net
    y_regress_prediction = SimpleFn(x)

    with tf.name_scope('loss'):
      squared_loss = tf.losses.mean_squared_error(
        labels=y_regress_label, predictions=y_regress_prediction)

      squared_loss = tf.reduce_mean(squared_loss)

    with tf.name_scope('adam_optimizer'):
      train_step = tf.train.AdamOptimizer(1e-4).minimize(squared_loss)

    return x, y_regress_label, y_regress_prediction, squared_loss, train_step

  def __train(self):
    print ('Start training ...')
    train_x, train_y = self.__prepare_training_data()
    num_samples = len(train_y)

    print('Data preparation complete! Total number of samples: {0}'.format(num_samples))

    sample_index = range(num_samples)

    x, y_regress_label, y_regress_prediction, squared_loss, train_step = self.__create_network()

    with tf.Session() as sess:
      saver = tf.train.Saver()
      sess.run(tf.global_variables_initializer())
      for i in range(self.num_epochs_):
        shuffle(sample_index)
        index = 0
        while index < num_samples:
          last_index = min(num_samples, index + self.batch_size_)
          batch_x = train_x[sample_index[index : last_index]]
          batch_y = train_y[sample_index[index : last_index]]

          regress_error = squared_loss.eval(feed_dict={
             x: batch_x, y_regress_label: batch_y})
          print('Epoch {0},  regress error {1}'.format(i, regress_error))

          train_step.run(feed_dict={x: batch_x, y_regress_label: batch_y})
          index += self.batch_size_

      save_path = saver.save(sess, self.model_path_)
      print('Model saved in path: {0}'.format(save_path))

  def __test(self):
    test_x, test_y = self.__prepare_test_data()
    x, y_regress_label, y_regress_prediction, squared_loss, train_step = self.__create_network()
    with tf.Session() as sess:
      saver = tf.train.Saver()
      sess.run(tf.global_variables_initializer())
      saver.restore(sess, self.model_path_)
      regress_error = squared_loss.eval(feed_dict={
             x: test_x, y_regress_label: test_y})

    print('Test regress error {0}'.format(regress_error))

