import tensorflow as tf
import numpy as np


class QNetwork:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size

        # Build the neural network
        self.model = self.build_model()

    def build_model(self):
        model = tf.keras.models.Sequential(
            [
                tf.keras.layers.Dense(
                    100, input_shape=(self.state_size,), activation="relu"
                ),
                tf.keras.layers.Dense(100, activation="relu"),
                tf.keras.layers.Dense(100, activation="relu"),
                tf.keras.layers.Dense(100, activation="relu"),
                tf.keras.layers.Dense(self.action_size, activation="linear"),
            ]
        )
        model.compile(
            loss="mse", optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), metrics=['accuracy']
        )
        model.summary()

        tf.keras.utils.plot_model(
            model, to_file="model.png", show_shapes=True, show_layer_names=True
        )

        return model

    def act(self, state, epsilon):
        if np.random.rand() <= epsilon:
            action_index = np.random.choice(self.action_size)
        else:
            q_values = self.model.predict(np.array([state]), verbose=0)
            action_index = np.argmax(q_values[0])

        return action_index

    def predict(self, state):
        q_values = self.model.predict(np.array([state]), verbose=0)
        action_index = np.argmax(q_values[0])

        return action_index
