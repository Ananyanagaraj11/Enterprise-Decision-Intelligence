"""
Deep learning training for multi-class network intrusion detection.
"""

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score
from torch.utils.data import DataLoader, TensorDataset

# Add parent for imports if needed
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset_loader import get_class_weights, prepare_for_training


class IntrusionDetectionMLP(nn.Module):
    """MLP for tabular network traffic features; can be extended for LSTM input."""

    def __init__(
        self,
        input_dim: int,
        num_classes: int,
        hidden_dims: tuple = (128, 64, 32),
        dropout: float = 0.3,
    ):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden_dims:
            layers.extend(
                [
                    nn.Linear(prev, h),
                    nn.BatchNorm1d(h),
                    nn.ReLU(inplace=True),
                    nn.Dropout(dropout),
                ]
            )
            prev = h
        self.backbone = nn.Sequential(*layers)
        self.head = nn.Linear(prev, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.backbone(x))


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0
    for X_batch, y_batch in loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        optimizer.zero_grad()
        logits = model(X_batch)
        loss = criterion(logits, y_batch)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float, float]:
    model.eval()
    total_loss = 0.0
    all_preds, all_labels = [], []
    for X_batch, y_batch in loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        logits = model(X_batch)
        loss = criterion(logits, y_batch)
        total_loss += loss.item()
        preds = logits.argmax(dim=1).cpu().numpy()
        all_preds.append(preds)
        all_labels.append(y_batch.cpu().numpy())
    y_true = np.concatenate(all_labels)
    y_pred = np.concatenate(all_preds)
    avg_loss = total_loss / len(loader)
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    return avg_loss, acc, f1


def main():
    parser = argparse.ArgumentParser(description="Train intrusion detection model")
    parser.add_argument("--data", type=str, required=True, help="Path to CSV file or CICIDS2017 directory")
    parser.add_argument("--label-column", type=str, default=None, help="Label column name")
    parser.add_argument("--out-dir", type=str, default="./outputs", help="Output directory")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--max-rows", type=int, default=None, help="Cap rows per file (or total for single CSV)")
    parser.add_argument("--max-rows-total", type=int, default=None, help="Cap total rows when using CICIDS2017 dir")
    parser.add_argument("--use-cicids2017-dir", action="store_true", help="Load from CICIDS2017 directory of CSVs")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    X_train, X_val, y_train, y_val, scaler, label_encoder, feature_names = prepare_for_training(
        args.data,
        label_column=args.label_column,
        test_size=0.2,
        random_state=args.seed,
        max_rows=args.max_rows,
        use_cicids2017_dir=args.use_cicids2017_dir,
        max_rows_total=args.max_rows_total,
    )

    n_features = X_train.shape[1]
    n_classes = len(label_encoder.classes_)
    class_weights = get_class_weights(y_train)
    class_weights_t = torch.from_numpy(class_weights).to(device)

    train_ds = TensorDataset(
        torch.from_numpy(X_train).float(),
        torch.from_numpy(y_train).long(),
    )
    val_ds = TensorDataset(
        torch.from_numpy(X_val).float(),
        torch.from_numpy(y_val).long(),
    )
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    model = IntrusionDetectionMLP(
        input_dim=n_features,
        num_classes=n_classes,
        hidden_dims=(128, 64, 32),
        dropout=0.3,
    ).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights_t)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    history = {"train_loss": [], "val_loss": [], "val_accuracy": [], "val_f1_macro": []}

    for epoch in range(args.epochs):
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, val_f1 = evaluate(model, val_loader, criterion, device)
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_accuracy"].append(val_acc)
        history["val_f1_macro"].append(val_f1)
        print(
            f"Epoch {epoch + 1}/{args.epochs} | train_loss={train_loss:.4f} | "
            f"val_loss={val_loss:.4f} | val_acc={val_acc:.4f} | val_f1_macro={val_f1:.4f}"
        )

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "input_dim": n_features,
            "num_classes": n_classes,
            "hidden_dims": (128, 64, 32),
            "dropout": 0.3,
        },
        out_dir / "model.pt",
    )
    torch.save(label_encoder.classes_, out_dir / "classes.pt")
    joblib.dump(scaler, out_dir / "scaler.joblib")
    with open(out_dir / "feature_names.txt", "w") as f:
        f.write("\n".join(feature_names))
    with open(out_dir / "history.json", "w") as f:
        json.dump(history, f, indent=2)

    print(f"Model and artifacts saved to {out_dir}")


if __name__ == "__main__":
    main()
