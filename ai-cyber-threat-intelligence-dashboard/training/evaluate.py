"""
Evaluate trained cyber attack detection model: metrics, confusion matrix, curves.
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# Import model architecture from train
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from train import IntrusionDetectionMLP
from dataset_loader import prepare_for_training


def load_model_and_artifacts(model_dir: Path, device: torch.device):
    """Load saved model, scaler, and class names."""
    import joblib

    ckpt = torch.load(model_dir / "model.pt", map_location=device, weights_only=False)
    model = IntrusionDetectionMLP(
        input_dim=ckpt["input_dim"],
        num_classes=ckpt["num_classes"],
        hidden_dims=ckpt["hidden_dims"],
        dropout=ckpt.get("dropout", 0.3),
    )
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    model.eval()

    scaler = joblib.load(model_dir / "scaler.joblib")
    classes = torch.load(model_dir / "classes.pt", map_location="cpu", weights_only=False)
    if isinstance(classes, torch.Tensor):
        classes = classes.numpy()
    return model, scaler, list(classes)


def plot_training_curves(history_path: Path, save_path: Path) -> None:
    """Plot train/val loss and accuracy/F1 and save."""
    with open(history_path) as f:
        history = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(history["train_loss"], label="Train loss")
    axes[0].plot(history["val_loss"], label="Val loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].set_title("Training and validation loss")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(history["val_accuracy"], label="Val accuracy")
    axes[1].plot(history["val_f1_macro"], label="Val F1 (macro)")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Score")
    axes[1].set_title("Validation accuracy and F1")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: list,
    save_path: Path,
) -> None:
    """Plot and save confusion matrix."""
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(max(8, len(class_names) * 0.5), max(6, len(class_names) * 0.4)))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)

    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=class_names,
        yticklabels=class_names,
        title="Confusion matrix",
        ylabel="True label",
        xlabel="Predicted label",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j, i, format(cm[i, j], "d"),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black",
            )
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Evaluate intrusion detection model")
    parser.add_argument("--model-dir", type=str, required=True, help="Directory with model.pt, scaler.joblib, classes.pt")
    parser.add_argument("--data", type=str, required=True, help="Path to CSV or CICIDS2017 directory")
    parser.add_argument("--out-dir", type=str, default=None, help="Output directory (default: model-dir)")
    parser.add_argument("--label-column", type=str, default=None)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--max-rows-total", type=int, default=None)
    parser.add_argument("--use-cicids2017-dir", action="store_true")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    out_dir = Path(args.out_dir or args.model_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, scaler, class_names = load_model_and_artifacts(model_dir, device)

    X_train, X_val, y_train, y_val, _, _, _ = prepare_for_training(
        args.data,
        label_column=args.label_column,
        test_size=0.2,
        random_state=42,
        max_rows=args.max_rows,
        use_cicids2017_dir=args.use_cicids2017_dir,
        max_rows_total=args.max_rows_total,
    )

    X_val_t = torch.from_numpy(X_val).float().to(device)
    with torch.no_grad():
        logits = model(X_val_t)
        y_pred = logits.argmax(dim=1).cpu().numpy()

    accuracy = accuracy_score(y_val, y_pred)
    precision_per_class = precision_score(y_val, y_pred, average=None, zero_division=0)
    recall_per_class = recall_score(y_val, y_pred, average=None, zero_division=0)
    f1_per_class = f1_score(y_val, y_pred, average=None, zero_division=0)
    f1_macro = f1_score(y_val, y_pred, average="macro", zero_division=0)

    report = classification_report(
        y_val, y_pred, target_names=class_names, output_dict=True, zero_division=0
    )

    metrics = {
        "accuracy": float(accuracy),
        "f1_macro": float(f1_macro),
        "per_class": {
            class_names[i]: {
                "precision": float(precision_per_class[i]),
                "recall": float(recall_per_class[i]),
                "f1": float(f1_per_class[i]),
            }
            for i in range(len(class_names))
        },
        "classification_report": report,
    }

    with open(out_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    plot_confusion_matrix(y_val, y_pred, class_names, out_dir / "confusion_matrix.png")
    if (model_dir / "history.json").exists():
        plot_training_curves(model_dir / "history.json", out_dir / "training_curves.png")

    print("Accuracy:", accuracy)
    print("Macro F1:", f1_macro)
    print("Metrics and plots saved to", out_dir)


if __name__ == "__main__":
    main()
