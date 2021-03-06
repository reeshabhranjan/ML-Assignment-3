import idx2numpy as idx2numpy
import numpy as np
from sklearn.neural_network import MLPClassifier
from matplotlib import pyplot as plt


def calculate_match_accuracy(y_pred, y_test):
	accuracy_sum = 0
	for row in range(y_pred.shape[0]):
		y_row_pred = y_pred[row].reshape(-1, 1)
		correct_label = y_test[row]
		max_index = np.argmax(y_row_pred)
		accuracy_sum += (max_index == correct_label)
	return accuracy_sum / y_test.shape[0]

class NeuralNet:
	num_layers = None
	num_nodes = None
	activation_function = None
	learning_rate = None
	weights = None
	weight_deltas = None
	outputs = None
	outputs_derivative = None
	deltas = None
	biases = None
	num_labels = None
	num_inputs = None

	def __init__(self, num_layers, num_nodes, activation_function, learning_rate, num_labels, num_inputs):
		self.num_layers = num_layers  # number of layers including input and output
		self.num_nodes = num_nodes  # list of number of nodes in each layer
		self.activation_function = activation_function  # activation function to be used (string)
		self.learning_rate = learning_rate  # learning rate
		self.weights = [None] * (num_layers - 1)  # it is a list of list of numpy arrays
		self.weight_deltas = [None] * (num_labels - 1)
		# the [i][j] index of the data-structure corresponds to weight to the jth node in the
		# (i + 1)th layer from all the nodes in the ith layer.
		self.outputs = [None] * (num_layers)  # it is a list of numpy arrays
		# it store the output of all the layers, where output is the phi(v)
		self.outputs_derivative = [None] * (num_layers)  # it is a list of numpy arrays
		# it stores the derivative of output of all the layers, where the derivative is phi'(v)
		self.deltas = [None] * (num_layers)  # it is a list of numpy arrays.
		# it stores delta values corresponding to each node in a given later.
		self.biases = [None] * (num_layers)
		self.num_labels = num_labels
		self.num_inputs = num_inputs

		# initialise the weights
		for layer in range(num_layers - 1):
			self.weights[layer] = 0.01 * np.random.normal(loc=0, scale=1, size=(self.num_nodes[layer], self.num_nodes[layer + 1]))

		# initialise weight-deltas
		self.reset_weight_deltas()

		# initialise the bias for each node
		for layer in range(num_layers):
			self.biases[layer] = np.zeros((self.num_nodes[layer], 1))
			
		# initialize the outputs, deltas to empty
		for output in range(len(self.outputs)):
			self.outputs[output] = np.empty((num_nodes[output], 1))

	def reset_weight_deltas(self):
		for layer in range(self.num_layers - 1):
			self.weight_deltas[layer] = np.zeros((self.num_nodes[layer], self.num_nodes[layer + 1]))

	def forward_phase(self, input):
		input = input.reshape(-1, 1)
		self.outputs[0] = input
		self.outputs_derivative[0] = Activation.grad(input, self.activation_function)
		for layer in range(1, self.num_layers):
			output = np.dot(np.transpose(self.weights[layer - 1]), self.outputs[layer - 1]) + self.biases[layer]
			if layer == self.num_layers - 1:
				output = Softmax.value(output)
				self.outputs_derivative[-1] = Softmax.grad(output)
			else:
				output = Activation.value(output, self.activation_function)
				self.outputs_derivative[layer] = Activation.grad(output, self.activation_function)
			self.outputs[layer] = output

	def update_weights(self, batch_size):
		for layer in range(self.num_layers - 1):
			self.weights[layer] += self.weight_deltas[layer] / batch_size

	def backward_phase(self, d, update_weights, batch_size):
		"""Call it with layer = 0"""

		d = d.reshape(-1, 1)
		# calculate deltas for the output layer
		self.deltas[-1] = (d - self.outputs[
			-1]) / 10  # * self.outputs_derivative[-1] #/ self.outputs[-1].shape[0] # TODO remove this
		# calculate bias for output layer
		self.biases[-1] += self.learning_rate * self.deltas[-1]
		
		if update_weights:
			self.update_weights(batch_size=batch_size)
			self.reset_weight_deltas()

		# calculate deltas for previous layers and update weights
		for layer in range(self.num_layers - 2, -1, -1):
			weight_delta = self.learning_rate * np.dot(self.outputs[layer], np.transpose(self.deltas[layer + 1]))
			self.deltas[layer] = np.multiply(np.dot(self.weights[layer], self.deltas[layer + 1]),
			                                 self.outputs_derivative[layer])
			self.weight_deltas[layer] += weight_delta
			# self.weights[layer] -= weights_delta
			self.biases[layer] += self.learning_rate * self.deltas[layer]

	def fit(self, x, y, batch_size, epochs):
		accuracy_epochs = []
		for epoch in range(epochs):
			score_epoch = 0
			batch_iter = 0
			for row in range(x.shape[0]):
				batch_iter += 1
				input = x[row, :]
				d = np.zeros((num_labels, 1))
				for i in range(num_labels):
					d[i, 0] = 1 if i == y[row, 0] else 0
				self.forward_phase(input)
				
				score_epoch += self.cross_entropy_loss(self.get_train_outputs(), d)
				update_weights = False
				if batch_iter == batch_size:
					update_weights = True
					batch_iter = 0
					
				self.backward_phase(d, update_weights=update_weights, batch_size=batch_size)
			score_epoch /= x.shape[0]
			accuracy_epochs.append(score_epoch)

		# save weights
		for layer in range(self.num_layers - 1):
			np.savetxt('weights/weights_' + self.activation_function + '_' + str(layer + 1), self.weights[layer])
		return accuracy_epochs

	def predict(self, X):
		self.forward_phase(X)
		return self.outputs[-1]

	def score(self, x_test, y_test):
		accuracy_sum = 0
		for row in range(x_test.shape[0]):
			x_row = x_test[row, :]
			y_row = y_test[row, :]
			y_pred = self.predict(x_row)
			max_index = np.argmax(y_pred)
			accuracy_sum += (max_index == y_test[row])
		return accuracy_sum / y_test.shape[0]

	def cross_entropy_loss(self, y_pred, y_act):
		return -(np.sum(np.dot(np.transpose(y_act), np.log(y_pred))) + np.sum(
			np.dot(np.transpose(1.0 - y_act), np.log(1.0 - y_pred))))

	def get_train_outputs(self):
		return self.outputs[-1]


