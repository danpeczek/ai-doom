import vizdoom as vzd
import os
import torch
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F
from agents import cnn_agent
import image_preprocessing
import numpy as np

device = 'cuda' if torch.cuda.is_available() else 'cpu'


def load(agent_file, model_used):
    if os.path.isfile(agent_file):
        print("=>loading agent")
        agent = torch.load(agent_file)
        model_used.load_state_dict(agent['state_dict'])
    else:
        print("no checkpoint found...")
    return model_used


class AI:
    def __init__(self, brain, body):
        self.brain = brain
        self.body = body

    def __call__(self, inputs):
        input_images = Variable(torch.from_numpy(np.array(inputs, dtype=np.float32))).to(device)
        output = self.brain(input_images)
        actions = self.body(output)
        return actions.data.cpu().numpy()


class SoftmaxBody(nn.Module):

    def __init__(self, temperature):
        super(SoftmaxBody, self).__init__()
        self.temperature = temperature

    # Outputs from the neural network
    def forward(self, outputs):
        probabilities = F.softmax(outputs * self.temperature, dim=len(outputs))
        actions = probabilities.multinomial(num_samples=1)
        return actions


if __name__ == '__main__':
    scenario = "scenarios/basic.cfg"
    print("=>device: {}".format(device))

    actions = []
    nb_available_buttons = 3
    for i in range(0, nb_available_buttons):
        actions.append([True if action_index == i else False for action_index in range(0, nb_available_buttons)])
    number_actions = len(actions)
    image_dim = 128

    cnn = cnn_agent.CNN(number_actions=nb_available_buttons, image_dim=image_dim)
    cnn = load("experiments\\basic_scenario\\basic_cnn_doom_50.pth", cnn)
    cnn.to(device)
    softmax_body = SoftmaxBody(temperature=1.0)
    ai = AI(brain=cnn, body=softmax_body)
    game = vzd.DoomGame()
    game.load_config(scenario)
    game.init()

    nb_episodes = 30
    for episode in range(1, nb_episodes+1):
        game.new_episode()
        reward = 0
        while not game.is_episode_finished():
            state = game.get_state()
            buffer = state.screen_buffer
            img = image_preprocessing.process_image_to_grayscale(buffer, image_dim, image_dim)
            action = ai(np.array([img]))[0][0]
            reward += game.make_action(actions[action])
        print("Episode {}, reward: {}".format(episode, reward))