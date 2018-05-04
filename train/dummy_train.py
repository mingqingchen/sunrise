# Disable linter warnings to maintain consistency with tutorial.
# pylint: disable=invalid-name
# pylint: disable=g-bad-import-order

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys
import tempfile
import math
import random
import numpy as np

from tensorflow.examples.tutorials.mnist import input_data

import tensorflow as tf

FLAGS = None

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

  return h_fc2

def MultiOutputFn(x):
  """ A fully connected network containing both regression and classification output
  :param x: input tensor
  :return:
    h_fc2: output tensor of regression
    h_fc3: output tensor of classification
  """
  with tf.name_scope('fc1'):
    W_fc1 = weight_variable([100, 256])
    b_fc1 = bias_variable([256])
    h_fc1 = tf.nn.relu(tf.matmul(x, W_fc1) + b_fc1)

  with tf.name_scope('fc2'):
    W_fc2 = weight_variable([256, 1])
    b_fc2 = bias_variable([1])
    h_fc2 = tf.nn.relu(tf.matmul(h_fc1, W_fc2) + b_fc2)

  with tf.name_scope('fc3'):
    W_fc3 = weight_variable([256, 2])
    b_fc3 = bias_variable([2])
    h_fc3 = tf.squeeze(tf.nn.relu(tf.matmul(h_fc1, W_fc3) + b_fc3))
  return h_fc2, h_fc3

def SimpleCnn(x):
  """ A simple 1D CNN.
  :param x: input tensor
  :return: h_fc2: regression output tensor
  """
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
    W_fc1 = weight_variable([36, 16])
    b_fc1 = bias_variable([16])
    h_conv3_flat = tf.reshape(h_conv3, [-1, 36])
    h_fc1 = tf.nn.relu(tf.matmul(h_conv3_flat, W_fc1) + b_fc1)
  with tf.name_scope('fc2'):
    W_fc2 = weight_variable([16, 1])
    b_fc2 = bias_variable([1])
    h_fc2 = tf.nn.relu(tf.matmul(h_fc1, W_fc2) + b_fc2)

  return h_fc2


def deepnn(x):
  """deepnn builds the graph for a deep net for classifying digits.

  Args:
    x: an input tensor with the dimensions (N_examples, 784), where 784 is the
    number of pixels in a standard MNIST image.

  Returns:
    A tuple (y, keep_prob). y is a tensor of shape (N_examples, 10), with values
    equal to the logits of classifying the digit into one of 10 classes (the
    digits 0-9). keep_prob is a scalar placeholder for the probability of
    dropout.
  """
  # Reshape to use within a convolutional neural net.
  # Last dimension is for "features" - there is only one here, since images are
  # grayscale -- it would be 3 for an RGB image, 4 for RGBA, etc.
  with tf.name_scope('reshape'):
    x_image = tf.reshape(x, [-1, 28, 28, 1])

  # First convolutional layer - maps one grayscale image to 32 feature maps.
  with tf.name_scope('conv1'):
    W_conv1 = weight_variable([5, 5, 1, 32])
    b_conv1 = bias_variable([32])
    h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)

  # Pooling layer - downsamples by 2X.
  with tf.name_scope('pool1'):
    h_pool1 = max_pool_2x2(h_conv1)

  # Second convolutional layer -- maps 32 feature maps to 64.
  with tf.name_scope('conv2'):
    W_conv2 = weight_variable([5, 5, 32, 64])
    b_conv2 = bias_variable([64])
    h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)

  # Second pooling layer.
  with tf.name_scope('pool2'):
    h_pool2 = max_pool_2x2(h_conv2)

  # Fully connected layer 1 -- after 2 round of downsampling, our 28x28 image
  # is down to 7x7x64 feature maps -- maps this to 1024 features.
  with tf.name_scope('fc1'):
    W_fc1 = weight_variable([7 * 7 * 64, 1024])
    b_fc1 = bias_variable([1024])

    h_pool2_flat = tf.reshape(h_pool2, [-1, 7 * 7 * 64])
    h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

  # Dropout - controls the complexity of the model, prevents co-adaptation of
  # features.
  with tf.name_scope('dropout'):
    keep_prob = tf.placeholder(tf.float32)
    h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

  # Map the 1024 features to 10 classes, one for each digit
  with tf.name_scope('fc2'):
    W_fc2 = weight_variable([1024, 10])
    b_fc2 = bias_variable([10])

    y_conv = tf.matmul(h_fc1_drop, W_fc2) + b_fc2
  return y_conv, keep_prob


def conv2d(x, W):
  """conv2d returns a 2d convolution layer with full stride."""
  return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')


def max_pool_2x2(x):
  """max_pool_2x2 downsamples a feature map by 2X."""
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

def generate_dummy_data():
  num_train_sample = 10000
  num_test_sample = 100
  num_x_dim = 100

  random.seed(None)

  # generate training data
  index = np.asarray(range(0, num_x_dim))
  train_x = np.zeros([num_train_sample, num_x_dim])
  train_regress_y = np.zeros([num_train_sample, 1])
  train_classify_y = np.zeros([num_train_sample, 1], 'uint8')
  test_x = np.zeros([num_test_sample, num_x_dim])
  test_regress_y = np.zeros([num_test_sample, 1])
  test_classify_y = np.zeros([num_test_sample, 1], 'uint8')

  for i in range(num_train_sample):
    y = random.random()
    x = np.sin(index * y)
    train_x[i, :] = x
    train_regress_y[i, 0] = y
    if y > 0.5:
      train_classify_y[i, 0] = 1
    else:
      train_classify_y[i, 0] = 0
  for i in range(num_test_sample):
    y = random.random()
    x = np.sin(index * y)
    test_x[i, :] = x
    test_regress_y[i, 0] = y
    if y > 0.5:
      test_classify_y[i, 0] = 1
    else:
      test_classify_y[i, 0] = 0
  return train_x, train_regress_y, train_classify_y, test_x, test_regress_y, test_classify_y

