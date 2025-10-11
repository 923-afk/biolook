#!/usr/bin/env python3
"""
train.py
簡易的 PyTorch 遷移學習訓練腳本（使用 timm model）
使用方式：
  python train.py --data-dir data --epochs 10 --batch-size 32 --model efficientnet_b3 --img-size 224
輸出 checkpoint 存到 checkpoints/
"""
import argparse, os, time
from pathlib import Path
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import timm
import numpy as np
from tqdm import tqdm
from sklearn.metrics import accuracy_score

def get_dataloaders(data_dir, img_size=224, batch_size=32, num_workers=4):
    train_trans = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(20),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    ])
    val_trans = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    ])
    train_ds = datasets.ImageFolder(os.path.join(data_dir, "train"), transform=train_trans)
    val_ds = datasets.ImageFolder(os.path.join(data_dir, "val"), transform=val_trans)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    return train_loader, val_loader, train_ds.classes

def train_one_epoch(model, loader, device, criterion, optimizer):
    model.train()
    losses = []
    preds = []
    gts = []
    for imgs, labels in tqdm(loader, desc="train"):
        imgs = imgs.to(device)
        labels = labels.to(device)
        out = model(imgs)
        loss = criterion(out, labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
        preds.extend(torch.argmax(out, dim=1).cpu().numpy().tolist())
        gts.extend(labels.cpu().numpy().tolist())
    acc = accuracy_score(gts, preds)
    return np.mean(losses), acc

def eval_model(model, loader, device, criterion):
    model.eval()
    losses = []
    preds = []
    gts = []
    with torch.no_grad():
        for imgs, labels in tqdm(loader, desc="eval"):
            imgs = imgs.to(device)
            labels = labels.to(device)
            out = model(imgs)
            loss = criterion(out, labels)
            losses.append(loss.item())
            preds.extend(torch.argmax(out, dim=1).cpu().numpy().tolist())
            gts.extend(labels.cpu().numpy().tolist())
    acc = accuracy_score(gts, preds)
    return np.mean(losses), acc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--model", default="efficientnet_b3")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--img-size", type=int, default=224)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=4)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Device:", device)

    train_loader, val_loader, classes = get_dataloaders(args.data_dir, img_size=args.img_size, batch_size=args.batch_size, num_workers=args.num_workers)
    num_classes = len(classes)
    print("Classes:", num_classes)

    model = timm.create_model(args.model, pretrained=True, num_classes=num_classes)
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    best_val_acc = 0.0
    os.makedirs("checkpoints", exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, device, criterion, optimizer)
        val_loss, val_acc = eval_model(model, val_loader, device, criterion)
        t1 = time.time()
        print(f"Epoch {epoch} | train_loss={train_loss:.4f} train_acc={train_acc:.4f} | val_loss={val_loss:.4f} val_acc={val_acc:.4f} | time={t1-t0:.1f}s")
        ckpt = f"checkpoints/epoch{epoch:02d}.pth"
        torch.save({"model_state": model.state_dict(), "classes": classes, "epoch": epoch}, ckpt)
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({"model_state": model.state_dict(), "classes": classes, "epoch": epoch}, "checkpoints/best.pth")
    print("Training done. Best val acc:", best_val_acc)

if __name__ == "__main__":
    main()


