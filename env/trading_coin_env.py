import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np
from positionStore import PositionStore
from positionStore import Order
from positionStore import ActionType

class TradingCoinEnv(gym.Env):
  metadata = {'render.modes': ['human']}

  #хранилище позиций
  pos = None

  #индекс текущей записи (на которую указывает анализируемый временной отрезок)
  current_step = 0

  #текущий баланс в USD
  current_balance = 0

  #текущее кол-во монет
  current_crypto_coins_cnt: 0

  def __init__(self, df, cfg):
    self.df = df
    self.cfg = cfg

    self.seed(123)
          
    #сколько исторических интревалов учитывается при анализе
    self.intervals_analize_cnt = self.cfg.history_analise_minutes * 60 / self.cfg.seconds_in_intrerval

    #кол-во action'ов = насколько честей разбивается баланс (возможна покупка и продажа) + hold
    self.actions_count = 2 * self.cfg.balance_parts + 1

    #кол-во доступных action'ов (buy_1..N, sell_1..N, hold)
    self.action_space = spaces.Discrete(self.actions_count)

    #максимальный угол наклона для линейной регрессии в одном интервале
    maxSlopeDegree = 2.0

    #максимальные объем и кол-во сделок по покупке/продаже в одном интервале
    maxSize = 30000.0
    maxCount = 1000.0

    #максимальное относительное измнение btc/usdt в процентах
    maxChangeBtc = 2.0

    minValues = np.array([-maxSlopeDegree, 0, 0, 0, 0, -maxChangeBtc])
    maxValues = np.array([maxSlopeDegree, maxSize, maxSize, maxCount, maxCount, maxChangeBtc])

    #диапазон изменений
    self.observation_space = spaces.Box(minValues, maxValues, dtype=np.float32)

    self.reset()
  
    print('init basic done')

  #случайное начальное состояние
  def reset(self):
    self.current_balance = self.cfg.balance_init
    self.current_coin_count = self.cfg.crypto_coins_cnt_init
    self.pos = PositionStore()

    maxIndex = self.df.shape[0] - self.cfg.max_minutes_hold_pos * 60 / self.cfg.seconds_in_intrerval
    self.current_step = random.randint(self.intervals_analize_cnt,  maxIndex)

  def step(self, action):
    assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))
    actionType, qtyRatio = self._parse_action(action)
    #print (actionType, qtyRatio)
    
    #fixme - доделать
    if (actionType == ActionType.HOLD):
      return 

    if (self.current_balance <= 0):
      reward = -1000
    
    if (actionType == ActionType.BUY):
      qty = self.cfg.balance_init * qtyRatio
      if (qty > self.current_balance):
        reward = -1000
      else:
        self.current_balance -= qty
        price = self.df.at[self.current_step, "avrPrice"]
        ord = Order(type = actionType, price = price, qty = qty)
        self.pos.addOrder(order)
        reward = self.pos

    

    
  def render(self, mode='human'):
    print('render')
    
  def close(self):
    print('close')

  def _parse_action(self, action_number):
    if (action_number == (self.actions_count - 1)):
      return [ActionType.HOLD, 0]
    
    actionInd = action_number // self.cfg.balance_parts
    if (actionInd > 1):
      raise "Action type errorr define"

    actionType = ActionType(actionInd)
    reminder = action_number % self.cfg.balance_parts
    qtyRatio = (reminder + 1) * (1 / self.cfg.balance_parts)

    return actionType, qtyRatio