def train_dummy():
  classify_weight = 1.0

  train_x, train_regress_y, train_classify_y, test_x, test_regress_y, test_classify_y = generate_dummy_data()
  x = tf.placeholder(tf.float32, [None, 100])

  # Define loss and optimizer
  y_regress_label = tf.placeholder(tf.float32, [None, 1])
  y_classify_label = tf.placeholder(tf.int64, [None, 1])

  # Build the graph for the deep net
  y_regress_prediction, y_classify_prediction = SimpleFn(x)
  #y_prediction = SimpleCnn(x)

  with tf.name_scope('loss'):
    squared_loss = tf.losses.mean_squared_error(
        labels=y_regress_label, predictions=y_regress_prediction)
    onehot_labels = tf.one_hot(indices=tf.cast(y_classify_label, tf.int32), depth=2)
    cross_entropy = tf.losses.softmax_cross_entropy(
        onehot_labels=onehot_labels, logits=y_classify_prediction)

    squared_loss = tf.reduce_mean(squared_loss)
    cross_entropy = tf.reduce_mean(cross_entropy)
    total_loss = squared_loss + classify_weight * cross_entropy

  with tf.name_scope('adam_optimizer'):
    train_step = tf.train.AdamOptimizer(1e-4).minimize(total_loss)

  graph_location = tempfile.mkdtemp()
  print('Saving graph to: %s' % graph_location)
  train_writer = tf.summary.FileWriter(graph_location)
  train_writer.add_graph(tf.get_default_graph())

  index = 0
  batch_size = 50

  use_pre_trained = False
  k_model_path = './model.ckpt'
  with tf.Session() as sess:
    saver = tf.train.Saver()
    if use_pre_trained:
      saver.restore(sess, k_model_path)
    else:
      sess.run(tf.global_variables_initializer())
      for i in range(2000):
        last_index = index + batch_size
        batch = (train_x[index: last_index, ], train_regress_y[index: last_index, ], train_classify_y[index : last_index, ])
        if i % 10 == 0:
          regress_error = squared_loss.eval(feed_dict={
             x: batch[0], y_regress_label: batch[1], y_classify_label: batch[2]})
          classify_error = cross_entropy.eval(feed_dict={
             x: batch[0], y_regress_label: batch[1], y_classify_label: batch[2]})
          print('step {0},  regress error {1}, classify error {2}'.format(i, regress_error, classify_error))
        train_step.run(feed_dict={x: batch[0], y_regress_label: batch[1], y_classify_label: batch[2]})
        index += batch_size
      save_path = saver.save(sess, k_model_path)
      print('Model saved in path: {0}'.format(save_path))

    regress_error = squared_loss.eval(feed_dict={
             x: test_x, y_regress_label: test_regress_y, y_classify_label: test_classify_y})
    classify_error = cross_entropy.eval(feed_dict={
             x: test_x, y_regress_label: test_regress_y, y_classify_label: test_classify_y})
    print('Test regress error {0}, classify error {1}'.format(regress_error, classify_error))

def train_mnist():

  # Import data
  mnist = input_data.read_data_sets(FLAGS.data_dir)

  # Create the model
  x = tf.placeholder(tf.float32, [None, 784])

  # Define loss and optimizer
  y_ = tf.placeholder(tf.int64, [None])

  # Build the graph for the deep net
  y_conv, keep_prob = deepnn(x)

  with tf.name_scope('loss'):
    cross_entropy = tf.losses.sparse_softmax_cross_entropy(
        labels=y_, logits=y_conv)
  cross_entropy = tf.reduce_mean(cross_entropy)

  with tf.name_scope('adam_optimizer'):
    train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)

  with tf.name_scope('accuracy'):
    correct_prediction = tf.equal(tf.argmax(y_conv, 1), y_)
    correct_prediction = tf.cast(correct_prediction, tf.float32)
  accuracy = tf.reduce_mean(correct_prediction)

  graph_location = tempfile.mkdtemp()
  print('Saving graph to: %s' % graph_location)
  train_writer = tf.summary.FileWriter(graph_location)
  train_writer.add_graph(tf.get_default_graph())

  with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    for i in range(20000):
      batch = mnist.train.next_batch(50)
      import pdb
      pdb.set_trace()
      if i % 100 == 0:
        train_accuracy = accuracy.eval(feed_dict={
            x: batch[0], y_: batch[1], keep_prob: 1.0})
        print('step %d, training accuracy %g' % (i, train_accuracy))
      train_step.run(feed_dict={x: batch[0], y_: batch[1], keep_prob: 0.5})

    print('test accuracy %g' % accuracy.eval(feed_dict={
        x: mnist.test.images, y_: mnist.test.labels, keep_prob: 1.0}))


def main(_):
  train_dummy()


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--data_dir', type=str,
                      default='/tmp/tensorflow/mnist/input_data',
                      help='Directory for storing input data')
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
