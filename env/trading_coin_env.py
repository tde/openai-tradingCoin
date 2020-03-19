import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np
import random
from env.positionStore import PositionStore
from env.positionStore import Order
from env.positionStore import ActionType

class TradingCoinEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    #хранилище позиций
    pos = None

    #индекс текущей записи (на которую указывает анализируемый временной отрезок)
    current_index = 0

    # сколько всего выполнено интераций


    #текущий баланс в USD
    current_balance = 0

    #текущее кол-во монет
    current_crypto_coins_cnt = 0

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
        maxSize = 40000.0
        maxCount = 1000.0

        #максимальное относительное измнение btc/usdt в процентах
        maxChangeBtc = 2.0

        # проверки на попадание в мин_макс значения
        assert df[df['slope'] <= -maxSlopeDegree].shape[0] <= 0, 'Slope lowest then default min'
        assert df[df['slope'] >= maxSlopeDegree].shape[0] <= 0, 'Slope greater then default max'
        
        assert df[df['buySize'] >= maxSize].shape[0] <= 0, 'maxBuySize greater then default max'
        assert df[df['sellSize'] >= maxSize].shape[0] <= 0, 'maxSellSize greater then default max'
        
        assert df[df['buyCnt'] >= maxCount].shape[0] <= 0, 'maxBuyCount greater then default max'
        assert df[df['sellCnt'] >= maxCount].shape[0] <= 0, 'maxSellCount greater then default max'
        
        assert df[df['bitcoinChange'] >= maxChangeBtc].shape[0] <= 0, 'maxBitcoinChange greater then default max'
        assert df[df['bitcoinChange'] <= -maxChangeBtc].shape[0] <= 0, 'minBitcoinChange lowest then default min'

        self._observation_columns = ['slope', 'buySize', 'sellSize', 'buyCnt', 'sellCnt', 'bitcoinChange']

        df['slope'] /= maxSlopeDegree
        df['buySize'] /= maxSize
        df['sellSize'] /= maxSize
        df['buyCnt'] /= maxCount
        df['sellCnt'] /= maxCount
        df['bitcoinChange'] /= maxChangeBtc

        #assert df[df > 1].shape[0] <= 0, 'dataframe contain values greate then 1'
        #assert df[df < -1].shape[0] <= 0, 'dataframe contain values lowest then -1'

        
        minValues = np.array([-1, 0, 0, 0, 0, -1, 0])
        maxValues = np.array([1, 1, 1, 1, 1, 1, 1])

        n_columns = len(self._observation_columns) + 1
        n_rows = int(self.intervals_analize_cnt) + 1

        #диапазон изменений
        #self.observation_space = spaces.Box(low = minValues, high = maxValues, 
        #         dtype=np.float32)
        self.observation_space = spaces.Box(low = -1.0, high = 1.0, 
                 shape=(n_rows, n_columns))
                 

        self.reset()
    
        print('init basic done')

    #случайное начальное состояние
    def reset(self):
        maxIndex = self.df.shape[0] - self.cfg.max_minutes_hold_pos * 60 / self.cfg.seconds_in_intrerval - 7
        
        self.current_index = random.randint(self.intervals_analize_cnt+5, maxIndex)
        self.current_interation = 0
        
        initial_price = self.df.at[self.current_index, "avrPrice"]

        self.pos = PositionStore(initial_usd = self.cfg.balance_init, initial_coins = self.cfg.coins_init,
                                initial_price = initial_price)

        return self._next_observation()

    def step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))

        done = False

        # следующий временной отрезок
        self.current_index += 1
        self.current_interation += 1

        # цена на данном отрезке
        cur_price = self.df.at[self.current_index, "avrPrice"]

        # проверка что закончился максимальный срок удержания позиции
        if (self.current_interation >= self.intervals_analize_cnt):
            done = True

        # распарсить тип действия и кол-во
        actionType, qtyRatio = self._parse_action(action)
        #print (actionType, qtyRatio)
        qty = (self.cfg.balance_init if actionType == ActionType.BUY else self.cfg.coins_init) * qtyRatio
        
        # действия - это покупка или продажа
        if (actionType != ActionType.HOLD):
            # неначто покупать или нечего продавать
            if ((actionType == ActionType.BUY and qty > self.pos.current_usd) or
                (actionType == ActionType.SELL and qty > self.pos.current_coins)):
                    reward = -100 * self.cfg.balance_init
            else:
                order = Order(type = actionType, price = cur_price, qty = qty)        
                self.pos.addOrder(order)
        
        # расчет профита
        reward = self.pos.calcProfit(current_price = cur_price)

        obs = self._next_observation()
        
        return obs, reward, done, {}
   
    # Render the environment to the screen
    def render(self, mode='human'):
        cur_price = self.df.at[self.current_index, "avrPrice"]
        profit = self.pos.calcProfit(current_price = cur_price)

        print(f'Step: {self.current_index}')
        print(f'Orders count: {len(self.pos.orders)}')
        print(f'Balance Usd: {self.pos.current_usd}')
        print(f'Balance Coins: {self.pos.current_coins}')
        print(f'Profit: {profit}')
        
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
    
    def _next_observation(self):
        ind1 = self.current_index - self.intervals_analize_cnt
        ind2 = self.current_index 

        data = self.df.loc[ind1 : ind2, self._observation_columns].to_numpy()

        # текущий баланс в usd и coins
        usd = self.pos.current_usd / self.pos.max_usd
        coins = self.pos.current_coins / self.pos.max_coins

        if (usd > 1 or coins > 1):
            print ('error usd')

        assert usd < 1 and coins < 1, f'usd or coins greater max {usd}, {coins}'

        nz = np.zeros((data.shape[0],1), dtype=float)
        nz[0,0] = usd
        nz[1,0] = coins

        result = np.concatenate((data, nz), axis=1)

        return result