class Activation:
	@staticmethod
	def value(x, activation_function):
		if activation_function == 'relu':
			return Relu.value(x)
		elif activation_function == 'linear':
			return Linear.value(x)
		elif activation_function == 'tanh':
			return Tanh.value(x)
		elif activation_function == 'sigmoid':
			return Sigmoid.value(x)

	@staticmethod
	def grad(x, activation_function):
		if activation_function == 'relu':
			return Relu.grad(x)
		elif activation_function == 'linear':
			return Linear.grad(x)
		elif activation_function == 'tanh':
			return Tanh.grad(x)
		elif activation_function == 'sigmoid':
			return Sigmoid.grad(x)


class Relu:
	@staticmethod
	def value(x):
		return x.clip(min=0)

	@staticmethod
	def grad(x):
		return (np.sign(x) + 1) // 2
		print(x)

class Sigmoid:
	@staticmethod
	def value(x):
		return 1 / (1 + np.exp(-x))

	@staticmethod
	def grad(x):
		# return np.multiply(Sigmoid.value(x), (1 - Sigmoid.value(x)))
		return np.multiply(Sigmoid.value(x), (1 - Sigmoid.value(x)))

class Linear:
	@staticmethod
	def value(x, m=1, c=0):
		return m * x + c

	@staticmethod
	def grad(x, m=1, c=0):
		return m

class Tanh:
	@staticmethod
	def value(x, a=1, b=1):
		return a * np.tanh(b * x)

	@staticmethod
	def grad(x, a=1, b=1):
		return a * b / np.square(np.cosh(b * x))

