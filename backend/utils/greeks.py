"""
Black-Scholes Greeks calculation for options pricing.
Used for real-time Greeks computation from market data.
"""

import math
from decimal import Decimal
from datetime import datetime


class GreeksCalculator:
    """Calculate option Greeks using Black-Scholes model."""
    
    @staticmethod
    def norm_cdf(x: float) -> float:
        """Cumulative normal distribution function."""
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0
    
    @staticmethod
    def norm_pdf(x: float) -> float:
        """Normal probability density function."""
        return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)
    
    @staticmethod
    def calculate_d1_d2(
        S: float,  # Underlying price
        K: float,  # Strike price
        T: float,  # Time to expiration (years)
        r: float,  # Risk-free rate
        sigma: float  # Volatility (IV)
    ) -> tuple[float, float]:
        """Calculate d1 and d2 from Black-Scholes formula."""
        if T <= 0 or sigma <= 0:
            return 0.0, 0.0
        
        ln_S_K = math.log(S / K)
        d1 = (ln_S_K + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        return d1, d2
    
    @classmethod
    def calculate_call_delta(
        cls,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """Delta for call option: N(d1)"""
        d1, _ = cls.calculate_d1_d2(S, K, T, r, sigma)
        return cls.norm_cdf(d1)
    
    @classmethod
    def calculate_put_delta(
        cls,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """Delta for put option: N(d1) - 1"""
        d1, _ = cls.calculate_d1_d2(S, K, T, r, sigma)
        return cls.norm_cdf(d1) - 1.0
    
    @classmethod
    def calculate_gamma(
        cls,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """Gamma for both calls and puts: N'(d1) / (S * sigma * sqrt(T))"""
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1, _ = cls.calculate_d1_d2(S, K, T, r, sigma)
        return cls.norm_pdf(d1) / (S * sigma * math.sqrt(T))
    
    @classmethod
    def calculate_vega(
        cls,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """Vega for both calls and puts: S * N'(d1) * sqrt(T) / 100"""
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1, _ = cls.calculate_d1_d2(S, K, T, r, sigma)
        # Vega is typically expressed per 1% change in IV
        return S * cls.norm_pdf(d1) * math.sqrt(T) / 100.0
    
    @classmethod
    def calculate_call_theta(
        cls,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """Theta for call option (per day)"""
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1, d2 = cls.calculate_d1_d2(S, K, T, r, sigma)
        sqrt_T = math.sqrt(T)
        
        term1 = -S * cls.norm_pdf(d1) * sigma / (2 * sqrt_T)
        term2 = -r * K * math.exp(-r * T) * cls.norm_cdf(d2)
        
        # Convert from annual to daily
        return (term1 + term2) / 365.0
    
    @classmethod
    def calculate_put_theta(
        cls,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """Theta for put option (per day)"""
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1, d2 = cls.calculate_d1_d2(S, K, T, r, sigma)
        sqrt_T = math.sqrt(T)
        
        term1 = -S * cls.norm_pdf(d1) * sigma / (2 * sqrt_T)
        term2 = r * K * math.exp(-r * T) * cls.norm_cdf(-d2)
        
        # Convert from annual to daily
        return (term1 + term2) / 365.0
