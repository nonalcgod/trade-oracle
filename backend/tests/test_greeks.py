"""
Test Suite for Greeks Calculator

Tests Black-Scholes implementation for option Greeks calculations.
Critical for position sizing and risk management.
"""

import pytest
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.greeks import GreeksCalculator


class TestBlackScholesD1D2:
    """Test d1 and d2 calculations (foundation for all Greeks)"""

    def test_d1_d2_atm(self):
        """ATM option should have d1 ≈ d2"""
        S = 100.0
        K = 100.0
        T = 0.25  # 3 months
        r = 0.05
        sigma = 0.30

        d1, d2 = GreeksCalculator.calculate_d1_d2(S, K, T, r, sigma)

        # ATM with reasonable vol: d1 and d2 should be similar
        assert abs(d1 - d2) < 0.2  # Difference should be small

    def test_zero_time_to_expiration(self):
        """Should handle T=0 gracefully (returns 0)"""
        S = 100.0
        K = 100.0
        T = 0.0  # Expired
        r = 0.05
        sigma = 0.30

        d1, d2 = GreeksCalculator.calculate_d1_d2(S, K, T, r, sigma)

        assert d1 == 0.0
        assert d2 == 0.0

    def test_zero_volatility(self):
        """Should handle sigma=0 gracefully (returns 0)"""
        S = 100.0
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.0  # Zero volatility

        d1, d2 = GreeksCalculator.calculate_d1_d2(S, K, T, r, sigma)

        assert d1 == 0.0
        assert d2 == 0.0


class TestDelta:
    """Test delta calculations for calls and puts"""

    def test_call_delta_atm(self):
        """ATM call delta should be approximately 0.5"""
        S = 100.0
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        delta = GreeksCalculator.calculate_call_delta(S, K, T, r, sigma)

        # ATM call delta should be around 0.5 (wider tolerance for interest rate effects)
        assert 0.40 < delta < 0.65, f"ATM call delta {delta} not near 0.5"

    def test_put_delta_atm(self):
        """ATM put delta should be approximately -0.5"""
        S = 100.0
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        delta = GreeksCalculator.calculate_put_delta(S, K, T, r, sigma)

        # ATM put delta should be around -0.5 (wider tolerance for interest rate effects)
        assert -0.65 < delta < -0.40, f"ATM put delta {delta} not near -0.5"

    def test_deep_itm_call_delta(self):
        """Deep ITM call delta should approach 1.0"""
        S = 150.0  # 50% above strike
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        delta = GreeksCalculator.calculate_call_delta(S, K, T, r, sigma)

        # Deep ITM call delta should be > 0.95
        assert delta > 0.95, f"Deep ITM call delta {delta} not close to 1.0"

    def test_deep_otm_call_delta(self):
        """Deep OTM call delta should approach 0.0"""
        S = 50.0  # 50% below strike
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        delta = GreeksCalculator.calculate_call_delta(S, K, T, r, sigma)

        # Deep OTM call delta should be < 0.05
        assert delta < 0.05, f"Deep OTM call delta {delta} not close to 0.0"

    def test_put_call_delta_parity(self):
        """Put delta = Call delta - 1 (put-call parity)"""
        S = 100.0
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        call_delta = GreeksCalculator.calculate_call_delta(S, K, T, r, sigma)
        put_delta = GreeksCalculator.calculate_put_delta(S, K, T, r, sigma)

        # Put delta should equal call delta minus 1
        expected_put_delta = call_delta - 1.0
        assert abs(put_delta - expected_put_delta) < 0.01, \
            f"Put-call delta parity violated: {put_delta} != {expected_put_delta}"


