import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from sklearn.linear_model import LinearRegression, HuberRegressor, TheilSenRegressor
import logging
from typing import Dict, Tuple, Optional

import config
from backend.database import get_session, AnalyticsResult
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """Computes quantitative analytics on price data"""
    
    def __init__(self):
        self.regression_models = {
            'ols': LinearRegression(),
            'huber': HuberRegressor(),
            'theil_sen': TheilSenRegressor()
        }
    
    def compute_basic_stats(self, df: pd.DataFrame) -> Dict:
        """Compute basic price statistics"""
        if df.empty or 'close' not in df.columns:
            return {}
        
        prices = df['close'].values
        returns = np.diff(np.log(prices))
        
        stats = {
            'mean': float(np.mean(prices)),
            'std': float(np.std(prices)),
            'min': float(np.min(prices)),
            'max': float(np.max(prices)),
            'current': float(prices[-1]),
            'return_mean': float(np.mean(returns)) if len(returns) > 0 else 0,
            'return_std': float(np.std(returns)) if len(returns) > 0 else 0,
            'volatility': float(np.std(returns) * np.sqrt(252)) if len(returns) > 0 else 0
        }
        
        return stats
    
    def compute_hedge_ratio(self, 
                           y_series: pd.Series, 
                           x_series: pd.Series,
                           method: str = 'ols') -> Tuple[float, float, float]:
        """
        Compute hedge ratio using regression
        Returns: (hedge_ratio, r_squared, intercept)
        """
        if len(y_series) < 2 or len(x_series) < 2:
            return 0.0, 0.0, 0.0
        
        # Align series
        common_idx = y_series.index.intersection(x_series.index)
        if len(common_idx) < 2:
            return 0.0, 0.0, 0.0
        
        y = y_series.loc[common_idx].values.reshape(-1, 1)
        x = x_series.loc[common_idx].values.reshape(-1, 1)
        
        # Get regression model
        model = self.regression_models.get(method, LinearRegression())
        
        try:
            model.fit(x, y)
            hedge_ratio = float(model.coef_[0][0])
            intercept = float(model.intercept_[0])
            
            # Calculate R-squared
            y_pred = model.predict(x)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            return hedge_ratio, float(r_squared), intercept
            
        except Exception as e:
            logger.error(f"Error computing hedge ratio: {e}")
            return 0.0, 0.0, 0.0
    
    def compute_spread(self, 
                       y_series: pd.Series, 
                       x_series: pd.Series,
                       hedge_ratio: float) -> pd.Series:
        """Compute spread: Y - hedge_ratio * X"""
        common_idx = y_series.index.intersection(x_series.index)
        spread = y_series.loc[common_idx] - hedge_ratio * x_series.loc[common_idx]
        return spread
    
    def compute_z_score(self, series: pd.Series, window: int = None) -> pd.Series:
        """Compute rolling z-score"""
        if window is None:
            window = config.Z_SCORE_WINDOW
        
        if len(series) < window:
            return pd.Series([0] * len(series), index=series.index)
        
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()
        
        z_score = (series - rolling_mean) / rolling_std
        z_score = z_score.fillna(0)
        
        return z_score
    
    def compute_correlation(self, 
                           series1: pd.Series, 
                           series2: pd.Series,
                           window: int = None) -> pd.Series:
        """Compute rolling correlation"""
        if window is None:
            window = config.CORRELATION_WINDOW
        
        common_idx = series1.index.intersection(series2.index)
        if len(common_idx) < window:
            return pd.Series([0] * len(common_idx), index=common_idx)
        
        s1 = series1.loc[common_idx]
        s2 = series2.loc[common_idx]
        
        rolling_corr = s1.rolling(window=window).corr(s2)
        rolling_corr = rolling_corr.fillna(0)
        
        return rolling_corr
    
    def perform_adf_test(self, series: pd.Series) -> Dict:
        """Perform Augmented Dickey-Fuller test for stationarity"""
        if len(series) < 10:
            return {
                'statistic': 0,
                'pvalue': 1,
                'critical_values': {},
                'is_stationary': False
            }
        
        try:
            result = adfuller(series.dropna(), autolag='AIC')
            
            is_stationary = result[1] < config.ADF_SIGNIFICANCE
            
            return {
                'statistic': float(result[0]),
                'pvalue': float(result[1]),
                'critical_values': {k: float(v) for k, v in result[4].items()},
                'is_stationary': is_stationary
            }
        except Exception as e:
            logger.error(f"Error performing ADF test: {e}")
            return {
                'statistic': 0,
                'pvalue': 1,
                'critical_values': {},
                'is_stationary': False
            }
    
    def compute_pair_analytics(self,
                              df1: pd.DataFrame,
                              df2: pd.DataFrame,
                              symbol1: str,
                              symbol2: str,
                              timeframe: str,
                              window_size: int = None,
                              regression_method: str = 'ols') -> Dict:
        """
        Compute comprehensive pair trading analytics
        """
        if df1.empty or df2.empty:
            return {}
        
        if window_size is None:
            window_size = config.DEFAULT_WINDOW_SIZE
        
        # Extract price series
        prices1 = df1.set_index('timestamp')['close']
        prices2 = df2.set_index('timestamp')['close']
        
        # Compute hedge ratio
        hedge_ratio, r_squared, intercept = self.compute_hedge_ratio(
            prices1, prices2, method=regression_method
        )
        
        # Compute spread
        spread = self.compute_spread(prices1, prices2, hedge_ratio)
        
        # Compute z-score of spread
        z_score = self.compute_z_score(spread, window=window_size)
        
        # Compute rolling correlation
        correlation = self.compute_correlation(prices1, prices2, window=window_size)
        
        # Perform ADF test on spread
        adf_result = self.perform_adf_test(spread)
        
        # Spread statistics
        spread_stats = {
            'mean': float(spread.mean()),
            'std': float(spread.std()),
            'current': float(spread.iloc[-1]) if len(spread) > 0 else 0
        }
        
        # Save to database
        self._save_analytics_result(
            symbol1, symbol2, timeframe,
            hedge_ratio, spread_stats['current'], 
            z_score.iloc[-1] if len(z_score) > 0 else 0,
            correlation.iloc[-1] if len(correlation) > 0 else 0,
            adf_result['statistic'], adf_result['pvalue'],
            spread_stats['mean'], spread_stats['std']
        )
        
        return {
            'hedge_ratio': hedge_ratio,
            'r_squared': r_squared,
            'intercept': intercept,
            'spread': spread.to_dict(),
            'z_score': z_score.to_dict(),
            'correlation': correlation.to_dict(),
            'adf_test': adf_result,
            'spread_stats': spread_stats,
            'current_z_score': float(z_score.iloc[-1]) if len(z_score) > 0 else 0,
            'current_correlation': float(correlation.iloc[-1]) if len(correlation) > 0 else 0
        }
    
    def _save_analytics_result(self, symbol1: str, symbol2: str, timeframe: str,
                               hedge_ratio: float, spread: float, z_score: float,
                               correlation: float, adf_stat: float, adf_pval: float,
                               spread_mean: float, spread_std: float):
        """Save analytics results to database"""
        session = get_session()
        try:
            result = AnalyticsResult(
                symbol_pair=f"{symbol1}_{symbol2}",
                timestamp=datetime.now(),
                timeframe=timeframe,
                hedge_ratio=hedge_ratio,
                spread=spread,
                z_score=z_score,
                correlation=correlation,
                adf_statistic=adf_stat,
                adf_pvalue=adf_pval,
                spread_mean=spread_mean,
                spread_std=spread_std
            )
            session.add(result)
            session.commit()
        except Exception as e:
            logger.error(f"Error saving analytics result: {e}")
            session.rollback()
        finally:
            session.close()
    
    def compute_liquidity_metrics(self, df: pd.DataFrame) -> Dict:
        """Compute liquidity-related metrics"""
        if df.empty or 'volume' not in df.columns:
            return {}
        
        volume = df['volume'].values
        prices = df['close'].values
        
        metrics = {
            'avg_volume': float(np.mean(volume)),
            'volume_std': float(np.std(volume)),
            'total_volume': float(np.sum(volume)),
            'avg_dollar_volume': float(np.mean(volume * prices)),
            'volume_trend': float(np.polyfit(range(len(volume)), volume, 1)[0]) if len(volume) > 1 else 0
        }
        
        return metrics
