"""LSTM model for cryptocurrency price prediction."""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Tuple, Optional, List
from loguru import logger
from sklearn.preprocessing import MinMaxScaler
import joblib


class LSTMPriceDataset(Dataset):
    """Dataset for LSTM price prediction."""

    def __init__(self, sequences: np.ndarray, targets: np.ndarray):
        """
        Initialize dataset.

        Args:
            sequences: Input sequences (samples, sequence_length, features)
            targets: Target values (samples,)
        """
        self.sequences = torch.FloatTensor(sequences)
        self.targets = torch.FloatTensor(targets)

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.sequences[idx], self.targets[idx]


class LSTMModel(nn.Module):
    """LSTM neural network for price prediction."""

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
        bidirectional: bool = False
    ):
        """
        Initialize LSTM model.

        Args:
            input_size: Number of input features
            hidden_size: Size of hidden layer
            num_layers: Number of LSTM layers
            dropout: Dropout rate
            bidirectional: Whether to use bidirectional LSTM
        """
        super(LSTMModel, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional

        # LSTM layer
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )

        # Fully connected layers
        fc_input_size = hidden_size * 2 if bidirectional else hidden_size
        self.fc1 = nn.Linear(fc_input_size, 32)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor (batch_size, sequence_length, input_size)

        Returns:
            Output predictions (batch_size, 1)
        """
        # LSTM forward pass
        lstm_out, _ = self.lstm(x)

        # Take the output from the last time step
        last_output = lstm_out[:, -1, :]

        # Fully connected layers
        out = self.fc1(last_output)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)

        return out


class LSTMPredictor:
    """LSTM-based price predictor."""

    def __init__(
        self,
        sequence_length: int = 60,
        features: Optional[List[str]] = None,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
        bidirectional: bool = False
    ):
        """
        Initialize LSTM predictor.

        Args:
            sequence_length: Length of input sequences (lookback window)
            features: List of feature column names (default: ['close'])
            hidden_size: LSTM hidden size
            num_layers: Number of LSTM layers
            dropout: Dropout rate
            bidirectional: Use bidirectional LSTM
        """
        self.sequence_length = sequence_length
        self.features = features or ['close']
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.bidirectional = bidirectional

        self.model: Optional[LSTMModel] = None
        self.scaler = MinMaxScaler()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        logger.info(f"LSTM Predictor initialized. Device: {self.device}")

    def prepare_sequences(
        self,
        data: pd.DataFrame,
        target_col: str = 'close'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for LSTM training.

        Args:
            data: DataFrame with features and target
            target_col: Target column name

        Returns:
            Tuple of (sequences, targets)
        """
        # Extract feature columns
        feature_data = data[self.features].values

        # Normalize features
        scaled_data = self.scaler.fit_transform(feature_data)

        sequences = []
        targets = []

        # Create sequences
        for i in range(len(scaled_data) - self.sequence_length):
            seq = scaled_data[i:i + self.sequence_length]
            target_idx = data.columns.get_loc(target_col)
            target = scaled_data[i + self.sequence_length, target_idx]

            sequences.append(seq)
            targets.append(target)

        return np.array(sequences), np.array(targets)

    def train(
        self,
        train_data: pd.DataFrame,
        val_data: Optional[pd.DataFrame] = None,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        early_stopping_patience: int = 10
    ) -> dict:
        """
        Train the LSTM model.

        Args:
            train_data: Training data DataFrame
            val_data: Validation data DataFrame (optional)
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            early_stopping_patience: Early stopping patience

        Returns:
            Training history dictionary
        """
        # Prepare data
        X_train, y_train = self.prepare_sequences(train_data)

        # Initialize model
        input_size = len(self.features)
        self.model = LSTMModel(
            input_size=input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout,
            bidirectional=self.bidirectional
        ).to(self.device)

        # Create data loaders
        train_dataset = LSTMPriceDataset(X_train, y_train)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        if val_data is not None:
            X_val, y_val = self.prepare_sequences(val_data)
            val_dataset = LSTMPriceDataset(X_val, y_val)
            val_loader = DataLoader(val_dataset, batch_size=batch_size)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)

        # Training loop
        history = {'train_loss': [], 'val_loss': []}
        best_val_loss = float('inf')
        patience_counter = 0

        logger.info(f"Starting training for {epochs} epochs...")

        for epoch in range(epochs):
            # Training
            self.model.train()
            train_losses = []

            for sequences, targets in train_loader:
                sequences = sequences.to(self.device)
                targets = targets.to(self.device)

                # Forward pass
                outputs = self.model(sequences).squeeze()
                loss = criterion(outputs, targets)

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                train_losses.append(loss.item())

            avg_train_loss = np.mean(train_losses)
            history['train_loss'].append(avg_train_loss)

            # Validation
            if val_data is not None:
                self.model.eval()
                val_losses = []

                with torch.no_grad():
                    for sequences, targets in val_loader:
                        sequences = sequences.to(self.device)
                        targets = targets.to(self.device)

                        outputs = self.model(sequences).squeeze()
                        loss = criterion(outputs, targets)
                        val_losses.append(loss.item())

                avg_val_loss = np.mean(val_losses)
                history['val_loss'].append(avg_val_loss)

                # Early stopping
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1

                if patience_counter >= early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch + 1}")
                    break

                if (epoch + 1) % 10 == 0:
                    logger.info(
                        f"Epoch {epoch + 1}/{epochs} - "
                        f"Train Loss: {avg_train_loss:.6f}, Val Loss: {avg_val_loss:.6f}"
                    )
            else:
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch + 1}/{epochs} - Train Loss: {avg_train_loss:.6f}")

        logger.info("Training completed!")
        return history

    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data.

        Args:
            data: DataFrame with features

        Returns:
            Array of predictions (in original scale)
        """
        if self.model is None:
            raise ValueError("Model must be trained before prediction")

        self.model.eval()

        # Prepare sequences
        feature_data = data[self.features].values
        scaled_data = self.scaler.transform(feature_data)

        sequences = []
        for i in range(len(scaled_data) - self.sequence_length):
            sequences.append(scaled_data[i:i + self.sequence_length])

        if len(sequences) == 0:
            raise ValueError("Insufficient data for prediction")

        sequences = np.array(sequences)
        sequences_tensor = torch.FloatTensor(sequences).to(self.device)

        # Make predictions
        with torch.no_grad():
            predictions = self.model(sequences_tensor).cpu().numpy().squeeze()

        # Inverse transform predictions
        # Create a dummy array with the same shape as the original features
        dummy = np.zeros((len(predictions), len(self.features)))
        dummy[:, 0] = predictions  # Put predictions in first column
        predictions_original = self.scaler.inverse_transform(dummy)[:, 0]

        return predictions_original

    def save(self, model_path: str, scaler_path: str):
        """Save model and scaler."""
        if self.model is None:
            raise ValueError("No model to save")

        torch.save(self.model.state_dict(), model_path)
        joblib.dump(self.scaler, scaler_path)
        logger.info(f"Model saved to {model_path}")

    def load(self, model_path: str, scaler_path: str):
        """Load model and scaler."""
        input_size = len(self.features)
        self.model = LSTMModel(
            input_size=input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout,
            bidirectional=self.bidirectional
        ).to(self.device)

        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.scaler = joblib.load(scaler_path)
        logger.info(f"Model loaded from {model_path}")