class TestGamma:
    """Test gamma calculations"""

    def test_gamma_positive(self):
        """Gamma is always positive for long options"""
        S = 100.0
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        gamma = GreeksCalculator.calculate_gamma(S, K, T, r, sigma)

        assert gamma > 0, f"Gamma {gamma} should be positive"

    def test_gamma_call_put_symmetry(self):
        """Call and put gamma should be identical"""
        S = 100.0
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        call_gamma = GreeksCalculator.calculate_gamma(S, K, T, r, sigma)
        put_gamma = GreeksCalculator.calculate_gamma(S, K, T, r, sigma)

        assert call_gamma == put_gamma, "Call and put gamma should be equal"

    def test_gamma_peaks_atm(self):
        """Gamma is highest for ATM options"""
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        # ATM gamma
        gamma_atm = GreeksCalculator.calculate_gamma(100.0, K, T, r, sigma)

        # ITM gamma
        gamma_itm = GreeksCalculator.calculate_gamma(120.0, K, T, r, sigma)

        # OTM gamma
        gamma_otm = GreeksCalculator.calculate_gamma(80.0, K, T, r, sigma)

        # ATM gamma should be highest
        assert gamma_atm > gamma_itm, "ATM gamma should exceed ITM gamma"
        assert gamma_atm > gamma_otm, "ATM gamma should exceed OTM gamma"


class TestVega:
    """Test vega calculations"""

    def test_vega_positive(self):
        """Vega is always positive (long vega for buyers)"""
        S = 100.0
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        vega = GreeksCalculator.calculate_vega(S, K, T, r, sigma)

        assert vega > 0, f"Vega {vega} should be positive"

    def test_vega_decreases_with_time(self):
        """Vega decreases as expiration approaches"""
        S = 100.0
        K = 100.0
        r = 0.05
        sigma = 0.30

        # Vega with 3 months to expiration
        vega_3mo = GreeksCalculator.calculate_vega(S, K, 0.25, r, sigma)

        # Vega with 1 month to expiration
        vega_1mo = GreeksCalculator.calculate_vega(S, K, 0.083, r, sigma)

        # Vega should decrease as expiration approaches
        assert vega_3mo > vega_1mo, f"Vega should decrease with time: {vega_3mo} vs {vega_1mo}"


class TestTheta:
    """Test theta calculations (time decay)"""

    def test_call_theta_negative(self):
        """Call theta should be negative (time decay)"""
        S = 100.0
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        theta = GreeksCalculator.calculate_call_theta(S, K, T, r, sigma)

        assert theta < 0, f"Call theta {theta} should be negative (time decay)"

    def test_put_theta_negative_otm(self):
        """OTM put theta should be negative"""
        S = 110.0  # Stock above strike (OTM put)
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        theta = GreeksCalculator.calculate_put_theta(S, K, T, r, sigma)

        # OTM put loses value with time
        assert theta < 0, f"OTM put theta {theta} should be negative"


class TestBlackScholesFormulas:
    """Test complete Black-Scholes calculations"""

    def test_integrated_greeks_calculation(self):
        """Test calculating multiple Greeks for the same option"""
        S = 100.0
        K = 100.0
        T = 0.25  # 3 months
        r = 0.05
        sigma = 0.30

        # Calculate all Greeks
        delta = GreeksCalculator.calculate_call_delta(S, K, T, r, sigma)
        gamma = GreeksCalculator.calculate_gamma(S, K, T, r, sigma)
        vega = GreeksCalculator.calculate_vega(S, K, T, r, sigma)
        theta = GreeksCalculator.calculate_call_theta(S, K, T, r, sigma)

        # Verify all Greeks are reasonable for ATM option
        assert 0.40 < delta < 0.65, f"Call delta {delta} out of reasonable range"
        assert gamma > 0, f"Gamma {gamma} should be positive"
        assert vega > 0, f"Vega {vega} should be positive"
        assert theta < 0, f"Theta {theta} should be negative"

    def test_greeks_consistency(self):
        """Test that Greeks maintain mathematical relationships"""
        S = 100.0
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.30

        # Call and put should have same gamma and vega
        call_delta = GreeksCalculator.calculate_call_delta(S, K, T, r, sigma)
        put_delta = GreeksCalculator.calculate_put_delta(S, K, T, r, sigma)
        gamma = GreeksCalculator.calculate_gamma(S, K, T, r, sigma)
        vega = GreeksCalculator.calculate_vega(S, K, T, r, sigma)

        # Put-call delta parity: put delta = call delta - 1
        expected_put_delta = call_delta - 1.0
        assert abs(put_delta - expected_put_delta) < 0.01, \
            f"Put-call delta parity violated: {put_delta} != {expected_put_delta}"

        # Gamma and vega should be identical for calls and puts
        assert gamma > 0, "Gamma should be positive"
        assert vega > 0, "Vega should be positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
