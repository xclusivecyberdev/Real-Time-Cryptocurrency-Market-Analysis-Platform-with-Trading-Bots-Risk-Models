"""Random Forest model for cryptocurrency price prediction."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from typing import Optional, Dict, Tuple, List
from loguru import logger
import joblib


class RandomForestPredictor:
    """Random Forest-based price predictor."""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: str = 'sqrt',
        task: str = 'regression',
        random_state: int = 42
    ):
        """
        Initialize Random Forest predictor.

        Args:
            n_estimators: Number of trees
            max_depth: Maximum tree depth
            min_samples_split: Minimum samples to split node
            min_samples_leaf: Minimum samples in leaf
            max_features: Number of features to consider for split
            task: 'regression' or 'classification'
            random_state: Random seed
        """
        self.task = task
        self.scaler = StandardScaler()

        if task == 'regression':
            self.model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=min_samples_split,
                min_samples_leaf=min_samples_leaf,
                max_features=max_features,
                random_state=random_state,
                n_jobs=-1
            )
        else:  # classification
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=min_samples_split,
                min_samples_leaf=min_samples_leaf,
                max_features=max_features,
                random_state=random_state,
                n_jobs=-1
            )

        self.feature_names: List[str] = []
        self.fitted = False

    def engineer_features(
        self,
        data: pd.DataFrame,
        include_ta: bool = True,
        include_lags: bool = True,
        lag_periods: List[int] = [1, 2, 3, 5, 10]
    ) -> pd.DataFrame:
        """
        Engineer features for Random Forest.

        Args:
            data: DataFrame with OHLCV data
            include_ta: Include technical analysis indicators
            include_lags: Include lagged features
            lag_periods: List of lag periods

        Returns:
            DataFrame with engineered features
        """
        df = data.copy()

        # Price-based features
        df['return'] = df['close'].pct_change()
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))

        # Volatility
        df['volatility'] = df['return'].rolling(window=20).std()

        # Price momentum
        df['momentum_5'] = df['close'].pct_change(5)
        df['momentum_10'] = df['close'].pct_change(10)
        df['momentum_20'] = df['close'].pct_change(20)

        # Volume features
        df['volume_change'] = df['volume'].pct_change()
        df['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()

        # High-Low spread
        df['hl_spread'] = (df['high'] - df['low']) / df['close']

        # Lagged features
        if include_lags:
            for lag in lag_periods:
                df[f'close_lag_{lag}'] = df['close'].shift(lag)
                df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
                df[f'return_lag_{lag}'] = df['return'].shift(lag)

        # Technical indicators (if requested)
        if include_ta:
            from backend.analytics.indicators import TechnicalIndicators

            # RSI
            df['rsi'] = TechnicalIndicators.calculate_rsi(df['close'].values)

            # MACD
            macd, signal, _ = TechnicalIndicators.calculate_macd(df['close'].values)
            df['macd'] = macd
            df['macd_signal'] = signal

            # Bollinger Bands
            upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(df['close'].values)
            df['bb_position'] = (df['close'] - lower) / (upper - lower)

            # EMAs
            df['ema_9'] = TechnicalIndicators.calculate_ema(df['close'].values, 9)
            df['ema_21'] = TechnicalIndicators.calculate_ema(df['close'].values, 21)
            df['ema_ratio'] = df['ema_9'] / df['ema_21']

        # Drop NaN values
        df = df.dropna()

        return df

    def prepare_data(
        self,
        data: pd.DataFrame,
        target_col: str = 'close',
        forecast_horizon: int = 1,
        feature_cols: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare data for training/prediction.

        Args:
            data: DataFrame with features
            target_col: Target column name
            forecast_horizon: How many periods ahead to predict
            feature_cols: List of feature columns (None = auto-detect)

        Returns:
            Tuple of (X, y, feature_names)
        """
        df = data.copy()

        # Create target (future price or direction)
        if self.task == 'regression':
            df['target'] = df[target_col].shift(-forecast_horizon)
        else:  # classification (predict direction)
            df['target'] = (df[target_col].shift(-forecast_horizon) > df[target_col]).astype(int)

        # Drop rows with NaN target
        df = df.dropna(subset=['target'])

        # Select features
        if feature_cols is None:
            # Auto-detect: use all numeric columns except target and original OHLCV
            exclude_cols = ['target', 'timestamp', 'date', 'open', 'high', 'low', 'close', 'volume']
            feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns
                           if col not in exclude_cols]

        self.feature_names = feature_cols

        X = df[feature_cols].values
        y = df['target'].values

        return X, y, feature_cols

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        scale_features: bool = True,
        cv_folds: int = 5
    ) -> Dict:
        """
        Train the Random Forest model.

        Args:
            X: Feature matrix
            y: Target values
            scale_features: Whether to scale features
            cv_folds: Number of cross-validation folds

        Returns:
            Dictionary with training metrics
        """
        # Scale features
        if scale_features:
            X = self.scaler.fit_transform(X)

        # Train model
        logger.info("Training Random Forest model...")
        self.model.fit(X, y)
        self.fitted = True

        # Cross-validation score
        cv_scores = cross_val_score(self.model, X, y, cv=cv_folds, n_jobs=-1)

        # Training score
        train_score = self.model.score(X, y)

        metrics = {
            'train_score': train_score,
            'cv_score_mean': cv_scores.mean(),
            'cv_score_std': cv_scores.std(),
            'cv_scores': cv_scores.tolist()
        }

        logger.info(f"Training completed. Train R² = {train_score:.4f}, CV R² = {cv_scores.mean():.4f}")

        return metrics

    def predict(self, X: np.ndarray, scale_features: bool = True) -> np.ndarray:
        """
        Make predictions.

        Args:
            X: Feature matrix
            scale_features: Whether to scale features

        Returns:
            Predictions
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before prediction")

        if scale_features:
            X = self.scaler.transform(X)

        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray, scale_features: bool = True) -> np.ndarray:
        """
        Get prediction probabilities (classification only).

        Args:
            X: Feature matrix
            scale_features: Whether to scale features

        Returns:
            Probability estimates
        """
        if self.task != 'classification':
            raise ValueError("predict_proba only available for classification")

        if not self.fitted:
            raise ValueError("Model must be fitted before prediction")

        if scale_features:
            X = self.scaler.transform(X)

        return self.model.predict_proba(X)

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance scores.

        Returns:
            DataFrame with feature importance
        """
        if not self.fitted:
            raise ValueError("Model must be fitted first")

        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        return importance_df

    def hyperparameter_tuning(
        self,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: Optional[Dict] = None,
        cv_folds: int = 5
    ) -> Dict:
        """
        Perform hyperparameter tuning using GridSearchCV.

        Args:
            X: Feature matrix
            y: Target values
            param_grid: Parameter grid for search
            cv_folds: Number of CV folds

        Returns:
            Best parameters and scores
        """
        if param_grid is None:
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [10, 20, 30, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'max_features': ['sqrt', 'log2']
            }

        logger.info("Starting hyperparameter tuning...")

        grid_search = GridSearchCV(
            self.model,
            param_grid,
            cv=cv_folds,
            n_jobs=-1,
            verbose=1
        )

        grid_search.fit(X, y)

        # Update model with best parameters
        self.model = grid_search.best_estimator_
        self.fitted = True

        results = {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'cv_results': grid_search.cv_results_
        }

        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best CV score: {grid_search.best_score_:.4f}")

        return results

    def save(self, model_path: str, scaler_path: str):
        """Save model and scaler."""
        if not self.fitted:
            raise ValueError("Model must be fitted before saving")

        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        joblib.dump(self.feature_names, model_path.replace('.pkl', '_features.pkl'))

        logger.info(f"Model saved to {model_path}")

    def load(self, model_path: str, scaler_path: str):
        """Load model and scaler."""
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.feature_names = joblib.load(model_path.replace('.pkl', '_features.pkl'))
        self.fitted = True

        logger.info(f"Model loaded from {model_path}")