class Softmax:
	@staticmethod
	def value(X):
		exp_vals = np.exp(X - np.max(X))
		return exp_vals / (np.sum(exp_vals, axis=0))

	@staticmethod
	def grad(X):
		return X / 10


if __name__ == '__main__':
	training_images = idx2numpy.convert_from_file('images/train-images.idx3-ubyte')
	training_labels = idx2numpy.convert_from_file('images/train-labels.idx1-ubyte')
	test_images = idx2numpy.convert_from_file('images/t10k-images.idx3-ubyte')
	test_labels = idx2numpy.convert_from_file('images/t10k-labels.idx1-ubyte')
	y_train = training_labels.reshape(-1, 1)
	y_test = test_labels.reshape(-1, 1)
	x_train = np.empty((training_images.shape[0], 784))
	x_test = np.empty((test_images.shape[0], 784))
	for i in range(0, training_images.shape[0]):
		x_train[i, :] = training_images[i, :].flatten()
	for i in range(test_images.shape[0]):
		x_test[i, :] = test_images[i, :].flatten()

	# shuffle train
	shuffle_dataset = np.concatenate((x_train, y_train), axis=1)
	np.random.shuffle(shuffle_dataset)
	x_train = shuffle_dataset[:, :-1]
	y_train = shuffle_dataset[:, -1].reshape(-1, 1)

	print(x_train.shape)
	print(y_train.shape)

	x = x_train[:1000, :]
	y = y_train[:1000, :]
	num_inputs = x.shape[1]
	num_labels = 10
	x_test = x_test[: 1000, :]
	y_test = y_test[: 1000, :]

	activation_custom = ['relu', 'sigmoid', 'linear', 'tanh']
	epochs_list = [100, 200, 10, 500]
	activation_sklearn = ['relu', 'logistic', 'identity', 'tanh']

	# custom

	for i, activation in enumerate(activation_custom):
		# break
		print("starting " + activation + "...")
		neuralNet = NeuralNet(5, [num_inputs, 256, 128, 64, num_labels], activation, 0.1, num_labels=num_labels, num_inputs=num_inputs)
		accuracy_epochs = neuralNet.fit(x, y, batch_size=100, epochs=epochs_list[i])
		accuracy_test = list(neuralNet.score(x_test, y_test).reshape(-1, ))
		print("Custom " + activation + " " + str(accuracy_test))

		# save graphs
		plt.figure()
		accuracy_xs = list(range(len(accuracy_epochs)))
		plt.plot(accuracy_xs, accuracy_epochs)
		plt.title("Custom " + activation)
		plt.xlabel("Epochs")
		plt.ylabel("Training error")
		plt.savefig('plots/' + 'custom_' + activation + '.png')
		plt.clf()
		print("custom " + activation + " done")

	# save weights to file

	# sklearn

	# clf = MLPClassifier(solver='sgd', activation='identity', alpha=0.1, hidden_layer_sizes=(256, 128, 64))
	# clf.fit(x, y.reshape(-1, ))
	# y_pred = clf.predict_proba(x_test)
	# print(calculate_match_accuracy(y_pred, y_test.reshape(-1, )))
	# print(y_pred[0].shape)

	for i, activation in enumerate(activation_sklearn):
		# break
		print('sklearn ' + activation)
		if activation != 'identity':
			clf = MLPClassifier(solver='sgd', activation=activation, alpha=0.1, hidden_layer_sizes=(256, 128, 64), max_iter=500)
		else:
			clf = MLPClassifier(activation='identity', alpha=0.1, hidden_layer_sizes=(256, 128, 64), max_iter=500, verbose=True)
		clf.fit(x, y.reshape(-1, ))
		score = clf.score(x_test, y_test)
		print('score: ' + str(score))
		
	clf = MLPClassifier(activation='identity', alpha=0.1, hidden_layer_sizes=(256, 128, 64), max_iter=500, verbose=True)
	clf.fit(x, y.reshape(-1, ))
	score = clf.score(x_test, y_test)
	print(score)
