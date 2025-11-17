"""Prophet model for cryptocurrency price forecasting."""
import pandas as pd
import numpy as np
from prophet import Prophet
from typing import Optional, Dict, List
from loguru import logger
import joblib


class ProphetPredictor:
    """Prophet-based price forecaster."""

    def __init__(
        self,
        changepoint_prior_scale: float = 0.05,
        seasonality_prior_scale: float = 10.0,
        seasonality_mode: str = 'multiplicative',
        daily_seasonality: bool = True,
        weekly_seasonality: bool = True,
        yearly_seasonality: bool = False
    ):
        """
        Initialize Prophet predictor.

        Args:
            changepoint_prior_scale: Flexibility of trend changes
            seasonality_prior_scale: Strength of seasonality
            seasonality_mode: 'additive' or 'multiplicative'
            daily_seasonality: Include daily seasonality
            weekly_seasonality: Include weekly seasonality
            yearly_seasonality: Include yearly seasonality
        """
        self.model = Prophet(
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_prior_scale=seasonality_prior_scale,
            seasonality_mode=seasonality_mode,
            daily_seasonality=daily_seasonality,
            weekly_seasonality=weekly_seasonality,
            yearly_seasonality=yearly_seasonality
        )
        self.fitted = False

    def add_regressors(self, regressors: List[str]):
        """
        Add additional regressors to the model.

        Args:
            regressors: List of regressor column names
        """
        for regressor in regressors:
            self.model.add_regressor(regressor)
        logger.info(f"Added regressors: {regressors}")

    def fit(
        self,
        data: pd.DataFrame,
        date_col: str = 'timestamp',
        target_col: str = 'close'
    ) -> 'ProphetPredictor':
        """
        Fit the Prophet model.

        Args:
            data: DataFrame with timestamp and target columns
            date_col: Name of date/timestamp column
            target_col: Name of target variable column

        Returns:
            Self
        """
        # Prepare data in Prophet format
        df = pd.DataFrame({
            'ds': pd.to_datetime(data[date_col]),
            'y': data[target_col]
        })

        # Add any additional regressors
        regressor_cols = [col for col in data.columns if col not in [date_col, target_col]]
        for col in regressor_cols:
            if col in [r['name'] for r in self.model.extra_regressors.values()]:
                df[col] = data[col]

        # Fit model
        logger.info("Fitting Prophet model...")
        self.model.fit(df)
        self.fitted = True
        logger.info("Prophet model fitted successfully")

        return self

    def predict(
        self,
        periods: int = 30,
        freq: str = '1H',
        include_history: bool = False
    ) -> pd.DataFrame:
        """
        Make future predictions.

        Args:
            periods: Number of periods to forecast
            freq: Frequency of predictions ('1H', '1D', etc.)
            include_history: Include historical fitted values

        Returns:
            DataFrame with predictions
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before prediction")

        # Create future dataframe
        future = self.model.make_future_dataframe(
            periods=periods,
            freq=freq,
            include_history=include_history
        )

        # Make predictions
        forecast = self.model.predict(future)

        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    def predict_on_data(
        self,
        data: pd.DataFrame,
        date_col: str = 'timestamp'
    ) -> pd.DataFrame:
        """
        Make predictions on specific dates.

        Args:
            data: DataFrame with dates to predict on
            date_col: Name of date/timestamp column

        Returns:
            DataFrame with predictions
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before prediction")

        # Prepare future dataframe
        future = pd.DataFrame({
            'ds': pd.to_datetime(data[date_col])
        })

        # Add any additional regressors
        for col in data.columns:
            if col != date_col and col in [r['name'] for r in self.model.extra_regressors.values()]:
                future[col] = data[col]

        # Make predictions
        forecast = self.model.predict(future)

        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    def get_components(self, forecast: pd.DataFrame) -> pd.DataFrame:
        """
        Get forecast components (trend, seasonality, etc.).

        Args:
            forecast: Forecast DataFrame from predict()

        Returns:
            DataFrame with components
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")

        return self.model.predict(forecast)[['ds', 'trend', 'weekly', 'daily']]

    def cross_validate(
        self,
        initial: str = '730 days',
        period: str = '180 days',
        horizon: str = '30 days'
    ) -> pd.DataFrame:
        """
        Perform cross-validation.

        Args:
            initial: Initial training period
            period: Spacing between cutoff dates
            horizon: Forecast horizon

        Returns:
            DataFrame with cross-validation results
        """
        from prophet.diagnostics import cross_validation

        if not self.fitted:
            raise ValueError("Model must be fitted before cross-validation")

        logger.info("Performing cross-validation...")
        cv_results = cross_validation(
            self.model,
            initial=initial,
            period=period,
            horizon=horizon
        )

        return cv_results

    def calculate_metrics(self, cv_results: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate performance metrics from cross-validation.

        Args:
            cv_results: Results from cross_validate()

        Returns:
            DataFrame with performance metrics
        """
        from prophet.diagnostics import performance_metrics

        metrics = performance_metrics(cv_results)
        return metrics

    def save(self, path: str):
        """Save model to file."""
        if not self.fitted:
            raise ValueError("Model must be fitted before saving")

        joblib.dump(self.model, path)
        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model from file."""
        self.model = joblib.load(path)
        self.fitted = True
        logger.info(f"Model loaded from {path}")


class ProphetEnsemble:
    """Ensemble of Prophet models for robust forecasting."""

    def __init__(self, n_models: int = 5):
        """
        Initialize Prophet ensemble.

        Args:
            n_models: Number of models in ensemble
        """
        self.n_models = n_models
        self.models: List[ProphetPredictor] = []

    def fit(
        self,
        data: pd.DataFrame,
        date_col: str = 'timestamp',
        target_col: str = 'close'
    ):
        """
        Fit ensemble of models with different hyperparameters.

        Args:
            data: Training data
            date_col: Date column name
            target_col: Target column name
        """
        # Different hyperparameter configurations
        configs = [
            {'changepoint_prior_scale': 0.001, 'seasonality_prior_scale': 1.0},
            {'changepoint_prior_scale': 0.01, 'seasonality_prior_scale': 5.0},
            {'changepoint_prior_scale': 0.05, 'seasonality_prior_scale': 10.0},
            {'changepoint_prior_scale': 0.1, 'seasonality_prior_scale': 15.0},
            {'changepoint_prior_scale': 0.5, 'seasonality_prior_scale': 20.0},
        ]

        self.models = []
        for i, config in enumerate(configs[:self.n_models]):
            logger.info(f"Training ensemble model {i + 1}/{self.n_models}")
            model = ProphetPredictor(**config)
            model.fit(data, date_col, target_col)
            self.models.append(model)

    def predict(
        self,
        periods: int = 30,
        freq: str = '1H',
        aggregation: str = 'mean'
    ) -> pd.DataFrame:
        """
        Make ensemble predictions.

        Args:
            periods: Number of periods to forecast
            freq: Frequency
            aggregation: How to aggregate predictions ('mean', 'median')

        Returns:
            DataFrame with ensemble predictions
        """
        all_predictions = []

        for model in self.models:
            pred = model.predict(periods=periods, freq=freq)
            all_predictions.append(pred['yhat'].values)

        # Aggregate predictions
        all_predictions = np.array(all_predictions)
        if aggregation == 'mean':
            final_pred = np.mean(all_predictions, axis=0)
        elif aggregation == 'median':
            final_pred = np.median(all_predictions, axis=0)
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation}")

        # Use timestamps from first model
        result = self.models[0].predict(periods=periods, freq=freq).copy()
        result['yhat'] = final_pred

        return result