class RandomForestTradingSignal:
    """Generate trading signals using Random Forest."""

    def __init__(self):
        """Initialize trading signal generator."""
        self.price_predictor = RandomForestPredictor(task='regression')
        self.direction_predictor = RandomForestPredictor(task='classification')

    def train(
        self,
        data: pd.DataFrame,
        forecast_horizon: int = 1
    ):
        """
        Train both price and direction predictors.

        Args:
            data: Training data with OHLCV
            forecast_horizon: Prediction horizon
        """
        # Engineer features
        featured_data = self.price_predictor.engineer_features(data)

        # Train price predictor
        X_price, y_price, features = self.price_predictor.prepare_data(
            featured_data,
            forecast_horizon=forecast_horizon
        )
        self.price_predictor.fit(X_price, y_price)

        # Train direction predictor
        X_dir, y_dir, _ = self.direction_predictor.prepare_data(
            featured_data,
            forecast_horizon=forecast_horizon
        )
        self.direction_predictor.fit(X_dir, y_dir)

        logger.info("Trading signal models trained successfully")

    def generate_signals(
        self,
        data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate trading signals.

        Args:
            data: Current market data

        Returns:
            DataFrame with signals and predictions
        """
        # Engineer features
        featured_data = self.price_predictor.engineer_features(data)

        # Prepare features
        X, _, _ = self.price_predictor.prepare_data(featured_data)

        # Get predictions
        price_pred = self.price_predictor.predict(X)
        direction_proba = self.direction_predictor.predict_proba(X)

        # Generate signals
        signals = pd.DataFrame({
            'predicted_price': price_pred,
            'prob_up': direction_proba[:, 1],
            'prob_down': direction_proba[:, 0],
            'signal': np.where(direction_proba[:, 1] > 0.6, 1,  # Buy
                              np.where(direction_proba[:, 1] < 0.4, -1, 0))  # Sell / Hold
        })

        return signals
