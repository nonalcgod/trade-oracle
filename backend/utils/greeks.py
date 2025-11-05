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


def calculate_all_greeks(
    underlying_price: Decimal,
    strike: Decimal,
    expiration: datetime,
    option_price: Decimal,
    is_call: bool,
    risk_free_rate: float = 0.05  # Default 5% risk-free rate
) -> dict:
    """
    Calculate all Greeks for an option.

    Args:
        underlying_price: Current price of underlying
        strike: Option strike price
        expiration: Option expiration datetime
        option_price: Current option price (for IV estimation)
        is_call: True for call, False for put
        risk_free_rate: Annual risk-free rate (default 5%)

    Returns:
        Dict with delta, gamma, theta, vega, iv
    """
    # Convert Decimal to float
    S = float(underlying_price)
    K = float(strike)
    option_px = float(option_price)

    # Calculate time to expiration in years
    now = datetime.utcnow()
    time_diff = expiration - now
    T = max(time_diff.total_seconds() / (365.25 * 24 * 3600), 0.0001)  # Minimum 1 hour

    # Estimate IV from option price (simplified - using ATM IV as proxy)
    # In production, use Newton-Raphson to solve for IV
    # For now, use a reasonable default based on option price
    if option_px > 0 and S > 0:
        # Rough IV estimation: higher option prices relative to underlying suggest higher IV
        moneyness = S / K if K > 0 else 1.0
        iv_estimate = min(max(option_px / (S * math.sqrt(T)) * math.sqrt(2 * math.pi), 0.10), 2.0)
    else:
        iv_estimate = 0.30  # Default 30% IV

    # Calculate Greeks using GreeksCalculator
    calc = GreeksCalculator()

    if is_call:
        delta = Decimal(str(calc.calculate_call_delta(S, K, T, risk_free_rate, iv_estimate)))
        theta = Decimal(str(calc.calculate_call_theta(S, K, T, risk_free_rate, iv_estimate)))
    else:
        delta = Decimal(str(calc.calculate_put_delta(S, K, T, risk_free_rate, iv_estimate)))
        theta = Decimal(str(calc.calculate_put_theta(S, K, T, risk_free_rate, iv_estimate)))

    gamma = Decimal(str(calc.calculate_gamma(S, K, T, risk_free_rate, iv_estimate)))
    vega = Decimal(str(calc.calculate_vega(S, K, T, risk_free_rate, iv_estimate)))
    iv = Decimal(str(iv_estimate))

    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'iv': iv
    }
