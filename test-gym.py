import os
import gym
import sys
import pandas as pd
import numpy as np
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import PPO2
from stable_baselines.common.env_checker import check_env
from env.trading_coin_env import TradingCoinEnv

props = {
    #начальный баланс на счете
    'balance_init': 4000,

    #начальное кол-во монет на счете
    'coins_init': 200,

    #на сколько частей можно разбить доступный остасток для покупки/продажи, 
    #т.е. покупать не на всю доступную сумму а на ее часть
    'balance_parts': 5,

    #сколько минут истории надо учитывать для обучения
    'history_analise_minutes': 900,

    #максимальное время удержания позиции (в минутах)
    'max_minutes_hold_pos': 600,

    #сколько секунд в одном интервале
    'seconds_in_intrerval': 15,

    #сколько исторических интервалов до текущего надо учитывать
    #'lookback_window_size': 20
}

class Config:
    def __init__(self, **entries):
        self.__dict__.update(entries)

#props to object
cfg = Config(**props)

#read data from file
DATASET_PATH = "data"
file_name = os.path.join(os.path.dirname(__file__), DATASET_PATH + "/binanceOpenAi-jan.dat")
df = pd.read_csv(file_name)
df.rename(columns=lambda x: x.strip(), inplace=True)

df['avrPrice'] = df['avrPrice'].replace(to_replace=0, method='ffill')

# The algorithms require a vectorized environment to run
#env = DummyVecEnv([lambda: TradingCoinEnv(df, cfg)])

env = TradingCoinEnv(df, cfg)
env = DummyVecEnv([lambda: env])

#check_env(env, warn=True)
model = PPO2(MlpPolicy, env, verbose=1)
model.learn(total_timesteps=10000)

obs = env.reset()
for i in range(1000):
    action, _states = model.predict(obs)
    obs, rewards, dones, info = env.step(action)
    env.render()